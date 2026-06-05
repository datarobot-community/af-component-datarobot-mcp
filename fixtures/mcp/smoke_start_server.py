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
"""Start the rendered MCP server for CI without calling DataRobot."""

import runpy
from unittest.mock import AsyncMock

from datarobot_genai.drmcp.core.feature_flags import FeatureFlag

# CI uses a placeholder token; drmcp would call /entitlements/evaluate/ and crash
# with 401. Match drmcp's integration test server and skip lineage sync here.
FeatureFlag.is_mcp_tools_gallery_support_enabled_for_static_mcp_container_user = AsyncMock(
    return_value=False
)

if __name__ == "__main__":
    runpy.run_path("app/main.py", run_name="__main__")
