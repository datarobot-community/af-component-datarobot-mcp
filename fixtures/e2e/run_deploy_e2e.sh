#!/usr/bin/env bash
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
set -euo pipefail

RENDERED_DIR="${RENDERED_DIR:-./rendered}"
STACK_NAME="${STACK_NAME:?STACK_NAME is required}"
CASE_NAME="${CASE_NAME:?CASE_NAME is required}"
WORKSPACE="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

# shellcheck disable=SC1091
source "${WORKSPACE}/fixtures/e2e/pulumi_e2e_lib.sh"

RENDERED_DIR="$(resolve_rendered_dir "${WORKSPACE}" "${RENDERED_DIR}")"

echo "Running deployment E2E case: ${CASE_NAME}"

append_env_var() {
  local key="$1"
  local value="$2"
  if [[ -n "${value}" ]]; then
    printf '%s=%q\n' "${key}" "${value}" >> "${RENDERED_DIR}/.env"
  fi
}

normalize_datarobot_api_endpoint() {
  local endpoint="${1%/}"
  if [[ "${endpoint}" == */api/v2 ]]; then
    printf '%s' "${endpoint}"
  else
    printf '%s/api/v2' "${endpoint}"
  fi
}

validate_datarobot_credentials() {
  local http_status

  http_status="$(
    curl -sS -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer ${DATAROBOT_API_TOKEN}" \
      "${DATAROBOT_ENDPOINT}/account/info/" || echo "000"
  )"

  if [[ "${http_status}" != "200" ]]; then
    echo "::error::DataRobot API rejected credentials (HTTP ${http_status}) for ${DATAROBOT_ENDPOINT}. Verify DATAROBOT_API_TOKEN and DATAROBOT_ENDPOINT (must resolve to the API v2 base, e.g. https://app.datarobot.com/api/v2)."
    exit 1
  fi

  echo "DataRobot API credentials validated against ${DATAROBOT_ENDPOINT}"
}

cp "${WORKSPACE}/fixtures/e2e/infra/Pulumi.yaml" "${RENDERED_DIR}/infra/Pulumi.yaml"
cp "${WORKSPACE}/fixtures/e2e/infra/pyproject.toml" "${RENDERED_DIR}/infra/pyproject.toml"
cp "${WORKSPACE}/fixtures/e2e/infra/__main__.py" "${RENDERED_DIR}/infra/__main__.py"
cp "${WORKSPACE}/fixtures/e2e/infra/infra/__init__.py" "${RENDERED_DIR}/infra/infra/__init__.py"

if [[ -z "${DATAROBOT_API_TOKEN:-}" ]]; then
  echo "::error::DATAROBOT_API_TOKEN is not set. Add it as a repository or organization Actions secret."
  exit 1
fi

DATAROBOT_API_TOKEN="$(printf '%s' "${DATAROBOT_API_TOKEN}" | tr -d '\r\n')"
DATAROBOT_ENDPOINT="$(normalize_datarobot_api_endpoint "${DATAROBOT_ENDPOINT:-https://app.datarobot.com}")"
export DATAROBOT_API_TOKEN DATAROBOT_ENDPOINT

validate_datarobot_credentials

cat > "${RENDERED_DIR}/.env" <<EOF
MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP=false
MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP=false
ENABLE_PREDICTIVE_TOOLS=true
OTEL_ENABLED=false
EOF

append_env_var DATAROBOT_ENDPOINT "${DATAROBOT_ENDPOINT}"
append_env_var DATAROBOT_API_TOKEN "${DATAROBOT_API_TOKEN}"
append_env_var PULUMI_CONFIG_PASSPHRASE "${PULUMI_CONFIG_PASSPHRASE}"
append_env_var SESSION_SECRET_KEY "${SESSION_SECRET_KEY}"
append_env_var MCP_DEPLOYMENT_TYPE "${MCP_DEPLOYMENT_TYPE:-}"
append_env_var MCP_WORKLOAD_DOCKERFILE_PATH "${MCP_WORKLOAD_DOCKERFILE_PATH:-}"
# DEFAULT: reuse an existing EE (skip Docker build). NAME: only when DEFAULT is empty;
# names a new EE built from scratch (CI uses a stable NAME — see use-cases.yaml header).
append_env_var DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT "${DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT:-}"
append_env_var DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID "${DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID:-}"
append_env_var DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME "${DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME:-}"

set -a
# shellcheck disable=SC1091
source "${RENDERED_DIR}/.env"
set +a

cd "${RENDERED_DIR}/mcp_server"
uv sync

effective_deployment_type="${MCP_DEPLOYMENT_TYPE:-datarobot-serverless}"
if [[ "${effective_deployment_type}" != "datarobot-workload-preview" ]]; then
  echo "Loading MCP item metadata for datarobot-serverless deploy"
  uv run dev_tools/lineage/cli.py load-and-save-mcp-item-metadata
fi

cd "${RENDERED_DIR}/infra"
uv sync

if [[ -n "${PULUMI_ACCESS_TOKEN:-}" ]]; then
  echo "Using Pulumi Cloud backend"
else
  pulumi login --local
fi

pulumi stack init "${STACK_NAME}" --non-interactive 2>/dev/null || pulumi stack select "${STACK_NAME}"

echo "Deploying stack ${STACK_NAME}"
pulumi up --yes --non-interactive

python3 - <<'PY'
import json
import subprocess
import sys

outputs = json.loads(subprocess.check_output(["pulumi", "stack", "output", "--json"], text=True))
if not outputs:
    print("ERROR: pulumi stack produced no outputs", file=sys.stderr)
    sys.exit(1)

endpoint_keys = [key for key in outputs if "MCP Endpoint" in key or "MCP Server MCP Endpoint" in key]
if not endpoint_keys:
    print("ERROR: expected an MCP endpoint stack output", file=sys.stderr)
    print(json.dumps(sorted(outputs.keys()), indent=2), file=sys.stderr)
    sys.exit(1)

print("Deployment outputs validated:")
for key in sorted(outputs):
    print(f"  - {key}")
PY

echo "Deployment E2E case ${CASE_NAME} succeeded"
