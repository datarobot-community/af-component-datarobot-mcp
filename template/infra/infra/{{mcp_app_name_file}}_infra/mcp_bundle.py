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

import fnmatch
from collections.abc import Callable
from pathlib import Path

import pulumi

DOCKERFILE_RELATIVE_PATH = "Dockerfile"
PYPROJECT_RELATIVE_PATH = "pyproject.toml"
UV_LOCK_RELATIVE_PATH = "uv.lock"
START_SERVER_RELATIVE_PATH = "start_server.sh"
DOCKER_BUILD_CONTEXT_FILES = (
    DOCKERFILE_RELATIVE_PATH,
    PYPROJECT_RELATIVE_PATH,
    UV_LOCK_RELATIVE_PATH,
    START_SERVER_RELATIVE_PATH,
)


def _read_dockerignore_patterns(dockerignore_path: Path) -> list[str]:
    if not dockerignore_path.is_file():
        return []
    patterns: list[str] = []
    for line in dockerignore_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def _matches_dockerignore(relative_path: str, patterns: list[str]) -> bool:
    """Approximate .dockerignore matching for pre-upload diagnostics."""
    basename = relative_path.rsplit("/", 1)[-1]
    for pattern in patterns:
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if relative_path == prefix or relative_path.startswith(f"{prefix}/"):
                return True
            continue
        if "/" in pattern:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
            continue
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(relative_path, pattern):
            return True
    return False


def log_docker_build_context(deployments_path: Path) -> None:
    """Log on-disk EE context before upload; .dockerignore is applied by the builder."""
    dockerignore_path = deployments_path / ".dockerignore"
    all_files = sorted(
        path.relative_to(deployments_path).as_posix()
        for path in deployments_path.rglob("*")
        if path.is_file()
    )
    patterns = _read_dockerignore_patterns(dockerignore_path)
    included = [path for path in all_files if not _matches_dockerignore(path, patterns)]
    app_on_disk = [path for path in all_files if path.startswith("app/")]
    app_in_estimate = [path for path in included if path.startswith("app/")]

    pulumi.info(
        "Docker EE build context on disk at "
        + str(deployments_path)
        + ": "
        + str(len(all_files))
        + " file(s) total"
    )
    pulumi.info(
        ".dockerignore present: "
        + str(dockerignore_path.is_file())
        + " ("
        + str(len(patterns))
        + " pattern(s)); estimated "
        + str(len(included))
        + " file(s) after ignore rules"
    )
    if app_on_disk:
        pulumi.info(
            "app/ on disk: "
            + str(len(app_on_disk))
            + " file(s); estimated included: "
            + str(len(app_in_estimate))
            + " — if included > 0, review .dockerignore"
        )
    sample = included[:25]
    if sample:
        pulumi.info("Estimated included files (sample): " + ", ".join(sample))
    pulumi.info(
        "Remote build logs also print dockerignore_probe lines from the Dockerfile "
        + "after COPY — compare app/ absent there for EE builds."
    )


def ensure_docker_build_context_files(deployments_path: Path) -> None:
    """Verify Docker build files exist at the app root.

    Custom execution-environment builds and workload DockerfileProvided builds
    both use the app root as context. Source files live here permanently —
    nothing is mirrored into a ``docker/`` subdirectory.
    """
    missing = [
        relative_path
        for relative_path in DOCKER_BUILD_CONTEXT_FILES
        if not (deployments_path / relative_path).is_file()
    ]
    if missing:
        message = (
            f"Docker build requires {', '.join(missing)} under {deployments_path}"
        )
        pulumi.error(message)
        raise RuntimeError(message)


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
    ``get_deployments_app_files`` -- and expects ``start_server.sh`` at the
    bundle root.
    """
    dockerfile_path = deployments_path / dockerfile_relative_path

    for required_path, relative_path in (
        (dockerfile_path, dockerfile_relative_path),
        (deployments_path / PYPROJECT_RELATIVE_PATH, PYPROJECT_RELATIVE_PATH),
        (deployments_path / UV_LOCK_RELATIVE_PATH, UV_LOCK_RELATIVE_PATH),
        (deployments_path / START_SERVER_RELATIVE_PATH, START_SERVER_RELATIVE_PATH),
    ):
        if not required_path.is_file():
            message = (
                f"Workload DockerfileProvided build requires {relative_path} "
                f"under {deployments_path}"
            )
            pulumi.error(message)
            raise RuntimeError(message)

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
