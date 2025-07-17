import inspect

import pytest

from .tool_base_ete import (
    ToolBaseE2E,
)


@pytest.mark.asyncio
class TestDataE2E(ToolBaseE2E):
    """End-to-end tests for data-related functionality."""

    # Note keep this test to run first, so that list datasets test can run after it for the sake of asserts
    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I need to upload a dataset to the DataRobot AI Catalog.
        Can you help me upload the dataset at {file_path}?
        """
        ],
    )
    async def test_upload_dataset_to_ai_catalog_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_upload_dataset_to_ai_catalog_success,
        prompt_template,
        diabetes_scoring_small_file_path,
    ):
        prompt = prompt_template.format(file_path=diabetes_scoring_small_file_path)
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_upload_dataset_to_ai_catalog_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I need to upload a dataset to the DataRobot AI Catalog.
        Can you help me upload the dataset at {file_path}?
        """
        ],
    )
    async def test_upload_dataset_to_ai_catalog_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_upload_dataset_to_ai_catalog_failure,
        prompt_template,
        nonexistent_file_path,
    ):
        prompt = prompt_template.format(file_path=nonexistent_file_path)
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_upload_dataset_to_ai_catalog_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt",
        [
            """
        I'm working on a machine learning project and I need to find out which datasets are available in the DataRobot AI Catalog.
        Can you help me list all the datasets in the AI Catalog?
        """
        ],
    )
    async def test_list_ai_catalog_items_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_list_ai_catalog_items_success,
        prompt,
    ):
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_list_ai_catalog_items_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
