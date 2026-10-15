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

The CI token cannot delete versions, so instead of pruning this walks the names
``<name>``, ``<name>-2``, ``<name>-3``, ... and picks the first one that does not
exist yet or is under the cap (failed builds do not count toward it). When
``<name>`` is full it emits a warning to clean it up by hand. After that clean-up
``<name>`` is under the cap again and is picked again, so the base name comes
back on its own.

Prints the execution environment name to use on stdout (and nothing else); all
logging goes to stderr. stdlib only (urllib) so it runs with the container's
bare python3. Failures are non-fatal by design: the name is returned unchanged
and the deploy decides pass or fail.
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


def choose_name(endpoint: str, name: str, cap: int) -> str:
    _log(f"endpoint={endpoint} caller={_describe_caller(endpoint)}")
    for suffix in range(1, 100):
        candidate = name if suffix == 1 else f"{name}-{suffix}"
        environment = _find_execution_environment(endpoint, candidate)
        if environment is None:
            _log(f"{candidate!r} does not exist yet; the build will create it")
            chosen = candidate
            break
        versions = _list_versions(endpoint, environment["id"])
        counts: dict[str, int] = {}
        for version in versions:
            status = str(version.get("buildStatus"))
            counts[status] = counts.get(status, 0) + 1
        _log(
            f"{candidate!r} (EE {environment['id']}): {_counted(versions)} of {cap} "
            f"versions count toward the cap, by build status {counts}"
        )
        if versions:
            _log(f"  newest: {_describe_version(versions[0])}")
        if _counted(versions) < cap:
            chosen = candidate
            break
    else:
        _log(f"no free name found up to {name}-99; keeping {name!r}")
        return name
    if chosen != name:
        _log(
            f"::warning title=CI execution environment at the version cap::"
            f"{name!r} is full ({cap} versions). Using {chosen!r} instead. Delete old "
            f"versions of {name!r} in DataRobot; once it is under {cap} again, "
            f"{name!r} is used again."
        )
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--cap", type=int, default=30, help="DataRobot per-EE version cap")
    args = parser.parse_args()

    endpoint = os.environ.get("DATAROBOT_ENDPOINT", "").strip().rstrip("/")
    if not endpoint or not os.environ.get("DATAROBOT_API_TOKEN"):
        _log("DATAROBOT_ENDPOINT/DATAROBOT_API_TOKEN not set")
        print(args.name)
        return 0

    try:
        print(choose_name(endpoint, args.name, args.cap))
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        _log(f"EE name check failed ({exc!r}); continuing with {args.name!r}")
        print(args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
