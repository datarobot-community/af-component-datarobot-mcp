import inspect

import pytest

from app.base.tests.ete.tool_base_ete import (
    ETETestExpectations,
    ToolBaseE2E,
    ToolCallTestExpectations,
)


@pytest.fixture(scope="session")
def expectations_for_example_placeholder() -> ETETestExpectations:
    return ETETestExpectations(
        tool_calls_expected=[
            ToolCallTestExpectations(
                name="tool_example_placeholder",
                parameters={"argument1": "test"},
                result="placeholder",
            ),
        ],
        llm_response_content_contains_expectations=[
            "placeholder",
        ],
    )


@pytest.mark.asyncio
class TestRecipePlaceholder(ToolBaseE2E):
    """End-to-end tests for recipe placeholder."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I need to use a tool.
        Can you help me use the example tool with argument "test"?
        """
        ],
    )
    async def test_upload_dataset_to_ai_catalog_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_example_placeholder,
        prompt_template,
    ) -> None:
        prompt = prompt_template.format()
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_example_placeholder,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
