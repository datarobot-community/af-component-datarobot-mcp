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

import datarobot as dr

from shared.credentials import get_credentials


def get_sdk_client():
    credentials = get_credentials()
    dr.Client(
        token=credentials.datarobot.api_token, endpoint=credentials.datarobot.endpoint
    )
    return dr


def get_s3_bucket_info() -> dict[str, str]:
    """Get S3 bucket configuration."""
    credentials = get_credentials()
    return {
        "bucket": credentials.aws.s3_bucket,
        "prefix": credentials.aws.s3_prefix,
    }
