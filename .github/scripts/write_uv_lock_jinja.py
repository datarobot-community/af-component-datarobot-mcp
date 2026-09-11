#!/usr/bin/env python3
"""Copy a rendered uv.lock into uv.lock.jinja, preserving the copier package name placeholder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Default copier answers use mcp_app_name=mcp_server → hyphenated root package in the lock.
DEFAULT_RENDERED_PACKAGE_NAME = "mcp-server"
JINJA_NAME_LINE = 'name = "{{ mcp_app_name | replace("_", "-") }}"'


def apply_jinja_package_name(content: str, rendered_package_name: str) -> str:
    old = f'name = "{rendered_package_name}"'
    if old not in content:
        raise ValueError(f"expected rendered lock to contain {old!r} exactly once")
    return content.replace(old, JINJA_NAME_LINE, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rendered_lock", type=Path, help="Path to rendered uv.lock")
    parser.add_argument(
        "template_lock_jinja",
        type=Path,
        help="Path to template/{{mcp_app_name_file}}/uv.lock.jinja",
    )
    parser.add_argument(
        "--rendered-package-name",
        default=DEFAULT_RENDERED_PACKAGE_NAME,
        help="Root [[package]] name from a default copier render",
    )
    args = parser.parse_args()

    try:
        content = apply_jinja_package_name(
            args.rendered_lock.read_text(encoding="utf-8"),
            args.rendered_package_name,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.template_lock_jinja.write_text(content, encoding="utf-8")
    written = args.template_lock_jinja.read_text(encoding="utf-8")
    if JINJA_NAME_LINE not in written:
        print(
            "error: uv.lock.jinja is missing the copier package name placeholder",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
