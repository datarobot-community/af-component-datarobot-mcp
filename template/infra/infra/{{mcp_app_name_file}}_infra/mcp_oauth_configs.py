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

"""OAuth metadata and well-known route configuration for MCP deployment and workload.

Everything here is configured from environment variables, so the same project
deploys to several DataRobot environments without editing a file in between: the
values that differ per environment (trusted issuer, audiences, token URL) come
from that environment's ``.env`` or CI secrets.

The settings are forwarded to the server unchanged — as runtime parameters on
the deployment path, container env vars on the workload path. The server
assembles the document it publishes at ``/.well-known/oauth-protected-resource``
from them; nothing here builds or parses that document.
"""

from __future__ import annotations

import os
from typing import Any

OAUTH_PROTECTED_RESOURCE_WELL_KNOWN_PATH = "/.well-known/oauth-protected-resource"

ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE_ENV_VAR = (
    "MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE"
)

RESOURCE_ENV_VAR = "MCP_OAUTH_RESOURCE"
AUTHORIZATION_SERVERS_ENV_VAR = "MCP_OAUTH_AUTHORIZATION_SERVERS"
SCOPES_SUPPORTED_ENV_VAR = "MCP_OAUTH_SCOPES_SUPPORTED"

XAA_TRUSTED_ISSUER_ENV_VAR = "MCP_XAA_TRUSTED_ISSUER"
XAA_EXCHANGE_AUDIENCE_ENV_VAR = "MCP_XAA_EXCHANGE_AUDIENCE"
XAA_TOKEN_URL_ENV_VAR = "MCP_XAA_TOKEN_URL"
XAA_TOKEN_AUDIENCE_ENV_VAR = "MCP_XAA_TOKEN_AUDIENCE"
XAA_SCOPES_ENV_VAR = "MCP_XAA_SCOPES"
XAA_TOKEN_ENDPOINT_AUTH_METHOD_ENV_VAR = "MCP_XAA_TOKEN_ENDPOINT_AUTH_METHOD"

# Every protected-resource metadata setting the server reads, in the order they
# appear in .env.template. Only the ones that are set are forwarded.
OAUTH_METADATA_ENV_VARS = (
    RESOURCE_ENV_VAR,
    AUTHORIZATION_SERVERS_ENV_VAR,
    SCOPES_SUPPORTED_ENV_VAR,
    XAA_TRUSTED_ISSUER_ENV_VAR,
    XAA_EXCHANGE_AUDIENCE_ENV_VAR,
    XAA_TOKEN_URL_ENV_VAR,
    XAA_TOKEN_AUDIENCE_ENV_VAR,
    XAA_SCOPES_ENV_VAR,
    XAA_TOKEN_ENDPOINT_AUTH_METHOD_ENV_VAR,
)

# Cross-Application Access is all-or-nothing: the server needs every one of these
# to publish the block at all.
XAA_REQUIRED_ENV_VARS = (
    XAA_TRUSTED_ISSUER_ENV_VAR,
    XAA_EXCHANGE_AUDIENCE_ENV_VAR,
    XAA_TOKEN_URL_ENV_VAR,
    XAA_SCOPES_ENV_VAR,
)

# Accepted spellings of "on" for the well-known route flag.
TRUTHY_VALUES = frozenset({"true", "1", "yes", "on"})


def coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_VALUES
    return bool(value)


def _env(name: str) -> str | None:
    """Read ``name``, treating blank and unset alike."""
    return os.getenv(name, "").strip() or None


def validate_cross_application_access_env() -> None:
    """Fail the deployment on a half-configured Cross-Application Access block.

    The server drops a partial block with a warning nobody reads, and published
    metadata that quietly omits ``cross_application_access`` looks identical to
    metadata that never asked for it — the agent-side failure then shows up much
    later, far from its cause.
    """
    present = [name for name in XAA_REQUIRED_ENV_VARS if _env(name)]
    if not present:
        return
    missing = [name for name in XAA_REQUIRED_ENV_VARS if not _env(name)]
    if missing:
        raise ValueError(
            "Incomplete MCP Cross-Application Access configuration: "
            f"{', '.join(missing)} is not set. Set every MCP_XAA_* variable, or "
            "unset them all to publish no cross_application_access block."
        )


def mcp_oauth_metadata_env_vars() -> list[dict[str, str]]:
    """The metadata settings that are configured, ready to forward."""
    validate_cross_application_access_env()
    env_vars = []
    for name in OAUTH_METADATA_ENV_VARS:
        value = _env(name)
        if value:
            env_vars.append({"name": name, "value": value})
    return env_vars


def mcp_enable_unauthenticated_well_known_route_value() -> str:
    """Resolve the well-known route flag, normalized to ``"true"`` / ``"false"``.

    This is a server-behaviour switch, not a metadata field, so it lives only in
    ``MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE`` and is never published in the
    document. Agents fetch the well-known route before they hold a token, so XAA
    discovery needs it enabled — and the cluster must permit unauthenticated
    access as well. Both are required: with the flag on but no platform-level
    opt-in, anonymous requests never reach the server.
    """
    enabled = coerce_bool(os.getenv(ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE_ENV_VAR))
    return str(enabled).lower()


def oauth_protected_resource_well_known_route_auth() -> str:
    if mcp_enable_unauthenticated_well_known_route_value() == "true":
        return "disabled"
    return "required"


def workload_default_mcp_oauth_routes() -> list[dict[str, str]]:
    """Workload artifact routes for OAuth protected resource metadata."""
    return [
        {
            "path": OAUTH_PROTECTED_RESOURCE_WELL_KNOWN_PATH,
            "auth": oauth_protected_resource_well_known_route_auth(),
        },
    ]


def get_workload_mcp_oauth_routes() -> list[dict[str, str]] | None:
    if mcp_enable_unauthenticated_well_known_route_value() == "true":
        return workload_default_mcp_oauth_routes()
    return None


def oauth_and_well_known_env_vars() -> list[dict[str, str]]:
    """Container env vars for MCP OAuth metadata and well-known route settings."""
    return [
        {
            "name": ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE_ENV_VAR,
            "value": mcp_enable_unauthenticated_well_known_route_value(),
        },
        *mcp_oauth_metadata_env_vars(),
    ]
