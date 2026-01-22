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

import pytest
from datarobot_genai.drmcp import integration_test_mcp_session
from mcp.types import CallToolResult, ListToolsResult, TextContent


@pytest.mark.asyncio
class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    async def test_user_tools(self) -> None:
        """Complete integration test for UserTools through MCP"""

        async with integration_test_mcp_session() as session:
            # 1 Test listing available tools
            tools_result: ListToolsResult = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]

            assert "user_tool_smoke_test" in tool_names

            # 2 Test getting user tool smoke test
            result: CallToolResult = await session.call_tool(
                "user_tool_smoke_test",
                {
                    "argument1": "test",
                },
            )

            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)

            result_text = result.content[0].text
            assert "user tool smoke test" in result_text, f"Result text: {result_text}"
