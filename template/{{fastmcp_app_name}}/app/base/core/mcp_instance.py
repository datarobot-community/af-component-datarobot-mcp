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

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import AnyFunction, ToolAnnotations
from mcp.types import Tool as MCPTool

from .config import MCPServerConfig, get_config
from .logging import log_execution
from .memory_management import MemoryManager, get_memory_manager
from .telemetry import trace_execution
from .tool_filter import filter_tools_by_tags, list_all_tags

logger = logging.getLogger(__name__)


async def get_agent_and_storage_ids(
    args: Tuple[Any, ...], kwargs: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract agent ID from request context and get corresponding storage ID.

    Args:
        args: Positional arguments that may contain a Context object
        kwargs: Keyword arguments that may contain a Context object

    Returns:
        Tuple of (agent_id, storage_id), both may be None if not found
    """
    # Find the context argument if it exists
    ctx = next((arg for arg in args if isinstance(arg, Context)), kwargs.get("ctx"))

    # Extract X-Agent-Id if context and headers exist
    agent_id = None
    if (
        ctx
        and ctx.request_context
        and ctx.request_context.request
        and hasattr(ctx.request_context.request, "headers")
    ):
        headers = ctx.request_context.request.headers
        agent_id = headers.get("x-agent-id")

    # If agent_id was found, get the active storage_id
    storage_id = None
    if agent_id and MemoryManager.is_initialized():
        memory_manager = get_memory_manager()
        if memory_manager:
            storage_id = await memory_manager.get_active_storage_id_for_agent(agent_id)

    return agent_id, storage_id


class TaggedFastMCP(FastMCP):
    """
    Extended FastMCP that supports tags and other annotations directly in the tool decorator.
    """

    def tool(  # type: ignore[override]
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
        filtered_tools = filter_tools_by_tags(list(all_tools), tags, match_all)

        return filtered_tools  # type: ignore[return-value]

    async def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all registered tools.

        Returns:
            List of all unique tags sorted alphabetically.
        """
        all_tools = await self.list_tools()
        return list_all_tags(list(all_tools))


# Create the tagged MCP instance
mcp_server_configs: MCPServerConfig = get_config()

mcp = TaggedFastMCP(
    name=mcp_server_configs.mcp_server_name,
    port=mcp_server_configs.mcp_server_port,
    log_level=mcp_server_configs.mcp_server_log_level,
    host=mcp_server_configs.mcp_server_host,
    stateless_http=True,
)


def dr_core_mcp_tool(
    tags: Optional[List[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes mcp.tool() and dr_mcp_extras()"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return mcp.tool(tags=tags)(dr_mcp_extras()(func))

    return decorator


async def memory_aware_wrapper(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """
    Wrapper function that adds memory management capabilities to any async function.
    Extracts agent and storage IDs from the context and adds them to kwargs if found.

    Args:
        func: The async function to wrap
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of calling the wrapped function
    """
    # Get agent and storage IDs from context
    agent_id, storage_id = await get_agent_and_storage_ids(args, kwargs)

    # Add IDs to kwargs if found
    if agent_id and storage_id:
        kwargs["agent_id"] = agent_id
        kwargs["storage_id"] = storage_id

    # Call the original function
    return await func(*args, **kwargs)


def dr_mcp_tool(
    tags: Optional[List[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes mcp.tool(), dr_mcp_extras(), and capture memory ids from the request headers if they exist

    Args:
        tags: Optional list of tags to apply to the tool
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await memory_aware_wrapper(func, *args, **kwargs)

        # Apply the MCP decorators
        return mcp.tool(tags=tags)(dr_mcp_extras()(wrapper))

    return decorator


def dr_mcp_extras(
    type: str = "tool",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Combined decorator that includes log_execution and trace_execution()

    Args:
        type: default is "tool", other options are "prompt", "resource"
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return log_execution(trace_execution(trace_type=type)(func))

    return decorator


async def register_tools(
    fn: AnyFunction,
    name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    structured_output: Optional[bool] = None,
) -> None:
    """
    Register new tools after server has started.

    Args:
        fn: The function to register as a tool
        name: Optional name for the tool (defaults to function name)
        title: Optional human-readable title for the tool
        description: Optional description of what the tool does
        tags: Optional list of tags to apply to the tool
        structured_output: Controls whether the tool's output is structured or unstructured
    """
    tool_name = name or fn.__name__
    logger.info(f"Registering new tool: {tool_name}")

    # Create a memory-aware version of the function
    @wraps(fn)
    async def memory_aware_fn(*args: Any, **kwargs: Any) -> Any:
        return await memory_aware_wrapper(fn, *args, **kwargs)

    # Apply dr_mcp_extras to the memory-aware function
    wrapped_fn = dr_mcp_extras()(memory_aware_fn)

    # Create annotations with tags if provided
    annotations = ToolAnnotations(tags=tags)

    # Register the tool
    mcp.add_tool(
        wrapped_fn,
        name=tool_name,
        title=title,
        description=description,
        annotations=annotations,
        structured_output=structured_output,
    )

    # Verify tool is registered
    tools = await mcp.list_tools()
    if not any(tool.name == tool_name for tool in tools):
        raise RuntimeError(f"Tool {tool_name} was not registered successfully")

    logger.info(f"Registered tools: {len(tools)}")
