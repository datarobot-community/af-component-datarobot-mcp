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

from typing import Any, Callable, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool as MCPTool
from mcp.types import ToolAnnotations

from .config import get_config
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
        **kwargs,
    ):
        """
        Extended tool decorator that supports tags and other annotations.

        Args:
            name: Tool name
            description: Tool description
            tags: List of tags for the tool
            **kwargs: Additional annotations to pass to ToolAnnotations
        """

        def decorator(func: Callable[..., Any]):
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