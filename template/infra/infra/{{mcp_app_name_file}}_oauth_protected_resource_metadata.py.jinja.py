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
import json
import logging
import os
from dataclasses import asdict
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any
from pathlib import Path

import pulumi_datarobot


logger = logging.getLogger(__name__)


@dataclass
class XAATokenExchangeParams:
    trusted_issuer: str
    audience: str

    @classmethod
    def from_json(cls, json_dict: dict[str, str]) -> "XAATokenExchangeParams":
        return cls(json_dict["trusted_issuer"], json_dict["audience"])


@dataclass
class XAATokenRequestParams:
    token_url: str
    # audience can be None if it is not setup for AuthN & AuthZ check (as resource) in IdP.
    audience: str | None
    scopes: list[str]

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "XAATokenRequestParams":
        return cls(
            json_dict["token_url"], json_dict.get("audience"), json_dict["scopes"]
        )


@dataclass
class XAAMetadata:
    token_endpoint_auth_method: str
    token_exchange: XAATokenExchangeParams
    token_request: XAATokenRequestParams

    @classmethod
    def from_json(cls, metadata_in_json: dict[str, Any]) -> "XAAMetadata":
        return cls(
            metadata_in_json["token_endpoint_auth_method"],
            XAATokenExchangeParams.from_json(metadata_in_json["token_exchange"]),
            XAATokenRequestParams.from_json(metadata_in_json["token_request"]),
        )

    def to_json_string(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class MCPOAuthProtectedResourceMetadata:
    resource: str
    authorization_servers: list[str]
    scopes_supported: list[str]
    xaa_metadata: XAAMetadata

    @classmethod
    def from_json(
        cls, metadata_in_json: dict[str, Any]
    ) -> "MCPOAuthProtectedResourceMetadata":
        return cls(
            metadata_in_json["resource"],
            metadata_in_json["authorization_servers"],
            metadata_in_json["scopes_supported"],
            XAAMetadata.from_json(metadata_in_json["xaa_metadata"]),
        )

    def to_json_string(self) -> str:
        return json.dumps(asdict(self))


def config_dir_path() -> Path:
    current_path = Path(os.path.dirname(__file__))
    return current_path.parent / "configurations"


class MCPOAuthProtectedResourceMetadataManager:
    def __init__(self):
        self.config_dir_path = config_dir_path()

    def get_metadata_config_path(self) -> Path:
        return self.config_dir_path / "mcp_oauth_protected_resource_metadata.json"

    def load_metadata_config(self) -> dict[str, Any]:
        return json.loads(self.get_metadata_config_path().read_text(encoding="utf-8"))

    def get_json_string_of_metadata(self) -> str | None:
        metadata_in_json_string = None
        try:
            metadata_json = self.load_metadata_config()
            metadata = MCPOAuthProtectedResourceMetadata.from_json(metadata_json)
            metadata_in_json_string = metadata.to_json_string()
        except FileNotFoundError:
            error_message = (
                "Failed to load MCP OAuth protected resource metadata "
                f"from {self.get_metadata_config_path()}"
            )
            logger.info(error_message)
        except (KeyError, TypeError):
            logger.exception("Failed to parse MCP metadata")
        except JSONDecodeError:
            logger.exception("Failed to load MCP metadata")
        return metadata_in_json_string

    def get_pulumi_custom_model_runtime_parameter_value_args_of_mcp_metadata(
        self,
    ) -> pulumi_datarobot.CustomModelRuntimeParameterValueArgs | None:
        metadata_in_json_string = self.get_json_string_of_metadata()

        return (
            pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
                key="MCP_OAUTH_PROTECTED_RESOURCE_METADATA",
                type="string",
                value=metadata_in_json_string,
            )
            if metadata_in_json_string
            else None
        )
