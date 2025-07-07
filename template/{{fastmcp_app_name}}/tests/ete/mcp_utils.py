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
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Try to load from script directory first, then fall back to root
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent.parent
script_env = script_dir / ".env"
root_env = root_dir / ".env"

# Try script directory first, then root
if script_env.exists():
    print(f"Loading .env from script directory: {script_env}")
    load_dotenv(dotenv_path=script_env, verbose=True, override=True)
else:
    print(f"Loading .env from root directory: {root_env}")
    load_dotenv(dotenv_path=root_env, verbose=True, override=True)


def get_dr_mcp_server_url() -> str:
    """
    Get DataRobot MCP server URL.
    """
    return os.environ.get("DR_MCP_SERVER_URL", "http://localhost:8080/mcp")


def get_openai_llm_client_config() -> Dict[str, str]:
    """
    Get OpenAI LLM client configuration.
    """

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    openai_api_base = os.environ.get("OPENAI_API_BASE")
    openai_api_deployment_id = os.environ.get("OPENAI_API_DEPLOYMENT_ID")
    openai_api_version = os.environ.get("OPENAI_API_VERSION")
    save_llm_responses = os.environ.get("SAVE_LLM_RESPONSES", "true").lower() == "true"

    # Check for OpenAI configuration
    if not openai_api_key:
        raise ValueError("Missing required environment variable: OPENAI_API_KEY")
    if (
        openai_api_base and not openai_api_deployment_id
    ):  # For Azure OpenAI, we need additional variables
        raise ValueError(
            "Missing required environment variable: OPENAI_API_DEPLOYMENT_ID"
        )

    return {
        "openai_api_key": openai_api_key,
        "openai_api_base": openai_api_base,
        "openai_api_deployment_id": openai_api_deployment_id,
        "openai_api_version": openai_api_version,
        "save_llm_responses": save_llm_responses,
    }
