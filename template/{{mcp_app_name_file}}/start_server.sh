#!/bin/sh
# Copyright 2026 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
# This is proprietary source code of DataRobot, Inc. and its affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.

# =============================================================================
# Startup script for MCP Server custom models.
#
# Copied to /opt/code/start_server.sh in the image and invoked by the platform
# for the custom-model surface only. The Workload API (code-to-workload) surface
# never runs this script -- it generates its own Dockerfile and entrypoint on top
# of this image.
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

# Custom docker EE builds bake /opt/venv at image build time. Pinned platform
# EEs do not — fall back to a project-local venv under the bundle.
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

# Sync dependencies when uv and a lock file are available. Never block startup.
if command -v uv >/dev/null 2>&1 && [ -f "${UV_PROJECT}/pyproject.toml" ]; then
  if [ -f "${UV_PROJECT_ENVIRONMENT}/bin/activate" ]; then
    uv sync --frozen --active --no-progress --color never 2>/dev/null || true
  else
    uv sync --frozen --no-progress --color never 2>/dev/null || true
    activate_venv || true
  fi
fi

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
# branch in python311_genai_agents. A deployed server is served under
# https://<endpoint>/deployments/<id>/directAccess/, and drmcp already applies
# that prefix itself: DRMCPConfig reads URL_PREFIX straight from the environment
# as `mount_path` (datarobot_genai/drmcp/core/config.py) and every route is
# registered through prefix_mount_path(). Passing the prefix again would
# double-prefix it.
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
