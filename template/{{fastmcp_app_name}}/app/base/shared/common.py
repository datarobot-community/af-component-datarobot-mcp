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

import functools
import logging
import traceback
from typing import Any, Callable, TypeVar

import datarobot as dr
from datarobot.context import Context as DRContext
from mcp.server.fastmcp import Context  # Correct import for FastMCP Context
from opentelemetry import trace

from .credentials import get_credentials


def get_sdk_client(ctx: Context = None):
    """
    Get a DataRobot SDK client, using the user's Bearer token from the request if available.
    Args:
        ctx: Optional FastMCP Context object. If provided, will attempt to extract the Bearer token from the request headers.
    Returns:
        datarobot module with authenticated client.
    """
    token = None
    endpoint = None
    if ctx is not None:
        # Try to get the Bearer token from the request headers
        auth_header = None
        # FastMCP context may have .request or .request_headers
        if hasattr(ctx, "request") and hasattr(ctx.request, "headers"):
            headers = ctx.request.headers
            # headers may be a dict or a case-insensitive dict
            for k, v in headers.items():
                if k.lower() == "authorization":
                    auth_header = v
                    break
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
    if not token:
        credentials = get_credentials()
        token = credentials.datarobot.api_token
        endpoint = credentials.datarobot.endpoint
    else:
        credentials = get_credentials()
        endpoint = credentials.datarobot.endpoint
    dr.Client(token=token, endpoint=endpoint)
    # The trafaret setting up a use case in the context, seem to mess up the tool calls
    DRContext.use_case = None
    return dr


def get_s3_bucket_info() -> dict[str, str]:
    """Get S3 bucket configuration."""
    credentials = get_credentials()
    return {
        "bucket": credentials.aws.s3_bucket,
        "prefix": credentials.aws.s3_prefix,
    }


# Type variable for generic function type
F = TypeVar("F", bound=Callable[..., Any])


class MCPError(Exception):
    """Base class for MCP errors"""


def setup_tool_logger(name: str) -> logging.Logger:
    """Set up a logger for tools with consistent formatting"""
    logger = logging.getLogger(name)
    if not logger.handlers:  # Only add handler if none exists
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_tool_error(
    logger: logging.Logger, func_name: str, error: Exception, **kwargs
) -> str:
    """Log tool errors in a consistent format"""
    error_msg = f"{type(error).__name__}: {str(error)}"
    logger.error(f"Error in {func_name}: {error_msg}")
    logger.debug(f"Full traceback: {traceback.format_exc()}")
    logger.debug(f"Function arguments: {kwargs}")
    return f"Error in {func_name}: {error_msg}"


def log_tool_execution(func: F) -> F:
    """Decorator to log tool execution with error handling"""
    logger = setup_tool_logger(func.__module__)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            logger.info(f"Starting {func.__name__}")
            logger.debug(f"Arguments: {args}, {kwargs}")
            result = await func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            error_msg = log_tool_error(
                logger, func.__name__, e, args=args, kwargs=kwargs
            )

            if span := trace.get_current_span():
                span.set_attribute("tool.success", False)
                span.record_exception(e)

            raise MCPError(error_msg)

    return wrapper
