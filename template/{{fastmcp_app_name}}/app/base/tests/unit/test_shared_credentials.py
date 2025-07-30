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

from unittest.mock import patch

from app.base.core import credentials


def test_datarobot_credentials_default_endpoint():
    """Test DataRobot credentials with default endpoint."""
    with patch.dict("os.environ", {}, clear=True):  # Clear all env vars
        creds = credentials.DataRobotCredentials()
        assert creds.api_token == "test-token"
        assert creds.endpoint == "https://app.datarobot.com/api/v2"


def test_datarobot_credentials_custom_endpoint():
    """Test DataRobot credentials with custom endpoint."""
    with patch.dict(
        "os.environ",
        {
            "DATAROBOT_ENDPOINT": "https://custom.endpoint.com/api/v2",
        },
        clear=True,  # Clear all env vars first
    ):
        creds = credentials.DataRobotCredentials()
        assert creds.api_token == "test-token"
        assert creds.endpoint == "https://custom.endpoint.com/api/v2"


def test_mcp_server_credentials_aws_defaults():
    """Test AWS credentials with default values."""
    with patch.dict("os.environ", {}, clear=True):  # Clear all env vars
        creds = credentials.MCPServerCredentials()
        assert creds.aws_access_key_id is None
        assert creds.aws_secret_access_key is None
        assert creds.aws_session_token is None
        assert creds.aws_predictions_s3_bucket == "datarobot-rd"
        assert creds.aws_predictions_s3_prefix == "dev/mcp-temp-storage/predictions/"


def test_mcp_server_credentials_aws_custom_values():
    """Test AWS credentials with custom values."""
    env_vars = {
        "AWS_ACCESS_KEY_ID": "test-key-id",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
        "AWS_SESSION_TOKEN": "test-session-token",
        "AWS_PREDICTIONS_S3_BUCKET": "custom-bucket",
        "AWS_PREDICTIONS_S3_PREFIX": "custom/prefix/",
    }
    with patch.dict("os.environ", env_vars, clear=True):  # Clear all env vars first
        creds = credentials.MCPServerCredentials()
        assert creds.aws_access_key_id == "test-key-id"
        assert creds.aws_secret_access_key == "test-secret-key"
        assert creds.aws_session_token == "test-session-token"
        assert creds.aws_predictions_s3_bucket == "custom-bucket"
        assert creds.aws_predictions_s3_prefix == "custom/prefix/"


def test_mcp_server_credentials_has_aws_credentials():
    """Test MCPServerCredentials.has_aws_credentials method."""
    # Test with AWS credentials
    env_vars = {
        "AWS_ACCESS_KEY_ID": "test-key-id",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    }
    with patch.dict("os.environ", env_vars, clear=True):  # Clear all env vars first
        creds = credentials.MCPServerCredentials()
        assert creds.has_aws_credentials() is True

    # Test without AWS credentials
    with patch.dict("os.environ", {}, clear=True):  # Clear all env vars
        creds = credentials.MCPServerCredentials()
        assert creds.has_aws_credentials() is False


def test_get_credentials_singleton():
    """Test get_credentials returns singleton instance."""
    with patch.dict("os.environ", {}, clear=True):  # Clear all env vars
        # Reset the singleton instance
        credentials._credentials = None

        # First call should create new instance
        creds1 = credentials.get_credentials()
        assert isinstance(creds1, credentials.MCPServerCredentials)

        # Second call should return same instance
        creds2 = credentials.get_credentials()
        assert creds2 is creds1
