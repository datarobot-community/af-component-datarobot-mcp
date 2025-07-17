import inspect

import pytest

from .tool_base_ete import ToolBaseE2E


@pytest.mark.asyncio
class TestProjectsE2E(ToolBaseE2E):
    """End-to-end tests for project-related functionality."""

    @pytest.mark.parametrize(
        "prompt",
        [
            """
        I'm working on a machine learning project and I need to list all the projects I have access to. Can you help me list all the projects?
        """
        ],
    )
    async def test_list_projects_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_list_projects_success,
        prompt,
    ):
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_list_projects_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project ID {project_id} and I need to get the dataset by name '{dataset_name}'. Can you help me get the dataset by name?
        """
        ],
    )
    async def test_get_project_dataset_by_name_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_project_dataset_by_name_success,
        classification_project_id,
        classification_dataset_name,
        prompt_template,
    ):
        prompt = prompt_template.format(
            project_id=classification_project_id,
            dataset_name=classification_dataset_name,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_project_dataset_by_name_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project ID {project_id} and I need to get the dataset by name '{dataset_name}'. Can you help me get the dataset by name?
        """
        ],
    )
    async def test_get_project_dataset_by_name_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_project_dataset_by_name_failure,
        classification_project_id,
        nonexistent_dataset_name,
        prompt_template,
    ):
        prompt = prompt_template.format(
            project_id=classification_project_id, dataset_name=nonexistent_dataset_name
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_project_dataset_by_name_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project {project_name} and I need to get the dataset by name '{dataset_name}'. Can you help me get the dataset by name?
        """
        ],
    )
    async def test_get_project_dataset_by_name_success_with_multiple_calls(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_project_dataset_by_name_success_with_multiple_calls,
        classification_project_name,
        classification_dataset_name,
        prompt_template,
    ):
        prompt = prompt_template.format(
            project_name=classification_project_name,
            dataset_name=classification_dataset_name,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_project_dataset_by_name_success_with_multiple_calls,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
