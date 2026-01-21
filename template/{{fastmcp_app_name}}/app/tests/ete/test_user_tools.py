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

from typing import Any

import pytest
from datarobot_genai.drmcp import (
    ETETestExpectations,
    ToolBaseE2E,
    ToolCallTestExpectations,
    ete_test_mcp_session,
)


@pytest.fixture(scope="session")
def expectations_for_user_tool_smoke_test() -> ETETestExpectations:
    return ETETestExpectations(
        tool_calls_expected=[
            ToolCallTestExpectations(
                name="user_tool_smoke_test",
                parameters={"argument1": "test"},
                result="user tool smoke test",
            ),
        ],
        llm_response_content_contains_expectations=[
            "user tool smoke test",
            "test",
            "smoke-test",
            "tool",
            "user",
            "tools",
            "smoke test",
        ],
    )


@pytest.mark.asyncio
class TestUserTools(ToolBaseE2E):
    """End-to-end tests for user tools."""

    @pytest.mark.parametrize(
        "prompt_template",
        [
            """
        I'm working on a machine learning project and I need to use a tool.
        Can you help me use the user tool smoke test with argument "test"?
        """
        ],
    )
    async def test_user_tool_smoke_test_success(
        self,
        openai_llm_client: Any,
        expectations_for_user_tool_smoke_test: ETETestExpectations,
        prompt_template: str,
    ) -> None:
        prompt = prompt_template.format()
        async with ete_test_mcp_session() as session:
            await self._run_test_with_expectations(
                prompt,
                expectations_for_user_tool_smoke_test,
                openai_llm_client,
                session,
                "test_user_tool_smoke_test_success",
            )
