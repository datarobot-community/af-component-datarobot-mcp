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

"""Shared MCP execution environment provisioning for deployment and workload paths."""

from __future__ import annotations

import os

import pulumi
import pulumi_datarobot
from datarobot_pulumi_utils.pulumi import resolve_execution_environment_version
from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironments

from .. import project_dir

DEFAULT_EXECUTION_ENVIRONMENT = "Python 3.11 GenAI Agents"


def provision_mcp_execution_environment(
    mcp_server_asset_name: str,
    *,
    resource_name_suffix: str = "",
) -> pulumi_datarobot.ExecutionEnvironment:
    """
    Mirror datarobot-deployment execution environment selection:

    - ``DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT`` set → reference existing EE
      (with GenAI default name normalization and optional version pin).
    - unset → build a new EE from ``{{mcp_app_name}}/docker`` via Pulumi.
    """
    resource_label = (
        mcp_server_asset_name + resource_name_suffix + " Execution Environment"
    )
    _dr_exec_env = os.environ.get(
        "DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT", ""
    ).strip()

    if len(_dr_exec_env) > 0:
        execution_environment_id = _dr_exec_env
        if DEFAULT_EXECUTION_ENVIRONMENT in execution_environment_id:
            pulumi.info("Using default GenAI Agentic Execution Environment.")
            execution_environment_id = (
                RuntimeEnvironments.PYTHON_311_GENAI_AGENTS.value.id
            )

        execution_environment_version_id = resolve_execution_environment_version(
            execution_environment_id,
            "DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID",
        )

        pulumi.info(
            "Using existing execution environment: "
            + execution_environment_id
            + " Version ID: "
            + str(execution_environment_version_id)
        )

        return pulumi_datarobot.ExecutionEnvironment.get(
            id=execution_environment_id,
            version_id=execution_environment_version_id,
            resource_name=resource_label,
        )

    pulumi.info("Using docker folder to compile the execution environment")
    return pulumi_datarobot.ExecutionEnvironment(
        resource_name=resource_label,
        name=mcp_server_asset_name + resource_name_suffix,
        description="Execution environment for MCP server",
        programming_language="python",
        use_cases=["customModel"],
        docker_context_path=str(project_dir.parent / "{{mcp_app_name}}" / "docker"),
        opts=pulumi.ResourceOptions(retain_on_delete=False),
    )
