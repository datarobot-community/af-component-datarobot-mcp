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

# Shared helpers for deployment E2E scripts (deploy + dedicated destroy job).

# Log in to the Pulumi backend the E2E jobs share. Cloud when
# PULUMI_ACCESS_TOKEN is set; otherwise an EXPLICIT workspace-anchored file
# backend. Never `pulumi login --local`: pulumi expands `~` via the passwd
# entry (/root in these containers), NOT the $HOME env var (/github/home), so
# `file://~` state ends up where no staging step looks for it.
pulumi_login_e2e_backend() {
  local workspace="${1:?workspace}"
  if [[ -n "${PULUMI_ACCESS_TOKEN:-}" ]]; then
    echo "Using Pulumi Cloud backend"
    return 0
  fi
  local backend_dir="${workspace}/pulumi-state"
  mkdir -p "${backend_dir}"
  pulumi login "file://${backend_dir}"
}

# Anchor a relative path to the workspace. Workflow env must pass paths
# relative (or via $GITHUB_WORKSPACE): the `${{ github.workspace }}` context
# expands to the runner HOST path in container jobs, which does not exist
# inside the container.
resolve_workspace_path() {
  local workspace="${1:?workspace}"
  local path="${2:?path}"
  if [[ "${path}" != /* ]]; then
    path="${workspace}/${path#./}"
  fi
  printf '%s' "${path}"
}

destroy_pulumi_stack() {
  local stack_name="${1:?STACK_NAME is required}"
  local case_name="${2:?CASE_NAME is required}"
  local rendered_dir="${3:?rendered_dir is required}"

  echo "Cleaning up Pulumi stack ${stack_name} (case=${case_name})"
  set +e

  if [[ -f "${rendered_dir}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${rendered_dir}/.env"
    set +a
  fi

  if [[ ! -d "${rendered_dir}/infra" ]]; then
    echo "No infra directory at ${rendered_dir}/infra; skipping Pulumi cleanup"
    set -e
    return 0
  fi

  cd "${rendered_dir}/infra"

  pulumi_login_e2e_backend "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

  if ! pulumi stack select "${stack_name}" >/dev/null 2>&1; then
    if [[ "${DEPLOY_JOB_RESULT:-}" == "success" ]]; then
      echo "::error::Deploy succeeded but Pulumi stack ${stack_name} is missing from the restored state — its resources are still deployed and would leak. Check the pulumi-state hand-off in the cleanup artifact."
      set -e
      return 1
    fi
    echo "Pulumi stack ${stack_name} not found; nothing to destroy"
    set -e
    return 0
  fi

  pulumi cancel --yes --non-interactive >/dev/null 2>&1

  echo "Running pulumi destroy for stack ${stack_name}"
  pulumi destroy --yes --non-interactive
  local destroy_rc=$?

  if [[ "${destroy_rc}" -eq 0 ]]; then
    if pulumi stack rm "${stack_name}" --yes --force; then
      echo "Pulumi stack ${stack_name} destroyed and removed"
    else
      echo "::warning::pulumi stack rm failed for ${stack_name} (exit $?)"
    fi
  else
    echo "::warning::pulumi destroy failed for ${stack_name} (exit ${destroy_rc}); stack kept in state for manual retry or cleanup"
    set -e
    return "${destroy_rc}"
  fi

  set -e
  return 0
}
