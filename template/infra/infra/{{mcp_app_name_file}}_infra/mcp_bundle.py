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
import string
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

CRLF = b"\r\n"
LF = b"\n"


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
        message = f"Docker build requires {', '.join(missing)} under {deployments_path}"
        pulumi.error(message)
        raise RuntimeError(message)


def normalize_shell_scripts(
    source_files: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Rewrite bundled ``*.sh`` files to LF line endings and return the bundle.

    These run under ``/bin/sh`` in a Linux container, where a trailing CR sticks
    to the last token of every line -- ``then<CR>`` stops being the ``then``
    keyword and the parser runs off the end of the file. Windows checkouts can
    leave CRLF on disk and the bundle is uploaded byte for byte, so normalize
    here, the last point we control. Idempotent, and rewriting in place keeps
    the paths Pulumi tracks stable.
    """
    for abs_path, rel_path in source_files:
        if not rel_path.endswith(".sh"):
            continue
        path = Path(abs_path)
        content = path.read_bytes()
        if CRLF not in content:
            continue
        path.write_bytes(content.replace(CRLF, LF))
        pulumi.info(f"Normalized CRLF line endings to LF in {rel_path}")
    return source_files


class FileBundler:
    def __init__(self, deployment_app_abs_path: Path, project_dir_abs_path: Path):
        self.deployment_app_abs_path = deployment_app_abs_path
        self.project_dir_abs_path = project_dir_abs_path
        self._safe_dir_name_chars = set(string.ascii_letters + string.digits + "_.-")

    @classmethod
    def resolve_dockerfile_relative_path(
        cls, deployment_app_abs_path: Path
    ) -> str | None:
        """
        Return a Dockerfile path relative to the app directory when using DockerfileProvided.

        ``MCP_WORKLOAD_DOCKERFILE_PATH`` overrides the default ``Dockerfile``
        check. Set ``MCP_WORKLOAD_DOCKERFILE_PATH=none`` (or ``false``/``0``) to force
        generated mode.
        """
        explicit = os.getenv("MCP_WORKLOAD_DOCKERFILE_PATH", "").strip()
        if explicit.lower() in {"none", "false", "0"}:
            return None
        if explicit:
            return explicit

        DEFAULT_DOCKERFILE_RELATIVE_PATH = "Dockerfile"
        default_path = deployment_app_abs_path / DEFAULT_DOCKERFILE_RELATIVE_PATH
        if default_path.is_file():
            return DEFAULT_DOCKERFILE_RELATIVE_PATH
        return None

    def _safe_dir_name(self, dir_name: str) -> str:
        return "".join(
            ch if ch in self._safe_dir_name_chars else "-" for ch in dir_name
        )

    def get_workload_build_dir_abs_path(
        self, build_dir_relative_path: Path | str, mcp_server_asset_name: str
    ) -> Path:
        build_dir_abs_path = (
            self.project_dir_abs_path
            / build_dir_relative_path
            / self._safe_dir_name(mcp_server_asset_name)
        )
        return build_dir_abs_path

    def setup_build_dir_for_workload_artifact_source_dir(
        self, build_dir_abs_path: Path, ignore_patterns: tuple[str, ...]
    ) -> Path:
        if build_dir_abs_path.exists():
            shutil.rmtree(build_dir_abs_path)

        shutil.copytree(
            self.deployment_app_abs_path,
            build_dir_abs_path,
            ignore=shutil.ignore_patterns(*ignore_patterns),
        )

        return build_dir_abs_path
