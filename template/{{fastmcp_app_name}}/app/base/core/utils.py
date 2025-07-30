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

import uuid
from typing import Optional

import boto3
from mcp.server.fastmcp.resources import HttpResource
from pydantic import BaseModel

from app.base.core.constants import MAX_INLINE_SIZE
from app.base.core.mcp_instance import mcp


def generate_presigned_url(bucket, key, expires_in=2592000):
    """
    Generate a presigned S3 URL for the given bucket and key.
    Args:
        bucket (str): S3 bucket name.
        key (str): S3 object key.
        expires_in (int): Expiration in seconds (default 30 days).
    Returns:
        str: Presigned S3 URL for get_object.
    """
    s3 = boto3.client("s3")
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
    )


class PredictionResponse(BaseModel):
    type: str
    data: Optional[str] = None
    resource_id: Optional[str] = None
    s3_url: Optional[str] = None


def predictions_result_response(
    df, bucket, key, resource_name, show_explanations=False
):
    csv_str = df.to_csv(index=False)
    if len(csv_str.encode("utf-8")) < MAX_INLINE_SIZE:
        return PredictionResponse(type="inline", data=csv_str)
    else:
        resource = save_df_to_s3_and_register_resource(df, bucket, key, resource_name)
        return PredictionResponse(
            type="resource",
            resource_id=resource.uri.encoded_string(),
            s3_url=resource.url,
            show_explanations=show_explanations,
        )


def save_df_to_s3_and_register_resource(
    df, bucket, key, resource_name, mime_type="text/csv"
):
    """
    Save a DataFrame to a temp CSV, upload to S3, register as a resource, and return the presigned URL.
    Args:
        df (pd.DataFrame): DataFrame to save and upload.
        bucket (str): S3 bucket name.
        key (str): S3 object key.
        resource_name (str): Name for the registered resource.
        mime_type (str): MIME type for the resource (default 'text/csv').
    Returns:
        str: Presigned S3 URL for the uploaded file.
    """
    temp_csv = f"/tmp/{uuid.uuid4()}.csv"
    df.to_csv(temp_csv, index=False)
    s3 = boto3.client("s3")
    s3.upload_file(temp_csv, bucket, key)
    s3_url = generate_presigned_url(bucket, key)
    resource = HttpResource(
        uri="predictions://" + uuid.uuid4().hex,
        url=s3_url,
        name=resource_name,
        mime_type=mime_type,
    )
    mcp.add_resource(resource)
    return resource
