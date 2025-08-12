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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from app.base.core.dr_mcp_server import DataRobotMCPServer


@pytest.fixture
def mock_mcp() -> MagicMock:
    """Create a mock FastMCP instance."""
    mock = MagicMock(spec=FastMCP)
    mock.list_tools = AsyncMock(
        return_value=[MagicMock(name="tool1"), MagicMock(name="tool2")]
    )
    return mock


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock configuration."""
    mock = MagicMock()
    mock.has.return_value = True
    mock.app_log_level = "INFO"
    return mock


class TestDataRobotMCPServer:
    """Test suite for DataRobotMCPServer class."""

    def test_initialization(self, mock_mcp: MagicMock) -> None:
        """Test server initialization with default transport."""
        server = DataRobotMCPServer(mock_mcp)
        assert server._mcp == mock_mcp
        assert server._mcp_transport == "streamable-http"

    def test_initialization_stdio_transport(self, mock_mcp: MagicMock) -> None:
        """Test server initialization with stdio transport."""
        server = DataRobotMCPServer(mock_mcp, transport="stdio")
        assert server._mcp == mock_mcp
        assert server._mcp_transport == "stdio"

    @patch("app.base.core.dr_mcp_server.get_credentials")
    def test_run_missing_config(self, mock_get_credentials: MagicMock, mock_mcp: MagicMock) -> None:
        """Test server run with missing configuration."""
        mock_creds = MagicMock()
        mock_creds.has_datarobot_credentials.return_value = False
        mock_get_credentials.return_value = mock_creds

        server = DataRobotMCPServer(mock_mcp)
        with pytest.raises(ValueError, match="Missing required DataRobot credentials"):
            server.run()

    @patch("app.base.core.dr_mcp_server.get_config")
    def test_run_success(self, mock_get_config: MagicMock, mock_mcp: MagicMock, mock_config: MagicMock) -> None:
        """Test successful server run."""
        mock_get_config.return_value = mock_config

        server = DataRobotMCPServer(mock_mcp)
        server.run()

        # Verify MCP server was started with correct transport
        mock_mcp.run.assert_called_once_with(transport="streamable-http")

        # Verify tools were listed
        mock_mcp.list_tools.assert_called_once()

    @patch("app.base.core.dr_mcp_server.get_config")
    def test_run_server_error(self, mock_get_config: MagicMock, mock_mcp: MagicMock, mock_config: MagicMock) -> None:
        """Test server run with MCP error."""
        mock_get_config.return_value = mock_config
        mock_mcp.run.side_effect = Exception("Server failed to start")

        server = DataRobotMCPServer(mock_mcp)
        with pytest.raises(Exception, match="Server failed to start"):
            server.run()

    @patch("app.base.core.dr_mcp_server.get_config")
    def test_run_lists_tools(self, mock_get_config: MagicMock, mock_mcp: MagicMock, mock_config: MagicMock) -> None:
        """Test that tools are listed before server start."""
        mock_get_config.return_value = mock_config
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_mcp.list_tools = AsyncMock(return_value=mock_tools)

        server = DataRobotMCPServer(mock_mcp)
        server.run()

        # Verify tools were listed before server start
        mock_mcp.list_tools.assert_called_once()
        mock_mcp.run.assert_called_once()
