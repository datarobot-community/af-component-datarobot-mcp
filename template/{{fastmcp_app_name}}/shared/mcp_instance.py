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

from mcp.server.fastmcp import FastMCP

from shared.config import get_config

mcp_server_configs = get_config()

mcp = FastMCP(
    name=mcp_server_configs.name,
    port=mcp_server_configs.port,
    log_level=mcp_server_configs.log_level,
    host=mcp_server_configs.host,
    stateless_http=True,
)
