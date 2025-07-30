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

from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.base.core.constants import (
    DEFAULT_DATAROBOT_ENDPOINT,
    RUNTIME_PARAM_ENV_VAR_NAME_PREFIX,
)


class DataRobotCredentials(BaseSettings):
    """DataRobot API credentials."""

    api_token: str = Field(
        default="test-token",  # For testing
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "DATAROBOT_API_TOKEN",
            "DATAROBOT_API_TOKEN",
        ),
        description="DataRobot API token",
    )
    endpoint: str = Field(
        default=DEFAULT_DATAROBOT_ENDPOINT,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "DATAROBOT_ENDPOINT",
            "DATAROBOT_ENDPOINT",
        ),
        description="DataRobot API endpoint",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
    )


class MCPServerCredentials(BaseSettings):
    """Application credentials combining DataRobot and AWS credentials."""

    datarobot: DataRobotCredentials = Field(default_factory=DataRobotCredentials)

    # AWS Credentials
    aws_access_key_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "AWS_ACCESS_KEY_ID",
            "AWS_ACCESS_KEY_ID",
        ),
        description="AWS Access Key ID",
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "AWS_SECRET_ACCESS_KEY",
            "AWS_SECRET_ACCESS_KEY",
        ),
        description="AWS Secret Access Key",
    )
    aws_session_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "AWS_SESSION_TOKEN",
            "AWS_SESSION_TOKEN",
        ),
        description="AWS Session Token",
    )

    aws_predictions_s3_bucket: str = Field(
        default="datarobot-rd",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "AWS_PREDICTIONS_S3_BUCKET",
            "AWS_PREDICTIONS_S3_BUCKET",
        ),
        description="S3 bucket name",
    )
    aws_predictions_s3_prefix: str = Field(
        default="dev/mcp-temp-storage/predictions/",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "AWS_PREDICTIONS_S3_PREFIX",
            "AWS_PREDICTIONS_S3_PREFIX",
        ),
        description="S3 key prefix",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
    )

    def has_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    def has_datarobot_credentials(self) -> bool:
        """Check if DataRobot credentials are configured."""
        return bool(self.datarobot.api_token)


# Global credentials instance
_credentials: Optional[MCPServerCredentials] = None


def get_credentials() -> MCPServerCredentials:
    """Get the global credentials instance."""
    global _credentials
    if _credentials is None:
        _credentials = MCPServerCredentials()
    return _credentials
