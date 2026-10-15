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
"""Delete old versions of the shared CI execution environment before a rebuild.

Every docker-context change builds a new version on the shared EE (stable name,
see use-cases.yaml). DataRobot caps non-failed versions per environment (30), so
without pruning the serverless-docker E2E eventually fails with
``409 Number of environment build versions should be less than 30``.

Keeps the newest ``--keep`` successfully built versions and deletes the rest.
Versions that are building, or failed (failed builds do not count toward the
cap), are never touched. A version still used by a model or deployment is
refused by the API with 409; that is logged and skipped.

stdlib only (urllib) so it runs with the container's bare python3. Failures are
non-fatal by design: pruning is housekeeping, the deploy decides pass or fail.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PAGE_SIZE = 100


def _api_request(method: str, url: str) -> dict:
    token = os.environ["DATAROBOT_API_TOKEN"]
    request = urllib.request.Request(url, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body.strip() else {}


def _find_execution_environment(endpoint: str, name: str) -> dict | None:
    query = urllib.parse.urlencode({"searchFor": name})
    listing = _api_request("GET", f"{endpoint}/executionEnvironments/?{query}")
    matches = [e for e in listing.get("data", []) if e.get("name") == name]
    return matches[0] if matches else None


def _list_versions(endpoint: str, environment_id: str) -> list[dict]:
    """All versions, newest first (the API sorts by creation time descending)."""
    versions: list[dict] = []
    while True:
        query = urllib.parse.urlencode({"offset": len(versions), "limit": PAGE_SIZE})
        url = f"{endpoint}/executionEnvironments/{environment_id}/versions/?{query}"
        page = _api_request("GET", url).get("data", [])
        versions.extend(page)
        if len(page) < PAGE_SIZE:
            return versions


def prune(endpoint: str, name: str, keep: int) -> int:
    environment = _find_execution_environment(endpoint, name)
    if environment is None:
        print(f"No execution environment named {name!r}; nothing to prune", file=sys.stderr)
        return 0
    versions = _list_versions(endpoint, environment["id"])
    built = [v for v in versions if v.get("buildStatus") == "success"]
    print(
        f"EE {environment['id']} has {len(versions)} versions, {len(built)} built; "
        f"keeping the newest {keep}",
        file=sys.stderr,
    )
    for version in built[keep:]:
        url = (
            f"{endpoint}/executionEnvironments/{environment['id']}"
            f"/versions/{version['id']}/"
        )
        try:
            _api_request("DELETE", url)
            print(f"Deleted version {version['id']}", file=sys.stderr)
        except urllib.error.HTTPError as exc:
            print(f"Kept version {version['id']}: HTTP {exc.code}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--keep", type=int, default=10)
    args = parser.parse_args()

    endpoint = os.environ.get("DATAROBOT_ENDPOINT", "").strip().rstrip("/")
    if not endpoint or not os.environ.get("DATAROBOT_API_TOKEN"):
        print("DATAROBOT_ENDPOINT/DATAROBOT_API_TOKEN not set", file=sys.stderr)
        return 0

    try:
        return prune(endpoint, args.name, args.keep)
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        print(f"EE version pruning failed ({exc!r}); continuing", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
