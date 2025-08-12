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

import inspect

import pytest

from .tool_base_ete import (
    ETETestExpectations,
    ToolBaseE2E,
    ToolCallTestExpectations,
)


@pytest.fixture(scope="session")
def expectations_for_get_deployment_info_prompt_success(
    deployment_id: str,
) -> ETETestExpectations:
    expected_text = f"""
    Show me detailed information about deployment {deployment_id}, including:
    - Model type and configuration
    - Required features and their importance
    - Target variable details
    - Time series configuration (if applicable)
    """
    return ETETestExpectations(
        tool_calls_expected=[
            ToolCallTestExpectations(
                name="get_deployment_info_prompt",
                parameters={"deployment_id": deployment_id},
                result=expected_text,
            ),
        ],
        llm_response_content_contains_expectations=[
            "model type",
            "configuration",
            "features",
            "importance",
            "target",
            "time series",
            deployment_id,
        ],
    )


@pytest.mark.asyncio
class TestDeploymentInfoPromptsE2E(ToolBaseE2E):
    """End-to-end tests for deployment info prompts functionality."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
            I need to get the prompt for detailed information about a deployment with ID '{deployment_id}'.
            What prompt should I use to get model type, features, target variable, and time series configuration?
            """
        ],
    )
    async def test_get_deployment_info_prompt_success(
        self,
        openai_llm_client,
        ete_test_mcp_session,
        expectations_for_get_deployment_info_prompt_success,
        deployment_id,
        prompt_template,
    ):
        prompt = prompt_template.format(deployment_id=deployment_id)

        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_get_deployment_info_prompt_success,
                openai_llm_client,
                session,
                inspect.currentframe().f_code.co_name,
            )
