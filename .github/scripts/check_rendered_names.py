#!/usr/bin/env python3
"""Fail if a rendered project still names another app, or carries an unfilled copier blank.

Render the component under a name other than the recipe's (`dr_mcp`) and run this on
the output. Plain template files are copied byte for byte, so a `dr_mcp` typed into
one of them shows up here, and so does a `{{ mcp_app_name }}` in a file that lost its
`.jinja` suffix.

Legitimate names that only contain the substring (`dr_mcp_tool`,
`get_dr_mcp_server_instance`, `DR_MCP_SERVER_URL`) do not match: `_` is a word
character, so there is no word boundary inside them.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RECIPE_NAME = re.compile(r"\bdr[_-]mcp(_infra|_clients|_user_params|_features)?\b")
# Copier's own variables. Task (`{{.UV_CMD}}`) and GitHub (`${{ matrix.x }}`) also use
# braces, so only blanks naming a copier question count.
COPIER_BLANK = re.compile(
    r"\{\{-?\s*(mcp_app_name|mcp_app_name_file|mcp_development_port|copyright_year|_copier\w*)\b"
    r"|\{%-?\s*(raw|endraw|if|for)\b"
)
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}


def problems(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if SKIP_DIRS.intersection(rel.parts):
            continue
        for pattern, what in (
            (RECIPE_NAME, "recipe app name"),
            (COPIER_BLANK, "copier blank"),
        ):
            if pattern.search(str(rel)):
                found.append(f"{rel}: {what} in path")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for pattern, what in (
                (RECIPE_NAME, "recipe app name"),
                (COPIER_BLANK, "copier blank"),
            ):
                if pattern.search(line):
                    found.append(f"{rel}:{number}: {what}: {line.strip()[:120]}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rendered_dir", type=Path, help="Output of a copier render")
    args = parser.parse_args()

    found = problems(args.rendered_dir)
    for line in found:
        print(line)
    if found:
        print(f"error: {len(found)} problem(s) in {args.rendered_dir}", file=sys.stderr)
        return 1
    print(f"ok: no recipe app name or copier blank in {args.rendered_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
