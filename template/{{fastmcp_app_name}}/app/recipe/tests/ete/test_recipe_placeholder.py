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
from typing import Any

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
        openai_llm_client: Any,
        ete_test_mcp_session: Any,
        expectations_for_example_placeholder: ETETestExpectations,
        prompt_template: str,
    ) -> None:
        prompt = prompt_template.format()
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_example_placeholder,
                openai_llm_client,
                session,
                "test_upload_dataset_to_ai_catalog_success",
            )
