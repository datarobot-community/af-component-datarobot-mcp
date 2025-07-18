import inspect

import pytest

from .tool_base_ete import (
    ToolBaseE2E,
)


@pytest.mark.asyncio
class TestModelE2E(ToolBaseE2E):
    """End-to-end tests for model-related functionality."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I have a DataRobot project with ID '{project_id}'.
        I need to find out which is the best performing model in this project. Can you help me identify
        the top model and tell me about its performance metrics?
        """
        ],
    )
    async def test_get_best_model_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_best_model_success,
        classification_project_id,
        prompt_template,
    ):
        prompt = prompt_template.format(project_id=classification_project_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_best_model_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I have a DataRobot project with ID '{project_id}'.
        I need to find out which is the best performing model in this project. Can you help me identify
        the top model and tell me about its performance metrics?
        """
        ],
    )
    async def test_get_best_model_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_best_model_failure,
        nonexistent_project_id,
        prompt_template,
    ):
        prompt = prompt_template.format(project_id=nonexistent_project_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_best_model_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.skip(
        reason="Skipping score_dataset_with_model test, until I fix the dataset_url fixture to point to a valid score dataset for the classification project"
    )
    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project with ID '{project_id}' and I have a DataRobot model with ID '{model_id}'.
        I need to score a dataset at {dataset_url}. Can you help me score the dataset?
        """
        ],
    )
    async def test_score_dataset_with_model_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_score_dataset_with_model_success,
        classification_project_id,
        model_id,
        dataset_url,
        prompt_template,
    ):
        prompt = prompt_template.format(
            project_id=classification_project_id,
            model_id=model_id,
            dataset_url=dataset_url,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_score_dataset_with_model_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project with ID '{project_id}' and I have a DataRobot model with ID '{model_id}'.
        I need to score a dataset at {dataset_url}. Can you help me score the dataset?
        """
        ],
    )
    async def test_score_dataset_with_model_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_score_dataset_with_model_failure,
        classification_project_id,
        nonexistent_model_id,
        dataset_url,
        prompt_template,
    ):
        prompt = prompt_template.format(
            project_id=classification_project_id,
            model_id=nonexistent_model_id,
            dataset_url=dataset_url,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_score_dataset_with_model_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
