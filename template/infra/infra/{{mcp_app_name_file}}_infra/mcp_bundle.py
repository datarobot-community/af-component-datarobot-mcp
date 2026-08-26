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

from collections.abc import Callable
from pathlib import Path

import pulumi

DOCKER_DIR = "docker"
DOCKERFILE_RELATIVE_PATH = f"{DOCKER_DIR}/Dockerfile"
PYPROJECT_RELATIVE_PATH = "pyproject.toml"
UV_LOCK_RELATIVE_PATH = "uv.lock"
DOCKER_DEPENDENCY_FILENAMES = (PYPROJECT_RELATIVE_PATH, UV_LOCK_RELATIVE_PATH)


def ensure_docker_dependency_files(deployments_path: Path) -> None:
    """Mirror pyproject.toml/uv.lock into docker/, overwriting only on change.

    The Files Catalog bundle reads them straight from ``deployments_path``, so
    this isn't needed for the remote build -- it's for a local
    ``docker build`` run with ``docker/`` as the context. The mirrored copies
    are gitignored; ``deployments_path`` stays the source of truth.
    """
    docker_dir = deployments_path / DOCKER_DIR
    docker_dir.mkdir(parents=True, exist_ok=True)
    for filename in DOCKER_DEPENDENCY_FILENAMES:
        content = (deployments_path / filename).read_bytes()
        target = docker_dir / filename
        if not target.is_file() or target.read_bytes() != content:
            target.write_bytes(content)
            pulumi.info(f"Copied {filename} into docker/ for local image builds")


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

    The Dockerfile installs uv and runs ``uv sync --frozen`` against
    ``pyproject.toml``/``uv.lock`` at the bundle root -- already included via
    ``get_deployments_app_files`` -- so only their presence is checked here,
    to fail fast instead of erroring deep in the remote Docker build.
    """
    dockerfile_path = deployments_path / dockerfile_relative_path

    for required_path, relative_path in (
        (dockerfile_path, dockerfile_relative_path),
        (deployments_path / PYPROJECT_RELATIVE_PATH, PYPROJECT_RELATIVE_PATH),
        (deployments_path / UV_LOCK_RELATIVE_PATH, UV_LOCK_RELATIVE_PATH),
    ):
        if not required_path.is_file():
            message = (
                f"Workload DockerfileProvided build requires {relative_path} "
                f"under {deployments_path}"
            )
            pulumi.error(message)
            raise RuntimeError(message)

    ensure_docker_dependency_files(deployments_path)

    return [(str(dockerfile_path), dockerfile_relative_path)]


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
