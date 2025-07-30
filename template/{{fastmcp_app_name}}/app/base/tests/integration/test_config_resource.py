import pytest
from mcp.types import ListResourcesResult, ReadResourceResult, TextResourceContents

from .mcp_utils import integration_test_mcp_session


@pytest.mark.asyncio
class TestMCPConfigResourceIntegration:
    """Integration tests for MCP config resource."""

    async def test_config_resource(self):
        """Complete integration test for MCP config resource"""

        async with integration_test_mcp_session() as session:
            # 1 Test listing available resources
            resources_result: ListResourcesResult = await session.list_resources()
            resource_names = [resource.name for resource in resources_result.resources]

            assert "get_server_config" in resource_names

            # 2 Test getting server config
            result: ReadResourceResult = await session.read_resource(
                "config://server",
            )

            assert len(result.contents) > 0
            assert isinstance(result.contents[0], TextResourceContents)

            result_text = result.contents[0].text
            assert "port" in result_text, f"Result text: {result_text}"
