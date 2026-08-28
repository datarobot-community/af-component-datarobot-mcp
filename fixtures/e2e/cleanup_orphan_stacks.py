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
"""Sweep DataRobot resources leaked by deploy E2E runs whose destroy no-oped.

Deletes, in dependency order (deployments block custom/registered model
deletion): deployments -> registered models -> custom models -> prediction
environments -> use cases. Resources are matched by the run-scoped naming
convention (``[ci-e2e-`` in the name/label); use cases are matched by the CI
description from fixtures/e2e/infra/infra/__init__.py. The shared execution
environment (ci-e2e-mcp-server-docker-ee) is intentionally left alone — it is
reused across runs via the context-hash mechanism.

Dry-run by default; pass --delete to actually delete. Run when no deploy E2E
workflow is in progress, or you may delete a live run's resources.

Usage:
    export DATAROBOT_API_TOKEN=... DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2
    python3 fixtures/e2e/cleanup_orphan_stacks.py            # list what would go
    python3 fixtures/e2e/cleanup_orphan_stacks.py --delete   # actually delete
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CI_NAME_MARKER = "[ci-e2e-"
CI_USE_CASE_DESCRIPTION = "CI E2E deployment test for DataRobot MCP Server."

# (route, display-name field, extra predicate) in deletion order.
RESOURCE_KINDS = (
    ("deployments", "label", None),
    ("registeredModels", "name", None),
    ("customModels", "name", None),
    ("predictionEnvironments", "name", None),
    (
        "useCases",
        "name",
        lambda entity: entity.get("description") == CI_USE_CASE_DESCRIPTION,
    ),
)


def _request(method: str, url: str) -> tuple[int, dict]:
    request = urllib.request.Request(url, method=method)
    request.add_header("Authorization", f"Bearer {os.environ['DATAROBOT_API_TOKEN']}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode("utf-8", "replace")}


def _list_all(endpoint: str, route: str) -> list[dict]:
    entities: list[dict] = []
    url: str | None = f"{endpoint}/{route}/?{urllib.parse.urlencode({'limit': 100})}"
    while url:
        status, payload = _request("GET", url)
        if status != 200:
            print(f"  WARNING: GET {route} returned HTTP {status}: {payload}")
            break
        entities.extend(payload.get("data", []))
        url = payload.get("next")
    return entities


def sweep(endpoint: str, marker: str, delete: bool) -> int:
    leaked_total = 0
    failed = 0
    for route, name_field, predicate in RESOURCE_KINDS:
        matches = [
            entity
            for entity in _list_all(endpoint, route)
            if marker in (entity.get(name_field) or "")
            or (predicate is not None and predicate(entity))
        ]
        print(f"{route}: {len(matches)} leaked")
        leaked_total += len(matches)
        for entity in matches:
            label = entity.get(name_field) or entity["id"]
            if not delete:
                print(f"  would delete {entity['id']}  {label}")
                continue
            status, payload = _request("DELETE", f"{endpoint}/{route}/{entity['id']}/")
            if status in (200, 202, 204):
                print(f"  deleted {entity['id']}  {label}")
            else:
                failed += 1
                print(
                    f"  WARNING: DELETE {route}/{entity['id']} ({label}) "
                    f"returned HTTP {status}: {payload}"
                )
    print(
        "\nNote: per-run ApiTokenCredentials named "
        "'... Session Secret Key' are not run-scoped and are left alone; "
        "the shared EE ci-e2e-mcp-server-docker-ee is kept on purpose."
    )
    if not delete and leaked_total:
        print(
            f"\nDry run only — re-run with --delete to remove {leaked_total} resources."
        )
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete (default is a dry-run listing)",
    )
    parser.add_argument("--marker", default=CI_NAME_MARKER)
    args = parser.parse_args()

    endpoint = os.environ.get("DATAROBOT_ENDPOINT", "").strip().rstrip("/")
    if not endpoint or not os.environ.get("DATAROBOT_API_TOKEN"):
        print(
            "DATAROBOT_ENDPOINT and DATAROBOT_API_TOKEN are required",
            file=sys.stderr,
        )
        return 2
    if not endpoint.endswith("/api/v2"):
        endpoint = f"{endpoint}/api/v2"

    return sweep(endpoint, args.marker, args.delete)


if __name__ == "__main__":
    raise SystemExit(main())
