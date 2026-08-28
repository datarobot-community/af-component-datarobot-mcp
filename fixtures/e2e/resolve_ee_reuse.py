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
"""Skip the remote EE image build when the docker context is unchanged.

The shared CI execution environment (stable name, see use-cases.yaml) stores a
``context-hash=<sha>`` marker in its description. ``resolve`` prints the EE id
when the stored hash matches the current docker context and the latest version
built successfully — the caller then deploys via
``DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT=<id>`` (no build). ``mark``
stamps the description after a successful build so the next run can reuse it.

stdlib only (urllib) so it runs with the container's bare python3. Failures are
non-fatal by design: on any API error the caller just falls back to building.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HASH_MARKER = "context-hash="


def _api_request(method: str, url: str, payload: dict | None = None) -> dict:
    token = os.environ["DATAROBOT_API_TOKEN"]
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body.strip() else {}


def _find_execution_environment(endpoint: str, name: str) -> dict | None:
    query = urllib.parse.urlencode({"searchFor": name})
    url = f"{endpoint.rstrip('/')}/executionEnvironments/?{query}"
    listing = _api_request("GET", url)
    matches = [
        entity for entity in listing.get("data", []) if entity.get("name") == name
    ]
    return matches[0] if matches else None


def cmd_resolve(endpoint: str, name: str, context_hash: str) -> int:
    entity = _find_execution_environment(endpoint, name)
    if entity is None:
        return 0
    description = entity.get("description") or ""
    if f"{HASH_MARKER}{context_hash}" not in description:
        return 0
    latest_version = entity.get("latestVersion") or {}
    if latest_version.get("buildStatus") != "success":
        print(
            f"EE {entity['id']} matches {HASH_MARKER}{context_hash} but its latest "
            f"version buildStatus is {latest_version.get('buildStatus')!r}; rebuilding",
            file=sys.stderr,
        )
        return 0
    print(entity["id"])
    return 0


def cmd_mark(endpoint: str, name: str, context_hash: str) -> int:
    entity = _find_execution_environment(endpoint, name)
    if entity is None:
        print(f"No execution environment named {name!r} to mark", file=sys.stderr)
        return 0
    url = f"{endpoint.rstrip('/')}/executionEnvironments/{entity['id']}/"
    _api_request(
        "PATCH",
        url,
        {"description": f"CI shared EE for MCP server ({HASH_MARKER}{context_hash})"},
    )
    print(f"Marked EE {entity['id']} with {HASH_MARKER}{context_hash}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("resolve", "mark"))
    parser.add_argument("--name", required=True)
    parser.add_argument("--context-hash", required=True)
    args = parser.parse_args()

    endpoint = os.environ.get("DATAROBOT_ENDPOINT", "").strip()
    if not endpoint or not os.environ.get("DATAROBOT_API_TOKEN"):
        print("DATAROBOT_ENDPOINT/DATAROBOT_API_TOKEN not set", file=sys.stderr)
        return 0

    try:
        if args.command == "resolve":
            return cmd_resolve(endpoint, args.name, args.context_hash)
        return cmd_mark(endpoint, args.name, args.context_hash)
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        # Reuse is an optimization: never fail the deploy over it.
        print(
            f"EE reuse lookup failed ({exc!r}); falling back to build", file=sys.stderr
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
