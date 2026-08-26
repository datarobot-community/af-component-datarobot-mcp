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

# Resolve before any cd — relative paths break after cd into mcp_server/infra.
if [[ "${RENDERED_DIR}" != /* ]]; then
  RENDERED_DIR="${WORKSPACE}/${RENDERED_DIR#./}"
fi

cleanup() {
  local exit_code=$?
  if [[ "${SKIP_DESTROY:-false}" == "true" ]]; then
    echo "Skipping destroy because SKIP_DESTROY=true"
    return "${exit_code}"
  fi

  echo "Cleaning up Pulumi stack ${STACK_NAME} (case=${CASE_NAME})"
  set +e
  cd "${RENDERED_DIR}/infra"
  if pulumi stack select "${STACK_NAME}" >/dev/null 2>&1; then
    pulumi destroy --yes --non-interactive
    pulumi stack rm "${STACK_NAME}" --yes --force
  fi
  set -e
  return "${exit_code}"
}
trap cleanup EXIT

echo "Running deployment E2E case: ${CASE_NAME}"

append_env_var() {
  local key="$1"
  local value="$2"
  if [[ -n "${value}" ]]; then
    printf '%s=%q\n' "${key}" "${value}" >> "${RENDERED_DIR}/.env"
  fi
}

validate_datarobot_credentials() {
  local endpoint="${DATAROBOT_ENDPOINT%/}"
  local http_status

  http_status="$(
    curl -sS -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer ${DATAROBOT_API_TOKEN}" \
      "${endpoint}/api/v2/account/info/" || echo "000"
  )"

  if [[ "${http_status}" != "200" ]]; then
    echo "::error::DataRobot API rejected credentials (HTTP ${http_status}) for ${endpoint}. Verify DATAROBOT_API_TOKEN and DATAROBOT_ENDPOINT (repository/org secret and variable)."
    exit 1
  fi

  echo "DataRobot API credentials validated against ${endpoint}"
}

cp "${WORKSPACE}/fixtures/e2e/infra/Pulumi.yaml" "${RENDERED_DIR}/infra/Pulumi.yaml"
cp "${WORKSPACE}/fixtures/e2e/infra/pyproject.toml" "${RENDERED_DIR}/infra/pyproject.toml"
cp "${WORKSPACE}/fixtures/e2e/infra/__main__.py" "${RENDERED_DIR}/infra/__main__.py"
cp "${WORKSPACE}/fixtures/e2e/infra/infra/__init__.py" "${RENDERED_DIR}/infra/infra/__init__.py"

cat > "${RENDERED_DIR}/.env" <<EOF
MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP=false
MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP=false
ENABLE_PREDICTIVE_TOOLS=true
OTEL_ENABLED=false
EOF

append_env_var DATAROBOT_ENDPOINT "${DATAROBOT_ENDPOINT:-https://app.datarobot.com}"
append_env_var DATAROBOT_API_TOKEN "${DATAROBOT_API_TOKEN:-}"
append_env_var PULUMI_CONFIG_PASSPHRASE "${PULUMI_CONFIG_PASSPHRASE}"
append_env_var SESSION_SECRET_KEY "${SESSION_SECRET_KEY}"
append_env_var MCP_DEPLOYMENT_TYPE "${MCP_DEPLOYMENT_TYPE:-}"
append_env_var MCP_WORKLOAD_DOCKERFILE_PATH "${MCP_WORKLOAD_DOCKERFILE_PATH:-}"
append_env_var DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT "${DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT:-}"
append_env_var DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID "${DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID:-}"

set -a
# shellcheck disable=SC1091
source "${RENDERED_DIR}/.env"
set +a

if [[ -z "${DATAROBOT_API_TOKEN:-}" ]]; then
  echo "::error::DATAROBOT_API_TOKEN is not set. Add it as a repository or organization Actions secret."
  exit 1
fi

DATAROBOT_API_TOKEN="$(printf '%s' "${DATAROBOT_API_TOKEN}" | tr -d '\r\n')"
DATAROBOT_ENDPOINT="${DATAROBOT_ENDPOINT:-https://app.datarobot.com}"
DATAROBOT_ENDPOINT="${DATAROBOT_ENDPOINT%/}"
export DATAROBOT_API_TOKEN DATAROBOT_ENDPOINT

validate_datarobot_credentials

cd "${RENDERED_DIR}/mcp_server"
uv sync --all-extras
cp pyproject.toml uv.lock docker/

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

echo "Planning deployment with pulumi preview"
pulumi preview --non-interactive

echo "Deploying stack ${STACK_NAME}"
if ! pulumi up --yes --non-interactive; then
  echo "::error::pulumi up failed for case ${CASE_NAME}. See provider errors above (common causes: invalid token, wrong DATAROBOT_ENDPOINT, or missing deploy permissions)."
  exit 1
fi

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
