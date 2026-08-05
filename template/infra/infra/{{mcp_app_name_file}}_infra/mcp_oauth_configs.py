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

"""OAuth metadata and well-known route configuration for MCP deployment and workload."""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError

from .. import project_dir

logger = logging.getLogger(__name__)

OAUTH_PROTECTED_RESOURCE_WELL_KNOWN_PATH = "/.well-known/oauth-protected-resource"


class BaseDataClass:
    def to_dict_without_null_attribute(self) -> dict[str, Any]:
        return asdict(
            self,  # type: ignore[call-overload]  # pyright: ignore[reportArgumentType]
            dict_factory=lambda x: {k: v for k, v in x if v is not None},
        )

    def to_yaml_string(self) -> str:
        return yaml.safe_dump(self.to_dict_without_null_attribute())


@dataclass
class XAATokenExchangeParams(BaseDataClass):
    trusted_issuer: str
    audience: str

    @classmethod
    def from_dict(cls, dict_input: dict[str, str]) -> XAATokenExchangeParams:
        return cls(dict_input["trusted_issuer"], dict_input["audience"])


@dataclass
class XAATokenRequestParams(BaseDataClass):
    token_url: str
    # audience can be None if it is not setup for AuthN & AuthZ check (as resource) in IdP.
    audience: str | None
    scopes: list[str]

    @classmethod
    def from_dict(cls, dict_input: dict[str, Any]) -> XAATokenRequestParams:
        return cls(
            dict_input["token_url"], dict_input.get("audience"), dict_input["scopes"]
        )


@dataclass
class XAAMetadata(BaseDataClass):
    token_endpoint_auth_method: str
    token_exchange: XAATokenExchangeParams
    token_request: XAATokenRequestParams

    @classmethod
    def from_dict(cls, metadata_in_dict: dict[str, Any]) -> XAAMetadata:
        return cls(
            metadata_in_dict["token_endpoint_auth_method"],
            XAATokenExchangeParams.from_dict(metadata_in_dict["token_exchange"]),
            XAATokenRequestParams.from_dict(metadata_in_dict["token_request"]),
        )


@dataclass
class MCPOAuthProtectedResourceMetadataConfig(BaseDataClass):
    resource: str
    authorization_servers: list[str]
    scopes_supported: list[str]
    xaa_metadata: XAAMetadata | None

    @classmethod
    def from_dict(
        cls, metadata_in_dict: dict[str, Any]
    ) -> MCPOAuthProtectedResourceMetadataConfig:
        xaa_metadata = (
            XAAMetadata.from_dict(metadata_in_dict["xaa_metadata"])
            if metadata_in_dict.get("xaa_metadata")
            else None
        )
        return cls(
            metadata_in_dict["resource"],
            metadata_in_dict["authorization_servers"],
            metadata_in_dict["scopes_supported"],
            xaa_metadata,
        )


def config_dir_path() -> Path:
    return project_dir.parent / "{{mcp_app_name}}"


class MCPOAuthProtectedResourceMetadataConfigManager:
    def __init__(self) -> None:
        self.config_dir_path = config_dir_path()

    def get_metadata_config_path(self) -> Path:
        return self.config_dir_path / "oauth-config.yaml"

    def load_metadata_config(self) -> dict[str, Any]:
        return yaml.safe_load(
            self.get_metadata_config_path().read_text(encoding="utf-8")
        )

    def get_yaml_string_of_metadata(self) -> str | None:
        metadata_in_string = None
        try:
            metadata_dict = self.load_metadata_config()
            metadata = MCPOAuthProtectedResourceMetadataConfig.from_dict(metadata_dict)
            metadata_in_string = metadata.to_yaml_string()
        except FileNotFoundError:
            error_message = (
                "Failed to load MCP OAuth protected resource metadata "
                f"from {self.get_metadata_config_path()}"
            )
            logger.info(error_message)
        except (AttributeError, KeyError, TypeError):
            logger.exception("Failed to parse MCP metadata")
        except YAMLError:
            logger.exception("Failed to load MCP metadata")
        return metadata_in_string


def mcp_oauth_metadata_value() -> str | None:
    """Resolve OAuth metadata YAML from MCP_OAUTH_METADATA env or oauth-config.yaml."""
    env_value = os.getenv("MCP_OAUTH_METADATA", "").strip()
    if env_value:
        return env_value
    return (
        MCPOAuthProtectedResourceMetadataConfigManager().get_yaml_string_of_metadata()
    )


def mcp_enable_unauthenticated_well_known_route_value() -> str:
    return str(
        os.getenv("MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE", "false")
    ).lower()


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
    env_vars: list[dict[str, str]] = [
        {
            "name": "MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE",
            "value": mcp_enable_unauthenticated_well_known_route_value(),
        },
    ]
    metadata = mcp_oauth_metadata_value()
    if metadata:
        env_vars.append({"name": "MCP_OAUTH_METADATA", "value": metadata})
    return env_vars
