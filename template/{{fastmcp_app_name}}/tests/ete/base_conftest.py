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

# NOTE: This is only to be updated in the base component repository.

import asyncio
from contextlib import asynccontextmanager

import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .mcp_utils import get_dr_mcp_server_url, get_openai_llm_client_config
from .openai_llm_mcp_client import LLMMCPClient


@pytest.fixture
@asynccontextmanager
async def ete_test_mcp_session(headers: dict[str, str] = None):
    """
    Create an MCP session for each test.
    """
    try:
        async with streamablehttp_client(
            url=get_dr_mcp_server_url(), headers=headers or {}
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=5)
                yield session
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Check if the MCP server is running at {get_dr_mcp_server_url()}"
        )


@pytest.fixture(scope="session")
def openai_llm_client() -> LLMMCPClient:
    """
    Create OpenAI LLM MCP client for the test session.
    """
    try:
        config = get_openai_llm_client_config()
        return LLMMCPClient(**config)
    except ValueError as e:
        raise ValueError(f"Missing required OpenAI environment variables: {e}") from e
    except Exception as e:
        raise ConnectionError(f"Failed to create LLM MCP client: {str(e)}") from e
