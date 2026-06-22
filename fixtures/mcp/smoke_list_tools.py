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

# Native predictive tools registered when ENABLE_PREDICTIVE_TOOLS=true and all
# other native tool groups are disabled (CI server env).
EXPECTED_PREDICTIVE_TOOLS = frozenset(
    {
        "catalog_analyze_dataset",
        "catalog_browse_datastore",
        "catalog_check_timeseries_eligibility",
        "catalog_get_eda_insights",
        "catalog_get_preview",
        "catalog_list_datasets",
        "catalog_list_datastores",
        "catalog_query_datastore",
        "catalog_suggest_ml_problems",
        "catalog_upload_dataset",
        "deployment_create_deployment",
        "deployment_generate_prediction_sample",
        "deployment_get_features",
        "deployment_get_info",
        "deployment_get_list",
        "deployment_get_model_info",
        "deployment_get_prediction_history",
        "deployment_validate_prediction_data",
        "modeling_get_model_feature_impact",
        "modeling_get_model_lift_chart",
        "modeling_get_model_roc",
        "modeling_get_modeldetails",
        "modeling_get_project_dataset",
        "modeling_list_models",
        "modeling_list_projects",
        "modeling_score_dataset",
        "modeling_start_autopilot",
        "models_get_bestmodel",
        "predict_batch_predictions_from_dataset",
        "predict_batch_predictions_from_partition",
        "predict_get_batch_job_status",
        "predict_get_batch_results",
        "predict_score_catalog_realtime",
        "predict_score_inline_realtime",
    }
)


async def _list_tools() -> list[str]:
    url = os.environ.get("MCP_SERVER_URL", "http://localhost:8082/mcp/")
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return sorted(tool.name for tool in tools_result.tools)


async def main() -> int:
    tool_names = await _list_tools()
    tool_set = set(tool_names)
    print(f"Found {len(tool_names)} tools")
    for name in tool_names:
        print(f"  - {name}")

    expected_count = int(
        os.environ.get(
            "MCP_SMOKE_EXPECTED_PREDICTIVE_TOOLS",
            str(len(EXPECTED_PREDICTIVE_TOOLS)),
        )
    )
    if len(tool_names) != expected_count:
        print(
            f"ERROR: expected exactly {expected_count} predictive tool(s), "
            f"got {len(tool_names)}",
            file=sys.stderr,
        )
        return 1

    unexpected_tools = sorted(tool_set - EXPECTED_PREDICTIVE_TOOLS)
    missing_tools = sorted(EXPECTED_PREDICTIVE_TOOLS - tool_set)
    if unexpected_tools or missing_tools:
        if unexpected_tools:
            print(
                f"ERROR: unexpected tool(s): {', '.join(unexpected_tools)}",
                file=sys.stderr,
            )
        if missing_tools:
            print(
                f"ERROR: missing predictive tool(s): {', '.join(missing_tools)}",
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
