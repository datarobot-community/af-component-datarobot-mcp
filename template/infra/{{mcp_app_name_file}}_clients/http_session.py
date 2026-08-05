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

"""Shared requests session with retries for DataRobot REST API clients."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Transient overload / gateway / server errors worth retrying.
DEFAULT_RETRY_STATUS_CODES: frozenset[int] = frozenset(
    {
        408,  # Request Timeout
        429,  # Too Many Requests (honours Retry-After when present)
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }
)

DEFAULT_RETRY_TOTAL = 5
DEFAULT_RETRY_BACKOFF_FACTOR = 1.0

# urllib3's default allowed methods omit POST; both Files and Workload APIs
# rely on POST for creates/build triggers/uploads.
RETRY_ALLOWED_METHODS = frozenset(
    {"DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT", "TRACE"}
)


def create_retry_adapter(
    *,
    total: int = DEFAULT_RETRY_TOTAL,
    backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    status_forcelist: frozenset[int] | None = None,
) -> HTTPAdapter:
    """Build an HTTPAdapter that retries transient connection and HTTP errors."""
    retry = Retry(
        total=total,
        connect=total,
        read=total,
        status=total,
        backoff_factor=backoff_factor,
        status_forcelist=tuple(status_forcelist or DEFAULT_RETRY_STATUS_CODES),
        allowed_methods=RETRY_ALLOWED_METHODS,
        raise_on_status=False,
    )
    return HTTPAdapter(max_retries=retry)


def create_datarobot_api_session(
    token: str,
    *,
    default_headers: dict[str, str] | None = None,
    retry_total: int = DEFAULT_RETRY_TOTAL,
    retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
) -> requests.Session:
    """Create a requests session authenticated for DataRobot API calls."""
    session = requests.Session()
    adapter = create_retry_adapter(
        total=retry_total,
        backoff_factor=retry_backoff_factor,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {"Authorization": f"Bearer {token}"}
    if default_headers:
        headers.update(default_headers)
    session.headers.update(headers)
    return session
