# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import Any, Dict, List

import openai
from mcp.client.session import ClientSession
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ListToolsResult,
    ReadResourceResult,
    TextContent,
    TextResourceContents,
)

# get_dr_mcp_server_url import removed as it's not used


class ToolCall:
    """Represents a tool call with its parameters and reasoning."""

    def __init__(self, tool_name: str, parameters: Dict[str, Any], reasoning: str):
        self.tool_name = tool_name
        self.parameters = parameters
        self.reasoning = reasoning


class LLMResponse:
    """Represents an LLM response with content and tool calls."""

    def __init__(
        self, content: str, tool_calls: List[ToolCall], tool_results: List[str]
    ):
        self.content = content
        self.tool_calls = tool_calls
        self.tool_results = tool_results


class LLMMCPClient:
    """Client for interacting with LLMs via MCP."""

    def __init__(self, config: str):
        """Initialize the LLM MCP client."""
        # Parse config string to extract parameters
        config_dict = eval(config) if isinstance(config, str) else config

        openai_api_key = config_dict.get("openai_api_key")
        openai_api_base = config_dict.get("openai_api_base")
        openai_api_deployment_id = config_dict.get("openai_api_deployment_id")
        model = config_dict.get("model", "gpt-3.5-turbo")
        save_llm_responses = config_dict.get("save_llm_responses", True)

        if openai_api_base and openai_api_deployment_id:
            # Azure OpenAI
            self.openai_client = openai.AzureOpenAI(
                api_key=openai_api_key,
                azure_endpoint=openai_api_base,
                api_version=config_dict.get("openai_api_version", "2024-02-15-preview"),
            )
            self.model = openai_api_deployment_id
        else:
            # Regular OpenAI
            self.openai_client = openai.OpenAI(api_key=openai_api_key)  # type: ignore[assignment]
            self.model = model

        self.save_llm_responses = save_llm_responses
        self.available_tools: List[Dict[str, Any]] = []
        self.available_prompts: List[Dict[str, Any]] = []
        self.available_resources: List[Dict[str, Any]] = []

    async def _add_mcp_tool_to_available_tools(
        self, mcp_session: ClientSession
    ) -> None:
        """Add a tool to the available tools."""
        tools_result: ListToolsResult = await mcp_session.list_tools()
        self.available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]

    async def _call_mcp_tool(
        self, tool_name: str, parameters: Dict[str, Any], mcp_session: ClientSession
    ) -> str:
        """Call an MCP tool and return the result as a string."""
        result: CallToolResult = await mcp_session.call_tool(tool_name, parameters)
        return (
            result.content[0].text
            if result.content and isinstance(result.content[0], TextContent)
            else str(result.content)
        )

    async def _read_mcp_resource(
        self, resource_uri: str, mcp_session: ClientSession
    ) -> str:
        """Read an MCP resource and return the result as a string."""
        result: ReadResourceResult = await mcp_session.read_resource(resource_uri)  # type: ignore[arg-type]
        return (
            result.contents[0].text
            if result.contents and isinstance(result.contents[0], TextResourceContents)
            else str(result.contents)
        )

    async def _get_mcp_prompt(
        self, prompt_name: str, arguments: Dict[str, Any], mcp_session: ClientSession
    ) -> str:
        """Get an MCP prompt and return the result as a string."""
        result: GetPromptResult = await mcp_session.get_prompt(
            prompt_name, arguments=arguments
        )
        return result.messages[0].content.text  # type: ignore[union-attr]

    async def _get_llm_response(
        self, messages: List[Dict[str, Any]], allow_tool_calls: bool = True
    ) -> Any:
        """Get a response from the LLM with optional tool calling capability."""
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if allow_tool_calls and self.available_tools:
            kwargs["tools"] = self.available_tools
            kwargs["tool_choice"] = "auto"

        return self.openai_client.chat.completions.create(**kwargs)

    async def process_prompt_with_mcp_support(
        self, prompt: str, mcp_session: ClientSession
    ) -> LLMResponse:
        """Process a prompt with MCP tool support."""
        # Add MCP tools to available tools
        await self._add_mcp_tool_to_available_tools(mcp_session)

        messages = [{"role": "user", "content": prompt}]
        tool_calls = []
        tool_results = []

        # Get initial response
        response = await self._get_llm_response(messages, allow_tool_calls=True)

        # Process tool calls if any
        if response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)

            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                parameters = json.loads(tool_call.function.arguments)

                tool_calls.append(
                    ToolCall(
                        tool_name=tool_name,
                        parameters=parameters,
                        reasoning="Tool selected by LLM",
                    )
                )

                try:
                    result_text = await self._call_mcp_tool(
                        tool_name, parameters, mcp_session
                    )
                    tool_results.append(result_text)

                    messages.append(
                        {
                            "role": "tool",
                            "content": result_text,
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                        }
                    )
                except Exception as e:
                    error_msg = f"Error calling {tool_name}: {str(e)}"
                    tool_results.append(error_msg)

        # Get final response
        final_response = response.choices[0].message.content
        clean_content = (
            final_response.replace("*", "").lower() if final_response else ""
        )

        return LLMResponse(
            content=clean_content,
            tool_calls=tool_calls,
            tool_results=tool_results,
        )
