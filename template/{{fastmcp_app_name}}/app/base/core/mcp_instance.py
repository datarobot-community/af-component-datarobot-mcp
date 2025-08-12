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

from functools import wraps
from typing import Any, Callable, List, Optional

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import Tool as MCPTool
from mcp.types import ToolAnnotations

from .config import get_config
from .logging import log_execution
from .memory_management import MemoryManager, get_memory_manager
from .telemetry import trace_execution
from .tool_filter import filter_tools_by_tags, list_all_tags


class TaggedFastMCP(FastMCP):
    """
    Extended FastMCP that supports tags and other annotations directly in the tool decorator.
    """

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Extended tool decorator that supports tags and other annotations.

        Args:
            name: Tool name
            description: Tool description
            tags: List of tags for the tool
            **kwargs: Additional annotations to pass to ToolAnnotations
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Create annotations with tags and any additional kwargs
            annotations_dict = kwargs.copy()
            if tags:
                annotations_dict["tags"] = tags

            # Create ToolAnnotations if we have any annotations
            annotations = (
                ToolAnnotations(**annotations_dict) if annotations_dict else None
            )

            # Call the parent tool decorator with annotations
            return FastMCP.tool(
                self, name=name, description=description, annotations=annotations
            )(func)

        return decorator

    async def list_tools(
        self, tags: Optional[List[str]] = None, match_all: bool = False
    ) -> list[MCPTool]:
        """
        List all available tools, optionally filtered by tags.

        Args:
            tags: Optional list of tags to filter by. If None, returns all tools.
            match_all: If True, tool must have all specified tags (AND logic).
                      If False, tool must have at least one tag (OR logic).
                      Only used when tags is provided.

        Returns:
            List of MCPTool objects that match the tag criteria.
        """
        # Get all tools from the parent class
        all_tools = await super().list_tools()

        # If no tags specified, return all tools
        if not tags:
            return all_tools

        # Filter tools by tags
        filtered_tools = filter_tools_by_tags(all_tools, tags, match_all)

        return filtered_tools

    async def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all registered tools.

        Returns:
            List of all unique tags sorted alphabetically.
        """
        all_tools = await self.list_tools()
        return list_all_tags(all_tools)


# Create the tagged MCP instance
mcp_server_configs = get_config()

mcp = TaggedFastMCP(
    name=mcp_server_configs.mcp_server_name,
    port=mcp_server_configs.mcp_server_port,
    log_level=mcp_server_configs.mcp_server_log_level,
    host=mcp_server_configs.mcp_server_host,
    stateless_http=True,
)


def dr_core_mcp_tool(tags: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes mcp.tool() and dr_mcp_extras()"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return mcp.tool(tags=tags)(dr_mcp_extras()(func))

    return decorator


def dr_mcp_tool(tags: Optional[List[str]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes mcp.tool(), dr_mcp_extras(), and capture memory ids from the request headers if they exist

    Args:
        tags: Optional list of tags to apply to the tool
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find the context argument if it exists
            ctx = next(
                (arg for arg in args if isinstance(arg, Context)), kwargs.get("ctx")
            )

            # Extract X-Agent-Id if context and headers exist
            agent_id = None
            if ctx and hasattr(ctx.request_context.request, "headers"):
                headers = ctx.request_context.request.headers
                agent_id = headers.get("x-agent-id")

            # If agent_id was found, get the active storage_id and add them to the kwargs
            if agent_id and MemoryManager.is_initialized():
                storage_id = await get_memory_manager().get_active_storage_id_for_agent(
                    agent_id
                )
                kwargs["agent_id"] = agent_id
                kwargs["storage_id"] = storage_id

            # Call the original function
            return await func(*args, **kwargs)

        # Apply the MCP decorators
        return mcp.tool(tags=tags)(dr_mcp_extras()(wrapper))

    return decorator


def dr_mcp_extras(type: str = "tool") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes log_execution and trace_execution()

    Args:
        type: default is "tool", other options are "prompt", "resource"
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return log_execution(trace_execution(trace_type=type)(func))

    return decorator
