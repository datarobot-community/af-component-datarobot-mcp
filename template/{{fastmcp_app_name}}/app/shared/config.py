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
import re
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

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


class MCPServerConfig(BaseSettings):
    """MCP Server configuration using pydantic settings."""

    name: str = Field(
        default="Deployments",
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
