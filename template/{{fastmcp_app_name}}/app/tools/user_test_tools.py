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

import logging

from datarobot_genai.drmcp import dr_mcp_tool

logger = logging.getLogger(__name__)

"""
This tool is excluded from the public repo, used for a smoke test on user tools functionality.
"""


@dr_mcp_tool(tags={"user", "tools", "smoke-test"})
async def user_tool_smoke_test(argument1: str) -> str:
    """
    A user tool used for a smoke test on user tools functionality.

    Args:
        argument1: A smoke test argument.
    Returns:
        A smoke test return value.
    """
    return "user tool smoke test"
