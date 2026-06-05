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
"""Smoke test: connect to a running MCP server and list registered tools."""

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def _list_tools() -> list[str]:
    url = os.environ.get("MCP_SERVER_URL", "http://localhost:8082/mcp/")
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return sorted(tool.name for tool in tools_result.tools)


async def main() -> int:
    tool_names = await _list_tools()
    print(f"Found {len(tool_names)} tools")
    for name in tool_names:
        print(f"  - {name}")

    min_tools = int(os.environ.get("MCP_SMOKE_MIN_TOOLS", "1"))
    if len(tool_names) < min_tools:
        print(
            f"ERROR: expected at least {min_tools} tool(s), got {len(tool_names)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
