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

from .config import get_config
from .logging import log_execution
from .telemetry import trace_execution

mcp_server_configs = get_config()

mcp = FastMCP(
    name=mcp_server_configs.mcp_server_name,
    port=mcp_server_configs.mcp_server_port,
    log_level=mcp_server_configs.mcp_server_log_level,
    host=mcp_server_configs.mcp_server_host,
    stateless_http=True,
)


def dr_mcp_tool():
    """Combined decorator that includes mcp.tool(), dr_mcp_extras()"""

    def decorator(func):
        return mcp.tool()(dr_mcp_extras()(func))

    return decorator


def dr_mcp_extras(type: str = "tool"):
    """Combined decorator that includes log_execution and trace_execution()

    Args:
        type: default is "tool", other options are "prompt", "resource"
    """

    def decorator(func):
        return log_execution(trace_execution(trace_type=type)(func))

    return decorator
