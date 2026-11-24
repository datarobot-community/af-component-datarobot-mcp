#!/usr/bin/env python3
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
"""Copier migration: carry user runtime parameters into ``<app>_infra/user_params.py``.

Older versions kept them in ``infra/infra/<app>_user_params.py``. That file is no
longer in the template, and ``copier update`` deletes it, edits included. So:

* ``before`` the update, copy it aside (with its import made relative), and
* ``after`` the update, write that copy over the template's default
  ``user_params.py`` and remove the old file if it survived.

Runs on every update and does nothing once the old file is gone, so it needs no
version pin. Run from the project root:
``move_user_params.py <answers file> before|after``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def paths(app: str) -> tuple[Path, Path, Path]:
    infra = Path("infra") / "infra"
    legacy = infra / f"{app}_user_params.py"
    target = infra / f"{app}_infra" / "user_params.py"
    pending = infra / f"{app}_infra" / "user_params.py.migrating"
    return legacy, target, pending


def before(app: str) -> None:
    legacy, _target, pending = paths(app)
    if not legacy.exists():
        return
    text = legacy.read_text(encoding="utf-8").replace(
        f"from infra.{app}_infra.mcp_utils import", "from .mcp_utils import"
    )
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text(text, encoding="utf-8")


def after(app: str) -> None:
    legacy, target, pending = paths(app)
    if pending.exists():
        target.write_text(pending.read_text(encoding="utf-8"), encoding="utf-8")
        pending.unlink()
        print(f"Moved your runtime parameters from {legacy} to {target}.")
    if legacy.exists() and target.exists():
        legacy.unlink()


def app_name(answers_file: Path) -> str:
    """``mcp_app_name`` from this instance's answers file (copier writes it plainly)."""
    text = answers_file.read_text(encoding="utf-8")
    match = re.search(r"^mcp_app_name:\s*['\"]?([A-Za-z0-9_]+)", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"mcp_app_name not found in {answers_file}")
    return match.group(1)


def main() -> int:
    answers_file, stage = Path(sys.argv[1]), sys.argv[2]
    if not answers_file.exists():
        return 0  # first copy, nothing to migrate
    app = app_name(answers_file)
    {"before": before, "after": after}[stage](app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
