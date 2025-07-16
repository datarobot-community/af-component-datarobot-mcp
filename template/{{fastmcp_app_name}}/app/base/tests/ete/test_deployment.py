import inspect

import pytest

from .tool_base_ete import (
    ToolBaseE2E,
)


@pytest.mark.asyncio
class TestDeploymentE2E(ToolBaseE2E):
    """End-to-end tests for deployment-related functionality."""

    @pytest.mark.parametrize(
        "prompt",
        [
            """
        I'm working on a machine learning project and I need to list all the deployments I have access to. Can you help me list all the deployments?
        """
        ],
    )
    async def test_list_deployments_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_list_deployments_success,
        prompt,
    ):
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_list_deployments_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project with deployment ID '{deployment_id}'. 
        I need to get the model info from the deployment. Can you help me get the model info from the deployment?
        """
        ],
    )
    async def test_get_model_info_from_deployment_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_model_info_from_deployment_success,
        deployment_id,
        prompt_template,
    ):
        prompt = prompt_template.format(deployment_id=deployment_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_model_info_from_deployment_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project with deployment ID '{deployment_id}'.
        I need to get the model info from the deployment. Can you help me get the model info from the deployment?
        """
        ],
    )
    async def test_get_model_info_from_deployment_failure(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_model_info_from_deployment_failure,
        nonexistent_deployment_id,
        prompt_template,
    ):
        prompt = prompt_template.format(deployment_id=nonexistent_deployment_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_model_info_from_deployment_failure,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
