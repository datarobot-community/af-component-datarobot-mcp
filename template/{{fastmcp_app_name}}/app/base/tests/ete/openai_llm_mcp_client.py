import json
from typing import Any, Dict, List, Optional, Tuple

import openai
from mcp.client.session import ClientSession
from mcp.types import CallToolResult, ListToolsResult, TextContent
from openai import AzureOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from pydantic import BaseModel

from .common import save_response_to_file
from .mcp_utils import get_dr_mcp_server_url


class ToolCall(BaseModel):
    """Represents a tool call decision made by the LLM."""

    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str


class LLMResponse(BaseModel):
    """Response from LLM including tool usage details."""

    content: str
    tool_calls_made: List[ToolCall]
    tool_results: List[str]
    clean_content: str


class LLMMCPClient:
    """
    An LLM client that can make decisions about when to call MCP tools
    and provide final responses based on tool results.
    Supports both standard OpenAI and Azure OpenAI configurations.
    """

    def __init__(
        self,
        openai_api_key: str,
        model: Optional[
            str
        ] = "gpt-4",  # Use deployment ID for Azure, gpt-4 for standard OpenAI
        openai_api_base: Optional[str] = None,
        openai_api_deployment_id: Optional[str] = None,
        openai_api_version: Optional[str] = None,
        save_llm_responses: bool = False,
    ):
        # Initialize OpenAI client with Azure or standard OpenAI
        if openai_api_base:
            self.openai_client = AzureOpenAI(
                azure_endpoint=openai_api_base,
                api_key=openai_api_key,
                api_version=openai_api_version,
            )
            self.model = openai_api_deployment_id
        else:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            self.model = model

        self.save_llm_responses = save_llm_responses

        self.available_tools: List[Dict[str, Any]] = []

    def _add_mcp_as_a_tool_to_available_tools(self) -> None:
        """Add MCP as a tool to the available tools."""
        # see https://platform.openai.com/docs/guides/tools-remote-mcp
        # It's coming but it doesn't work yet (2025-06-16)
        # openai.BadRequestError: Error code: 400 - {'error': {'message': "Missing required parameter: 'tools[0].function'.", 'type': 'invalid_request_error', 'param': 'tools[0].function', 'code': 'missing_required_parameter'}}
        self.available_tools = [
            {
                "type": "mcp",
                "server_label": "datarobot-mcp-server",
                "server_url": get_dr_mcp_server_url(),
                "require_approval": "never",
            }
        ]

    async def _add_mcp_tool_to_available_tools(
        self, mcp_session: ClientSession
    ) -> None:
        """Add a tool to the available tools."""
        tools_result: ListToolsResult = await mcp_session.list_tools()
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
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

    async def _process_tool_calls(
        self,
        response: ChatCompletion,
        messages: List[Dict[str, Any]],
        mcp_session: ClientSession,
    ) -> Tuple[List[ToolCall], List[str]]:
        """Process tool calls from the response, and return the tool calls and tool results."""
        tool_calls = []
        tool_results = []

        # If the response has tool calls, process them
        if response.choices[0].message.tool_calls:
            messages.append(
                response.choices[0].message
            )  # Add assistant's message with tool calls

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

                    # Add tool result to messages
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
                    messages.append(
                        {
                            "role": "tool",
                            "content": error_msg,
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                        }
                    )

        return tool_calls, tool_results

    async def _get_llm_response(
        self, messages: List[Dict[str, Any]], allow_tool_calls: bool = True
    ) -> ChatCompletion:
        """Get a response from the LLM with optional tool calling capability."""
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        if allow_tool_calls and self.available_tools:
            kwargs.update(
                {
                    "tools": self.available_tools,
                    "tool_choice": "auto",
                }
            )

        return self.openai_client.chat.completions.create(**kwargs)

    async def process_prompt_with_mcp_support(
        self,
        prompt: str,
        mcp_session: ClientSession,
        output_file_name: Optional[str] = None,
    ) -> LLMResponse:
        """Process a user prompt through the MCP-specific flow.

        Args:
            prompt: The user's prompt to process
            mcp_session: The MCP client session to use
            output_file_name: Optional name of the file to save the response to
        """
        # Ensure available tools are set up
        if not self.available_tools:
            await self._add_mcp_tool_to_available_tools(mcp_session)

        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that can use tools to help users. If you need more information to provide a complete response, you can make multiple tool calls. When dealing with file paths, use them as raw paths without converting to file:// URLs.",
            },
            {"role": "user", "content": prompt},
        ]

        all_tool_calls = []
        all_tool_results = []

        while True:
            # Get LLM response
            response = await self._get_llm_response(messages)

            # If no tool calls in response, this is the final response
            if not response.choices[0].message.tool_calls:
                final_response = response.choices[0].message.content
                break

            # Process tool calls
            tool_calls, tool_results = await self._process_tool_calls(
                response, messages, mcp_session
            )
            all_tool_calls.extend(tool_calls)
            all_tool_results.extend(tool_results)

            # Get another LLM response to see if we need more tool calls
            response = await self._get_llm_response(messages, allow_tool_calls=True)

            # If no more tool calls needed, this is the final response
            if not response.choices[0].message.tool_calls:
                final_response = response.choices[0].message.content
                break

        clean_content = final_response.replace("*", "").lower()

        llm_response = LLMResponse(
            content=final_response,
            tool_calls_made=all_tool_calls,
            tool_results=all_tool_results,
            clean_content=clean_content,
        )

        if self.save_llm_responses:
            save_response_to_file(llm_response, name=output_file_name)

        return llm_response
