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

"""Source bundle helpers for workload image builds."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pulumi

DOCKER_DIR = "docker"
DOCKERFILE_RELATIVE_PATH = f"{DOCKER_DIR}/Dockerfile"
START_SERVER_SOURCE_RELATIVE_PATH = f"{DOCKER_DIR}/start_server.sh"
ROOT_START_SERVER_RELATIVE_PATH = "start_server.sh"
ROOT_REQUIREMENTS_RELATIVE_PATH = "requirements.txt"
DOCKER_REQUIREMENTS_RELATIVE_PATH = f"{DOCKER_DIR}/requirements.txt"


def _uv_command() -> list[str]:
    uv = shutil.which("uv")
    if uv is None:
        message = (
            "uv is required to generate docker/requirements.txt for workload image builds. "
            "Install uv or run `task install` before deploying."
        )
        pulumi.error(message)
        raise RuntimeError(message)
    return [uv]


def generate_docker_requirements_txt(deployments_path: Path) -> str:
    """Export locked dependencies as requirements.txt content via uv."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "VIRTUAL_ENV"}
    }
    result = subprocess.run(
        [
            *_uv_command(),
            "export",
            "--format",
            "requirements-txt",
            "--no-emit-project",
            "--project",
            str(deployments_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(deployments_path),
        env=env,
    )
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        message = (
            "Failed to generate docker requirements.txt via `uv export`: "
            f"{stderr or 'unknown error'}"
        )
        pulumi.error(message)
        raise RuntimeError(message)
    return result.stdout


def ensure_docker_requirements_txt(deployments_path: Path) -> Path:
    """Generate docker/requirements.txt and overwrite only when content changes."""
    docker_dir = deployments_path / DOCKER_DIR
    docker_dir.mkdir(parents=True, exist_ok=True)
    target = docker_dir / "requirements.txt"
    new_content = generate_docker_requirements_txt(deployments_path)

    if target.is_file() and target.read_text(encoding="utf-8") == new_content:
        pulumi.info("docker/requirements.txt is up to date")
        return target

    target.write_text(new_content, encoding="utf-8")
    pulumi.info("Generated docker/requirements.txt for workload image build")
    return target


def get_docker_bundle_files(
    deployments_path: Path,
    dockerfile_relative_path: str = DOCKERFILE_RELATIVE_PATH,
) -> list[tuple[str, str]]:
    """
    Files required for DockerfileProvided workload builds.

    ``dockerfile_relative_path`` is the catalog-relative path the artifact spec
    points the build at (``MCP_WORKLOAD_DOCKERFILE_PATH``). The same path locates
    the Dockerfile on disk and places it in the bundle, so a custom location is
    uploaded where the build looks for it.

    The catalog Dockerfile expects ``requirements.txt`` and ``start_server.sh`` at
    the bundle root, so those paths are included alongside it.
    """
    dockerfile_path = deployments_path / dockerfile_relative_path
    start_server_path = deployments_path / START_SERVER_SOURCE_RELATIVE_PATH

    if not dockerfile_path.is_file():
        message = (
            f"Workload DockerfileProvided build requires {dockerfile_relative_path} "
            f"under {deployments_path}"
        )
        pulumi.error(message)
        raise RuntimeError(message)
    if not start_server_path.is_file():
        message = (
            f"Workload DockerfileProvided build requires {START_SERVER_SOURCE_RELATIVE_PATH} "
            f"under {deployments_path}"
        )
        pulumi.error(message)
        raise RuntimeError(message)

    requirements_path = ensure_docker_requirements_txt(deployments_path)

    return [
        (str(dockerfile_path), dockerfile_relative_path),
        (str(requirements_path), ROOT_REQUIREMENTS_RELATIVE_PATH),
        (str(start_server_path), ROOT_START_SERVER_RELATIVE_PATH),
    ]


def merge_source_files(
    *file_groups: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Merge bundle entries, keeping the last occurrence for duplicate relative paths."""
    merged: dict[str, str] = {}
    for group in file_groups:
        for abs_path, rel_path in group:
            merged[rel_path] = abs_path
    return [(abs_path, rel_path) for rel_path, abs_path in sorted(merged.items())]


def get_workload_source_files(
    *,
    deployments_path: Path,
    dockerfile_relative_path: str | None,
    get_core_app_files: Callable[[], list[tuple[str, str]]],
) -> list[tuple[str, str]]:
    """Collect the Files catalog bundle for workload provisioning."""
    core_files = get_core_app_files()
    if dockerfile_relative_path is None:
        return core_files
    docker_files = get_docker_bundle_files(deployments_path, dockerfile_relative_path)
    return merge_source_files(core_files, docker_files)
