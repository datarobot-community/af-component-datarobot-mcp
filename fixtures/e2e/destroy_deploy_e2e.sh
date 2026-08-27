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
PULUMI_STATE_DIR="${PULUMI_STATE_DIR:-${HOME}/.pulumi}"

# shellcheck disable=SC1091
source "${WORKSPACE}/fixtures/e2e/pulumi_e2e_lib.sh"

RENDERED_DIR="$(resolve_rendered_dir "${WORKSPACE}" "${RENDERED_DIR}")"

if [[ -d "${PULUMI_STATE_DIR}" ]] && [[ -n "$(ls -A "${PULUMI_STATE_DIR}" 2>/dev/null || true)" ]]; then
  mkdir -p "${HOME}/.pulumi"
  cp -a "${PULUMI_STATE_DIR}/." "${HOME}/.pulumi/"
fi

if [[ ! -f "${RENDERED_DIR}/.env" ]]; then
  # A successful deploy always stages rendered/.env — if it's missing here the
  # artifact hand-off broke and exiting quietly would leak the whole stack
  # (this exact failure hid the upload-artifact hidden-file exclusion bug).
  if [[ "${DEPLOY_JOB_RESULT:-}" == "success" ]]; then
    echo "::error::Deploy succeeded but ${RENDERED_DIR}/.env was not restored from the cleanup artifact — refusing to no-op; the stack's resources are still deployed. Check the upload/download of the e2e-pulumi artifact."
    exit 1
  fi
  echo "No rendered .env at ${RENDERED_DIR}/.env; stack may never have been created"
  exit 0
fi

cp "${WORKSPACE}/fixtures/e2e/infra/Pulumi.yaml" "${RENDERED_DIR}/infra/Pulumi.yaml"
cp "${WORKSPACE}/fixtures/e2e/infra/pyproject.toml" "${RENDERED_DIR}/infra/pyproject.toml"
cp "${WORKSPACE}/fixtures/e2e/infra/__main__.py" "${RENDERED_DIR}/infra/__main__.py"
cp "${WORKSPACE}/fixtures/e2e/infra/infra/__init__.py" "${RENDERED_DIR}/infra/infra/__init__.py"

cd "${RENDERED_DIR}/infra"
uv sync --quiet

destroy_pulumi_stack "${STACK_NAME}" "${CASE_NAME}" "${RENDERED_DIR}"
