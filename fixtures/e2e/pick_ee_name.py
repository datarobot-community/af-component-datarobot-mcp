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
"""Pick the shared CI execution environment name that still has room for a build.

Every docker-context change builds a new version on the shared EE (stable name,
see use-cases.yaml). DataRobot caps non-failed versions per environment (30), so
without housekeeping the serverless-docker E2E eventually fails with
``409 Number of environment build versions should be less than 30``.

The CI token cannot delete versions, so instead of pruning this works with a
family of names: ``<name>``, ``<name>-2``, ``<name>-3``, ... Reusing an image
creates no version, so reuse is decided first and ignores the cap; only a build
needs room.

1. Reuse: if ``--context-hash`` is given and any EE in the family carries it in
   its description (see resolve_ee_reuse.py) with a successful latest version,
   use it. The highest-numbered match wins. The caller then skips the build.
2. Build: otherwise use the highest-numbered existing EE while it is under the
   cap (failed builds do not count toward it). If it is full, use the next
   number above it, which the build creates. Names only ever move up and gaps
   are never filled, so the latest build is always on the highest name and the
   reuse check above finds it. With no EE at all, the base name is used.

Whenever an existing EE is at the cap it emits a warning. Old, full EEs can be
cleaned up or deleted by hand; that does not change which name is picked.

Prints the execution environment name to use on stdout (and nothing else); all
logging goes to stderr. stdlib only (urllib) so it runs with the container's
bare python3. Failures are non-fatal by design: the name is returned unchanged
and the deploy decides pass or fail.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

PAGE_SIZE = 100
# Keep in sync with HASH_MARKER in resolve_ee_reuse.py.
HASH_MARKER = "context-hash="


def _api_request(method: str, url: str) -> dict:
    token = os.environ["DATAROBOT_API_TOKEN"]
    request = urllib.request.Request(url, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body.strip() else {}


def _find_family(endpoint: str, name: str) -> dict[int, dict]:
    """Existing EEs named ``<name>`` (key 1) or ``<name>-<n>`` (key n)."""
    query = urllib.parse.urlencode({"searchFor": name})
    listing = _api_request("GET", f"{endpoint}/executionEnvironments/?{query}")
    pattern = re.compile(rf"^{re.escape(name)}(?:-(\d+))?$")
    family: dict[int, dict] = {}
    for entity in listing.get("data", []):
        match = pattern.match(entity.get("name") or "")
        if match:
            family[int(match.group(1) or 1)] = entity
    return family


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


def _log(message: str) -> None:
    print(f"[pick-ee] {message}", file=sys.stderr)


def _describe_caller(endpoint: str) -> str:
    """Who the token belongs to; handy when comparing with the EE owner in the UI."""
    try:
        info = _api_request("GET", f"{endpoint}/account/info/")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return f"unknown ({exc!r})"
    return f"{info.get('username') or info.get('uid')} (uid {info.get('uid')})"


def _describe_version(version: dict) -> str:
    return (
        f"{version['id']} created={version.get('created')} "
        f"status={version.get('buildStatus')} label={version.get('label')!r}"
    )


def _counted(versions: list[dict]) -> int:
    """Versions that count toward the cap (everything except failed builds)."""
    return sum(1 for v in versions if v.get("buildStatus") != "failed")


def _candidate(name: str, suffix: int) -> str:
    return name if suffix == 1 else f"{name}-{suffix}"


def choose_name(endpoint: str, name: str, cap: int, context_hash: str) -> str:
    _log(f"endpoint={endpoint} caller={_describe_caller(endpoint)}")
    family = _find_family(endpoint, name)
    used: dict[int, int] = {}
    for suffix in sorted(family):
        environment = family[suffix]
        versions = _list_versions(endpoint, environment["id"])
        used[suffix] = _counted(versions)
        statuses: dict[str, int] = {}
        for version in versions:
            key = str(version.get("buildStatus"))
            statuses[key] = statuses.get(key, 0) + 1
        _log(
            f"{_candidate(name, suffix)!r} (EE {environment['id']}): {used[suffix]} of "
            f"{cap} versions count toward the cap, by build status {statuses}; "
            f"description={environment.get('description')!r}"
        )
        if versions:
            _log(f"  newest: {_describe_version(versions[0])}")

    reusable = [
        suffix
        for suffix, environment in family.items()
        if context_hash
        and f"{HASH_MARKER}{context_hash}" in (environment.get("description") or "")
        and (environment.get("latestVersion") or {}).get("buildStatus") == "success"
    ]
    if reusable:
        chosen = _candidate(name, max(reusable))
        _log(f"{chosen!r} already holds the image for context-hash {context_hash}; reusing it")
        return chosen

    if not used:
        chosen = name
        _log(f"no execution environment named {name!r} yet; the build will create it")
    elif used[max(used)] < cap:
        chosen = _candidate(name, max(used))
        _log(f"using the latest EE {chosen!r}")
    else:
        chosen = _candidate(name, max(used) + 1)
        _log(f"the latest EE is full; the build will create {chosen!r}")

    full = [_candidate(name, n) for n, count in sorted(used.items()) if count >= cap]
    if full:
        _log(
            f"::warning title=CI execution environment at the version cap::"
            f"{', '.join(full)} reached {cap} versions. Using {chosen!r}. Old, full "
            f"execution environments can be cleaned up or deleted in DataRobot."
        )
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--context-hash", default="", help="Docker context hash to look for")
    parser.add_argument("--cap", type=int, default=30, help="DataRobot per-EE version cap")
    args = parser.parse_args()

    endpoint = os.environ.get("DATAROBOT_ENDPOINT", "").strip().rstrip("/")
    if not endpoint or not os.environ.get("DATAROBOT_API_TOKEN"):
        _log("DATAROBOT_ENDPOINT/DATAROBOT_API_TOKEN not set")
        print(args.name)
        return 0

    try:
        print(choose_name(endpoint, args.name, args.cap, args.context_hash))
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        _log(f"EE name check failed ({exc!r}); continuing with {args.name!r}")
        print(args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
