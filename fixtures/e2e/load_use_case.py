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
"""Load a deployment E2E use case and emit GitHub Actions environment lines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - CI installs pyyaml via uvx
    raise SystemExit(
        "PyYAML is required. Run with: uvx --with pyyaml python load_use_case.py ..."
    ) from exc

ENV_KEYS = (
    "MCP_DEPLOYMENT_TYPE",
    "MCP_WORKLOAD_DOCKERFILE_PATH",
    "DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT",
    "DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT_VERSION_ID",
)


def emit_github_env(key: str, value: str) -> None:
    """Write a line (or heredoc block) safe for appending to GITHUB_ENV."""
    if any(ch in value for ch in " \n\r[]:#"):
        delimiter = f"{key}_EOF"
        print(f"{key}<<{delimiter}")
        print(value)
        print(delimiter)
    else:
        print(f"{key}={value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("use_case_id", help="Key under use_cases in use-cases.yaml")
    parser.add_argument(
        "--use-cases-file",
        type=Path,
        default=Path(__file__).with_name("use-cases.yaml"),
    )
    args = parser.parse_args()

    data = yaml.safe_load(args.use_cases_file.read_text(encoding="utf-8"))
    use_cases = data.get("use_cases", {})
    if args.use_case_id not in use_cases:
        known = ", ".join(sorted(use_cases))
        print(
            f"Unknown use case '{args.use_case_id}'. Known cases: {known}",
            file=sys.stderr,
        )
        return 1

    case = use_cases[args.use_case_id]
    env = case.get("env", {})

    emit_github_env("CASE_NAME", args.use_case_id)
    for key in ENV_KEYS:
        emit_github_env(key, env.get(key, ""))

    description = case.get("description", "")
    if description:
        emit_github_env("USE_CASE_DESCRIPTION", description)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
