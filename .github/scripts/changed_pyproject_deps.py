#!/usr/bin/env python3
"""Print normalized PyPI names of dependencies touched in a unified git diff."""

from __future__ import annotations

import re
import sys

# PEP 508 name before extras or version operators.
_NAME = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


def _package_from_requirement_line(text: str) -> str | None:
    text = text.strip().strip(",").strip().strip('"').strip("'")
    if not text or text.startswith("#"):
        return None
    if not any(token in text for token in (">=", "==", "!=", "<=", "~=", ">", "<", "[")):
        return None
    match = _NAME.match(text)
    if not match:
        return None
    return match.group(1).lower().replace("_", "-")


def packages_in_diff(diff: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for line in diff.splitlines():
        if not line or line.startswith(("+++", "---", "@@")):
            continue
        if not line.startswith(("+", "-")):
            continue
        body = line[1:].strip()
        if not body:
            continue
        pkg = _package_from_requirement_line(body)
        if pkg and pkg not in seen:
            seen.add(pkg)
            ordered.append(pkg)
    return ordered


def main() -> int:
    diff = sys.stdin.read()
    for pkg in packages_in_diff(diff):
        print(pkg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
