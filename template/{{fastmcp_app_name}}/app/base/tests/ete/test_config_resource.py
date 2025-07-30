import inspect

import pytest

from .tool_base_ete import (
    ETETestExpectations,
    ToolBaseE2E,
    ToolCallTestExpectations,
)


@pytest.fixture(scope="session")
def expectations_for_get_server_config_success() -> ETETestExpectations:
    return ETETestExpectations(
        tool_calls_expected=[
            ToolCallTestExpectations(
                name="get_server_config",
                parameters={},
                result="name",
            ),
        ],
        llm_response_content_contains_expectations=[
            "server configuration",
            "name",
            "port",
            "host",
        ],
    )


@pytest.mark.asyncio
class TestConfigResourceE2E(ToolBaseE2E):
    """End-to-end tests for configuration resource functionality."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            Can you show me the server configuration? I need to see details like the name, port, and host settings.
            """
        ],
    )
    async def test_get_server_config_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_server_config_success,
        prompt_template,
    ):
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt_template,
                expectations_for_get_server_config_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
