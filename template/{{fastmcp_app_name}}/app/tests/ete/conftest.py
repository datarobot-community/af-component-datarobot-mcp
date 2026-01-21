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

import os

import pytest
from datarobot_genai.drmcp import LLMMCPClient


@pytest.fixture(scope="session")
def openai_llm_client() -> LLMMCPClient:
    """Create OpenAI LLM MCP client for the test session."""
    try:
        config = {
            "openai_api_key": os.environ.get("OPENAI_API_KEY"),
            "openai_api_base": os.environ.get("OPENAI_API_BASE"),
            "openai_api_deployment_id": os.environ.get("OPENAI_API_DEPLOYMENT_ID"),
            "openai_api_version": os.environ.get("OPENAI_API_VERSION"),
            "save_llm_responses": os.environ.get("SAVE_LLM_RESPONSES", "false").lower()
            == "true",
        }
        return LLMMCPClient(str(config))
    except ValueError as e:
        raise ValueError(f"Missing required OpenAI environment variables: {e}") from e
    except Exception as e:
        raise ConnectionError(f"Failed to create LLM MCP client: {str(e)}") from e
