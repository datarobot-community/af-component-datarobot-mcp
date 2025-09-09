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

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import Tool, ToolAnnotations

from app.base.core.mcp_instance import register_tools


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock Context with headers."""
    mock_request = MagicMock()
    mock_request.headers = {"x-agent-id": "test-agent-123"}

    mock_request_context = MagicMock()
    mock_request_context.request = mock_request

    ctx = MagicMock(spec=Context)
    ctx.request_context = mock_request_context
    return ctx


@pytest.fixture
def mock_memory_manager() -> MagicMock:
    """Create a mock MemoryManager."""
    mock = MagicMock()
    mock.get_active_storage_id_for_agent = AsyncMock(return_value="test-storage-456")
    return mock


def setup_mock_mcp(mock_mcp: MagicMock, tool_name: str) -> None:
    """Setup mock MCP to handle tool registration verification.

    Args:
        mock_mcp: The MCP mock to setup
        tool_name: The name of the tool that will be registered
    """
    registered_tools: List[Tool] = []

    def add_tool(fn: Any, **kwargs: Any) -> None:
        """Mock add_tool that tracks the registered tool."""
        new_tool = Tool(
            name=kwargs.get("name", ""),
            title=kwargs.get("title"),
            description=kwargs.get("description", ""),
            inputSchema={"type": "object", "properties": {}},
            outputSchema={"type": "object", "properties": {}},
            annotations=kwargs.get("annotations"),
        )
        registered_tools.append(new_tool)

    async def list_tools() -> List[Tool]:
        """Mock list_tools that returns registered tools."""
        # First call will be before registration
        if not registered_tools:
            return []
        # Subsequent calls will include the registered tool
        return registered_tools

    mock_mcp.add_tool = MagicMock(side_effect=add_tool)
    mock_mcp.list_tools = AsyncMock(side_effect=list_tools)


@pytest.mark.asyncio
@patch("app.base.core.mcp_instance.mcp")
@patch("app.base.core.mcp_instance.MemoryManager")
@patch("app.base.core.mcp_instance.get_memory_manager")
async def test_register_tools_basic(
    mock_get_memory_manager: MagicMock,
    mock_memory_manager_cls: MagicMock,
    mock_mcp: MagicMock,
) -> None:
    """Test basic tool registration without tags or memory management."""

    # Setup
    async def dummy_tool() -> None:
        pass

    setup_mock_mcp(mock_mcp, "test_tool")

    # Execute
    await register_tools(
        dummy_tool, name="test_tool", description="Test tool description"
    )

    # Verify
    mock_mcp.add_tool.assert_called_once()
    call_args = mock_mcp.add_tool.call_args[1]
    assert call_args["name"] == "test_tool"
    assert call_args["description"] == "Test tool description"


@pytest.mark.asyncio
@patch("app.base.core.mcp_instance.mcp")
async def test_register_tools_with_tags(mock_mcp: MagicMock) -> None:
    """Test tool registration with tags."""

    # Setup
    async def dummy_tool() -> None:
        pass

    setup_mock_mcp(mock_mcp, "test_tool")
    test_tags = ["tag1", "tag2"]

    # Execute
    await register_tools(dummy_tool, name="test_tool", tags=test_tags)

    # Verify
    mock_mcp.add_tool.assert_called_once()
    call_args = mock_mcp.add_tool.call_args[1]
    annotations = call_args["annotations"]
    assert isinstance(annotations, ToolAnnotations)
    assert annotations.model_dump()["tags"] == test_tags


@pytest.mark.asyncio
@patch("app.base.core.mcp_instance.mcp")
@patch("app.base.core.mcp_instance.MemoryManager")
@patch("app.base.core.mcp_instance.get_memory_manager")
async def test_register_tools_with_memory_management(
    mock_get_memory_manager: MagicMock,
    mock_memory_manager_cls: MagicMock,
    mock_mcp: MagicMock,
    mock_context: MagicMock,
    mock_memory_manager: MagicMock,
) -> None:
    """Test tool registration with memory management."""
    # Setup
    mock_memory_manager_cls.is_initialized = MagicMock(return_value=True)
    mock_get_memory_manager.return_value = mock_memory_manager
    setup_mock_mcp(mock_mcp, "test_tool")

    # Create a tool that expects memory management args
    async def dummy_tool(
        ctx: Context[ServerSession, Dict[str, Any]],
        agent_id: str | None = None,
        storage_id: str | None = None,
    ) -> dict[str, str | None]:
        return {"agent_id": agent_id, "storage_id": storage_id}

    # Execute
    await register_tools(dummy_tool, name="test_tool")

    # Get the wrapped function from add_tool call
    wrapped_fn = mock_mcp.add_tool.call_args[0][0]

    # Call the wrapped function with a context
    result = await wrapped_fn(mock_context)

    # Verify memory IDs were properly injected
    assert result["agent_id"] == "test-agent-123"
    assert result["storage_id"] == "test-storage-456"


@pytest.mark.asyncio
@patch("app.base.core.mcp_instance.mcp")
async def test_register_tools_structured_output(mock_mcp: MagicMock) -> None:
    """Test tool registration with structured output flag."""

    # Setup
    async def dummy_tool() -> None:
        pass

    setup_mock_mcp(mock_mcp, "test_tool")

    # Execute
    await register_tools(dummy_tool, name="test_tool", structured_output=True)

    # Verify
    mock_mcp.add_tool.assert_called_once()
    call_args = mock_mcp.add_tool.call_args[1]
    assert call_args["structured_output"] is True
