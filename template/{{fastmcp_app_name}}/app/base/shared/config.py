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

import logging
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

from app.base.shared.constants import DEFAULT_DATAROBOT_ENDPOINT

load_dotenv(verbose=True, override=True)

# Secret patterns to redact from logs
SECRET_PATTERNS = [
    r"([a-zA-Z0-9]{20,})",  # Long alphanumeric strings (potential tokens)
    r"(sk-[a-zA-Z0-9]{48})",  # OpenAI-style keys
    r"(AKIA[0-9A-Z]{16})",  # AWS Access Key pattern
]


class SecretRedactingFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive information from logs."""

    def format(self, record):
        msg = super().format(record)
        return self._redact_secrets(msg)

    def _redact_secrets(self, message: str) -> str:
        """Redact potential secrets from log messages."""
        for pattern in SECRET_PATTERNS:
            message = re.sub(pattern, "[REDACTED]", message)
        return message


class OpenTelemetrySettings(BaseSettings):
    """OpenTelemetry settings."""

    def _get_default_otel_endpoint() -> str:
        """Get the default OpenTelemetry endpoint e.g. https://app.datarobot.com/otel."""
        parsed_url = urlparse(
            os.environ.get("DATAROBOT_ENDPOINT", DEFAULT_DATAROBOT_ENDPOINT)
        )
        stripped_url = (parsed_url.scheme, parsed_url.netloc, "otel", "", "", "")
        return urlunparse(stripped_url)

    collector_base_url: str = Field(
        default=_get_default_otel_endpoint(),
        validation_alias="OTEL_COLLECTOR_BASE_URL",
        description="Base URL for the OpenTelemetry collector",
    )
    entity_id: str = Field(
        default="mcp-default",
        validation_alias="OTEL_ENTITY_ID",
        description="Entity ID for tracing",
    )
    attributes: Dict[str, Any] = Field(
        default={},
        validation_alias="OTEL_ATTRIBUTES",
        description="Attributes for tracing",
    )
    enabled: bool = Field(
        default=True,
        validation_alias="OTEL_ENABLED",
        description="Enable/disable OpenTelemetry",
    )


class MCPServerConfig(BaseSettings):
    """MCP Server configuration using pydantic settings."""

    name: str = Field(
        default="datarobot-mcp-server",
        validation_alias="MCP_SERVER_NAME",
        description="Name of the MCP server",
    )
    port: int = Field(
        default=8080,
        validation_alias="MCP_SERVER_PORT",
        description="Port number for the MCP server",
    )
    log_level: str = Field(
        default="WARNING",
        validation_alias="MCP_SERVER_LOG_LEVEL",
        description="Log level for the MCP server",
    )
    host: str = Field(
        default="0.0.0.0",
        validation_alias="MCP_SERVER_HOST",
        description="Host address for the MCP server",
    )
    root_logger_level: str = Field(
        default="INFO",
        validation_alias="ROOT_LOGGER_LEVEL",
        description="Root logger level",
    )
    otel: OpenTelemetrySettings = OpenTelemetrySettings()

    def setup_logging(self):
        """Configure logging with secret redaction and set log level."""
        # Create formatter with minimal format string
        formatter = SecretRedactingFormatter("%(message)s")

        # Remove all existing handlers
        logging.root.handlers.clear()

        # Add a console handler with our formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.root.addHandler(console_handler)

        # Set the root logger level
        logging.root.setLevel(self.root_logger_level)


# Global configuration instance
_config: Optional[MCPServerConfig] = None


def get_config() -> MCPServerConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MCPServerConfig()
        _config.setup_logging()
    return _config
