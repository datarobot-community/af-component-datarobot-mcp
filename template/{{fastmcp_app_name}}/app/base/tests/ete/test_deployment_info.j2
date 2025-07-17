import inspect

import pytest

from .tool_base_ete import ToolBaseE2E


@pytest.mark.asyncio
class TestDeploymentInfoE2E(ToolBaseE2E):
    """End-to-end tests for deployment info functionality."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            I have a DataRobot deployment with ID '{deployment_id}' and I need to understand what features it requires for making predictions.
            Can you help me get information about the required input features, their types, and importance scores?
            """
        ],
    )
    async def test_get_deployment_features_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_deployment_features_success,
        deployment_id,
        prompt_template,
    ):
        prompt = prompt_template.format(deployment_id=deployment_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_deployment_features_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            I have a DataRobot deployment with ID '{deployment_id}' and I need to create a template CSV file for making predictions.
            Can you help me generate a template with 5 rows of sample data that matches the deployment's requirements?
            """
        ],
    )
    async def test_generate_prediction_data_template_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_generate_prediction_data_template_success,
        deployment_id,
        prompt_template,
    ):
        prompt = prompt_template.format(deployment_id=deployment_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_generate_prediction_data_template_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.skip(
        reason="Skipping this test for now until we have a way to validate score file for the classification project to replace diabetes_scoring_small_file_path"
    )
    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            I have a DataRobot deployment with ID '{deployment_id}' and a CSV file at '{file_path}'.
            Can you help me validate if this file is suitable for making predictions with this deployment?
            """
        ],
    )
    async def test_validate_prediction_data_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_validate_prediction_data_success,
        deployment_id,
        diabetes_scoring_small_file_path,
        prompt_template,
    ):
        prompt = prompt_template.format(
            deployment_id=deployment_id,
            file_path=diabetes_scoring_small_file_path,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_validate_prediction_data_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            I have a DataRobot deployment with ID '{deployment_id}' and I need to validate a CSV file at '{file_path}'.
            Can you check if this file is suitable for making predictions?
            """
        ],
    )
    async def test_validate_prediction_data_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_validate_prediction_data_failure,
        deployment_id,
        nonexistent_file_path,
        prompt_template,
    ):
        prompt = prompt_template.format(
            deployment_id=deployment_id,
            file_path=nonexistent_file_path,
        )

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_validate_prediction_data_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
