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

RENDERED_DIR="$(resolve_workspace_path "${WORKSPACE}" "${RENDERED_DIR}")"

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

# POST a JSON-RPC initialize to the deployed MCP endpoint until it answers 2xx.
# Catches images that build fine but crash at container start — the gateway then
# returns 5xx, which the stack-outputs check alone would miss.
probe_mcp_endpoint() {
  local endpoint="$1"
  local attempts="${MCP_PROBE_ATTEMPTS:-24}"
  local delay="${MCP_PROBE_DELAY_S:-10}"
  local payload='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"ci-e2e-probe","version":"0.0.1"}}}'
  local body_file status attempt errored_count=0
  body_file="$(mktemp)"

  echo "Probing MCP endpoint ${endpoint}"
  for attempt in $(seq 1 "${attempts}"); do
    status="$(
      curl -sS -o "${body_file}" -w '%{http_code}' --max-time 30 \
        -X POST \
        -H "Authorization: Bearer ${DATAROBOT_API_TOKEN}" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d "${payload}" \
        "${endpoint}" || echo "000"
    )"
    if [[ "${status}" == 2* ]]; then
      echo "MCP endpoint answered initialize (HTTP ${status}, attempt ${attempt}/${attempts})"
      rm -f "${body_file}"
      return 0
    fi
    # A workload reporting ERRORED is a crash loop, not a slow start — waiting
    # out the remaining attempts just burns CI minutes. Require a few sightings
    # in case the status flaps while replicas restart.
    if grep -q "status is 'ERRORED'" "${body_file}" 2>/dev/null; then
      errored_count=$((errored_count + 1))
      if [[ "${errored_count}" -ge 3 ]]; then
        echo "::error::Workload reported status ERRORED ${errored_count} times — container is crash-looping; aborting probe early"
        cat "${body_file}" || true
        rm -f "${body_file}"
        return 1
      fi
    fi
    echo "MCP endpoint not ready (HTTP ${status}, attempt ${attempt}/${attempts}); retrying in ${delay}s"
    sleep "${delay}"
  done

  echo "::error::MCP endpoint ${endpoint} never answered initialize with 2xx (last HTTP ${status})"
  echo "Last response body:"
  cat "${body_file}" || true
  rm -f "${body_file}"
  return 1
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

# Reuse the shared CI execution environment when the docker context is
# unchanged: the NAME/import path in the template still rebuilds the EE image
# on every fresh ephemeral stack (~7-10 min remote build), so CI stamps a
# context hash on the EE and flips to the DEFAULT (get, no build) path on a
# match. Runs after `uv sync` so uv.lock exists. EE_MARK_NAME is set only when
# we build, so a successful `pulumi up` can stamp the hash for the next run.
EE_MARK_NAME=""
EE_MARK_HASH=""
if [[ -n "${DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME:-}" && -z "${DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT:-}" ]]; then
  EE_CONTEXT_HASH="$(cat Dockerfile pyproject.toml uv.lock .dockerignore | sha256sum | cut -c1-16)"
  reuse_id="$(
    python3 "${WORKSPACE}/fixtures/e2e/resolve_ee_reuse.py" resolve \
      --name "${DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME}" \
      --context-hash "${EE_CONTEXT_HASH}"
  )"
  if [[ -n "${reuse_id}" ]]; then
    echo "Reusing execution environment ${reuse_id} (context-hash ${EE_CONTEXT_HASH} unchanged) — skipping EE build"
    export DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT="${reuse_id}"
    append_env_var DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT "${reuse_id}"
  else
    echo "No reusable execution environment for context-hash ${EE_CONTEXT_HASH}; building via Pulumi"
    EE_MARK_NAME="${DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME}"
    EE_MARK_HASH="${EE_CONTEXT_HASH}"
  fi
fi

effective_deployment_type="${MCP_DEPLOYMENT_TYPE:-datarobot-serverless}"
if [[ "${effective_deployment_type}" != "datarobot-workload-preview" ]]; then
  echo "Loading MCP item metadata for datarobot-serverless deploy"
  uv run dev_tools/lineage/cli.py load-and-save-mcp-item-metadata
fi

cd "${RENDERED_DIR}/infra"
uv sync

pulumi_login_e2e_backend "${WORKSPACE}"

# Reuse an existing stack on re-runs; surface real init errors instead of
# hiding them behind the select fallback.
pulumi stack select "${STACK_NAME}" 2>/dev/null || pulumi stack init "${STACK_NAME}" --non-interactive

echo "Deploying stack ${STACK_NAME}"
pulumi up --yes --non-interactive

if [[ -n "${EE_MARK_NAME}" ]]; then
  python3 "${WORKSPACE}/fixtures/e2e/resolve_ee_reuse.py" mark \
    --name "${EE_MARK_NAME}" --context-hash "${EE_MARK_HASH}" || true
fi

python3 - <<'PY'
import json
import subprocess
import sys
from pathlib import Path

outputs = json.loads(subprocess.check_output(["pulumi", "stack", "output", "--json"], text=True))
if not outputs:
    print("ERROR: pulumi stack produced no outputs", file=sys.stderr)
    sys.exit(1)

endpoint_keys = [key for key in outputs if key.endswith("MCP Server MCP Endpoint")] or [
    key for key in outputs if "MCP Endpoint" in key
]
if not endpoint_keys:
    print("ERROR: expected an MCP endpoint stack output", file=sys.stderr)
    print(json.dumps(sorted(outputs.keys()), indent=2), file=sys.stderr)
    sys.exit(1)

Path("mcp_endpoint.txt").write_text(str(outputs[endpoint_keys[0]]), encoding="utf-8")

print("Deployment outputs validated:")
for key in sorted(outputs):
    print(f"  - {key}")
PY

probe_mcp_endpoint "$(cat mcp_endpoint.txt)"

echo "Deployment E2E case ${CASE_NAME} succeeded"
