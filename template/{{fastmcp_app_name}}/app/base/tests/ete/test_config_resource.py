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
        openai_llm_client: Any,
        ete_test_mcp_session: Any,
        expectations_for_get_server_config_success: Any,
        prompt_template: str,
    ) -> None:
        async with ete_test_mcp_session as session:
            await self._run_test_with_expectations(
                prompt_template,
                expectations_for_get_server_config_success,
                openai_llm_client,
                session,
                "test_get_server_config_success",
            )
