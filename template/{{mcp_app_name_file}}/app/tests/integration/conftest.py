# Copyright 2026 DataRobot, Inc.
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


import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def _integration_disable_datarobot_api_at_startup():
    """Disable dynamic tools/prompts registration so the server does not call DataRobot API at startup.

    Saves and restores env vars so they do not leak to other test modules (e.g. ete).
    """
    keys = (
        "MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP",
        "MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP",
    )
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP"] = "false"
        os.environ["MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP"] = "false"
        yield
    finally:
        for k in keys:
            if saved[k] is not None:
                os.environ[k] = saved[k]
            else:
                os.environ.pop(k, None)
