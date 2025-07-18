import pytest
from mcp.types import CallToolResult, ListToolsResult, TextContent

from app.base.tests.integration.mcp_utils import integration_test_mcp_session


@pytest.mark.asyncio
class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    async def test_example(self):
        """Complete integration test for RecipePlaceholder through MCP"""

        async with integration_test_mcp_session() as session:
            # 1 Test listing available tools
            tools_result: ListToolsResult = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]

            assert "tool_example_placeholder" in tool_names

            # 2 Test getting example placeholder
            result: CallToolResult = await session.call_tool(
                "tool_example_placeholder",
                {
                    "argument1": "test",
                },
            )

            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)

            result_text = result.content[0].text
            assert "placeholder" in result_text, f"Result text: {result_text}"
