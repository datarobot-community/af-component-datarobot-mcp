# Copyright 2025 DataRobot, Inc.
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

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.base.core.constants import (
    DEFAULT_DATAROBOT_ENDPOINT,
    RUNTIME_PARAM_ENV_VAR_NAME_PREFIX,
)


class MCPServerConfig(BaseSettings):
    """MCP Server configuration using pydantic settings."""

    mcp_server_name: str = Field(
        default="datarobot-mcp-server",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "MCP_SERVER_NAME",
            "MCP_SERVER_NAME",
        ),
        description="Name of the MCP server",
    )
    mcp_server_port: int = Field(
        default=8080,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "MCP_SERVER_PORT",
            "MCP_SERVER_PORT",
        ),
        description="Port number for the MCP server",
    )
    mcp_server_log_level: str = Field(
        default="WARNING",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "MCP_SERVER_LOG_LEVEL",
            "MCP_SERVER_LOG_LEVEL",
        ),
        description="Log level for the MCP server",
    )
    mcp_server_host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "MCP_SERVER_HOST",
            "MCP_SERVER_HOST",
        ),
        description="Host address for the MCP server",
    )
    app_log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "APP_LOG_LEVEL",
            "APP_LOG_LEVEL",
        ),
        description="App log level",
    )

    def _get_default_otel_endpoint() -> str:
        """Get the default OpenTelemetry endpoint e.g. https://app.datarobot.com/otel."""
        parsed_url = urlparse(
            os.environ.get("DATAROBOT_ENDPOINT", DEFAULT_DATAROBOT_ENDPOINT)
        )
        stripped_url = (parsed_url.scheme, parsed_url.netloc, "otel", "", "", "")
        return urlunparse(stripped_url)

    otel_collector_base_url: str = Field(
        default=_get_default_otel_endpoint(),
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "OTEL_COLLECTOR_BASE_URL",
            "OTEL_COLLECTOR_BASE_URL",
        ),
        description="Base URL for the OpenTelemetry collector",
    )
    otel_entity_id: str = Field(
        default="mcp-default",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "OTEL_ENTITY_ID",
            "OTEL_ENTITY_ID",
        ),
        description="Entity ID for tracing",
    )
    otel_attributes: Dict[str, Any] = Field(
        default={},
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "OTEL_ATTRIBUTES",
            "OTEL_ATTRIBUTES",
        ),
        description="Attributes for tracing (as JSON string)",
    )
    otel_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "OTEL_ENABLED",
            "OTEL_ENABLED",
        ),
        description="Enable/disable OpenTelemetry",
    )
    otel_enabled_http_instrumentors: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "OTEL_ENABLED_HTTP_INSTRUMENTORS",
            "OTEL_ENABLED_HTTP_INSTRUMENTORS",
        ),
        description="Enable/disable HTTP instrumentors",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
    )


# Global configuration instance
_config: Optional[MCPServerConfig] = None


def get_config() -> MCPServerConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MCPServerConfig()
    return _config
