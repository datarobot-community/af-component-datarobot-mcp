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

from dotenv import load_dotenv
from pydantic import AliasChoices, AliasPath, Field
from pydantic_settings import BaseSettings

load_dotenv(verbose=True, override=True)


class DRCredentials(BaseSettings): ...


class DataRobotCredentials(DRCredentials):
    """DataRobot API credentials."""

    api_token: str = Field(
        validation_alias="DATAROBOT_API_TOKEN", description="DataRobot API token"
    )
    endpoint: str = Field(
        default="https://app.datarobot.com/api/v2",
        validation_alias="DATAROBOT_ENDPOINT",
        description="DataRobot API endpoint",
    )


class AWSCredentials(DRCredentials):
    """AWS credentials for S3 operations."""

    runtime_param_env_var_name_prefix: str = "MLOPS_RUNTIME_PARAM_"
    aws_credentials_env_var_name: str = (
        runtime_param_env_var_name_prefix + "MCP_AWS_CREDENTIALS"
    )

    access_key_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "AWS_ACCESS_KEY_ID",
            AliasPath(aws_credentials_env_var_name, "payload", "awsAccessKeyId"),
        ),
        description="AWS Access Key ID",
    )
    secret_access_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "AWS_SECRET_ACCESS_KEY",
            AliasPath(
                aws_credentials_env_var_name,
                "payload",
                "awsSecretAccessKey",
            ),
        ),
        description="AWS Secret Access Key",
    )
    session_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "AWS_SESSION_TOKEN",
            AliasPath(aws_credentials_env_var_name, "payload", "awsSessionToken"),
        ),
        description="AWS Session Token",
    )

    s3_bucket: str = Field(
        default="datarobot-rd",
        validation_alias="AWS_PREDICTIONS_S3_BUCKET",
        description="S3 bucket name",
    )
    s3_prefix: str = Field(
        default="dev/mcp-temp-storage/predictions/",
        validation_alias="AWS_PREDICTIONS_S3_PREFIX",
        description="S3 key prefix",
    )


class AppCredentials(DRCredentials):
    """Application credentials combining DataRobot and AWS credentials."""

    datarobot: DataRobotCredentials = Field(default_factory=DataRobotCredentials)
    aws: AWSCredentials = Field(default_factory=AWSCredentials)

    def has_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(self.aws.access_key_id and self.aws.secret_access_key)

    def has_datarobot_credentials(self) -> bool:
        """Check if DataRobot credentials are configured."""
        return bool(self.datarobot.api_token)


# Global credentials instance
_credentials: Optional[AppCredentials] = None


def get_credentials() -> AppCredentials:
    """Get the global credentials instance."""
    global _credentials
    if _credentials is None:
        _credentials = AppCredentials()
    return _credentials
