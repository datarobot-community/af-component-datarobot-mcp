#!/bin/sh
# Copyright 2026 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
# This is proprietary source code of DataRobot, Inc. and its affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.

# =============================================================================
# Runtime bootstrap for deployments on pinned platform EEs, i.e. whenever
# DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT is set (e.g. "[DataRobot] Python 3
# MCP"). Two surfaces run it from the model bundle:
#
#   - serverless custom models: the platform invokes /opt/code/start_server.sh
#     (the EE image deliberately ships no start script of its own);
#   - workloads with a generated Dockerfile: infra sets this script as the
#     container entrypoint (workload.py DEFAULT_GENERATED_ENTRYPOINT).
#
# Both sync THIS bundle's uv.lock into the venv before starting, so the bundle's
# pinned versions always win over whatever the EE image baked — the bake is only
# a warm cache that can lag behind (datarobot-genai minor bumps are breaking).
#
# Not used for docker-built paths (serverless-docker, workload-docker): those
# images bake /opt/venv at build time and start via CMD ["python", "-m",
# "app.main"].
#
# POSIX sh on purpose: keep it free of bashisms.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export UV_PROJECT="${CODE_DIR:-/opt/code}"
export UV_COMPILE_BYTECODE=0

# Use a cache dir under the code tree; /tmp/uv-cache is often root-owned on
# pinned platform execution environments.
export UV_CACHE_DIR="${UV_CACHE_DIR:-${SCRIPT_DIR}/.uv-cache}"
mkdir -p "${UV_CACHE_DIR}" 2>/dev/null || true

# Reuse an existing venv when the image provides one: docker EE builds bake
# /opt/venv, and the Python 3 MCP EE points VENV_DIR at its baked venv — the
# sync below then only applies the delta between the bake and this bundle's
# lock. Fall back to a project-local venv under the bundle otherwise.
VENV="${VENV_DIR:-/opt/venv}"
if [ ! -f "${VENV}/bin/activate" ]; then
  VENV="${SCRIPT_DIR}/.venv"
fi
export UV_PROJECT_ENVIRONMENT="${VENV}"

activate_venv() {
  if [ -f "${UV_PROJECT_ENVIRONMENT}/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "${UV_PROJECT_ENVIRONMENT}/bin/activate"
    return 0
  fi
  return 1
}

if ! activate_venv; then
  if command -v uv >/dev/null 2>&1; then
    uv venv "${UV_PROJECT_ENVIRONMENT}" 2>/dev/null || true
    activate_venv || true
  fi
fi

# Sync THIS bundle's lock into the venv — and require it to succeed. The baked
# environment may lag the bundle, and datarobot-genai minor bumps are breaking,
# so silently serving the baked versions is worse than failing loudly here where
# deployment logs (and the component's e2e probe) surface it. Transient failures
# (registry hiccups) get retries; the platform restarts the container on exit.
if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv not found on PATH; cannot sync the bundle's dependencies." >&2
  exit 1
fi
if [ ! -f "${UV_PROJECT}/pyproject.toml" ]; then
  echo "Error: no pyproject.toml under ${UV_PROJECT}; the bundle is incomplete." >&2
  exit 1
fi

run_uv_sync() {
  if [ -f "${UV_PROJECT_ENVIRONMENT}/bin/activate" ]; then
    uv sync --frozen --active --no-progress --color never
  else
    uv sync --frozen --no-progress --color never
  fi
}

attempt=1
max_attempts=3
until run_uv_sync; do
  if [ "${attempt}" -ge "${max_attempts}" ]; then
    echo "Error: uv sync failed ${max_attempts} times; refusing to start against" >&2
    echo "whatever the venv currently holds (it may be a stale baked set)." >&2
    exit 1
  fi
  echo "uv sync failed (attempt ${attempt}/${max_attempts}); retrying in 5s..." >&2
  attempt=$((attempt + 1))
  sleep 5
done
activate_venv || true

# Optional: Dump environment variables for debugging
if [ "${ENABLE_CUSTOM_MODEL_RUNTIME_ENV_DUMP}" = "1" ]; then
    echo "Environment variables:"
    env
fi

# -----------------------------------------------------------------------------
# MCP Server
# Requires: app/ directory in the same location
#
# No --root_path / ROOT_PATH_ARG is threaded through here, unlike the dragent
# start script in the legacy python311_genai_agents environment. A deployed
# server is served under https://<endpoint>/deployments/<id>/directAccess/, and
# drmcp already applies that prefix itself: MCPServerConfig reads URL_PREFIX
# straight from the environment as `mount_path`
# (datarobot_genai/drmcp/core/config.py) and every route is registered through
# prefix_mount_path(). Passing the prefix again would double-prefix it.
# -----------------------------------------------------------------------------
if [ -d "$SCRIPT_DIR/app" ]; then
    echo "Starting Custom Model environment with MCP server"

    # Set Python path to script directory for module imports
    export PYTHONPATH="$SCRIPT_DIR"

    PYTHON_BIN="python"
    if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
      PYTHON_BIN="python3"
    fi

    # Start the MCP server
    exec "${PYTHON_BIN}" -m app.main
fi

# -----------------------------------------------------------------------------
# Error: No valid entry point found
# -----------------------------------------------------------------------------
echo "Error: No valid entry point found in $SCRIPT_DIR"
echo "This environment requires an app/ directory containing an MCP server"
echo "exposing a runnable app.main module."
exit 1
