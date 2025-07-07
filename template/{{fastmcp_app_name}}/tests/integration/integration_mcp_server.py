#!/usr/bin/env python3

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

"""Simple MCP server for integration testing."""

import glob
import os

from mcp_server_stubs import create_test_mock_dr_client

from shared.dr_mcp_server import DataRobotMCPServer
from shared.mcp_instance import mcp


def _mock_dependencies():
    """
    Monkey patch get_sdk_client directly in the tools modules
    """
    should_mock_dr_client = os.environ.get("SHOULD_MOCK_DR_CLIENT", "true") == "true"
    if should_mock_dr_client:
        dr_client = create_test_mock_dr_client()

        # Monkey patch get_sdk_client in all tool modules
        # Dynamically import all modules from tools to register them with MCP
        tools_dir = os.path.dirname(os.path.dirname(__file__)) + "/tools"
        for file in glob.glob(os.path.join(tools_dir, "*.py")):
            if os.path.basename(file) != "__init__.py":
                module_name = f"tools.{os.path.splitext(os.path.basename(file))[0]}"
                module = __import__(module_name, fromlist=["get_sdk_client"])
                setattr(module, "get_sdk_client", lambda: dr_client)


def main():
    """Run the integration test MCP server with test mocks."""

    _mock_dependencies()

    server = DataRobotMCPServer(mcp, transport="stdio")
    server.run()


if __name__ == "__main__":
    main()
