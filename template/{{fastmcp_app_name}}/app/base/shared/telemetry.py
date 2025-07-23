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
import inspect
import logging
import os
from typing import Any, Callable, Optional, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Span, SpanContext, format_trace_id

from .config import get_config
from .credentials import get_credentials

root_logger = logging.getLogger(__name__)

# Track instrumentation state
_INSTRUMENTED = False


def _setup_otel_env_variables() -> None:
    """Setup OpenTelemetry environment variables for DataRobot integration."""

    # do not override if already set
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get(
        "OTEL_EXPORTER_OTLP_HEADERS"
    ):
        root_logger.info(
            "OTEL_EXPORTER_OTLP_ENDPOINT or OTEL_EXPORTER_OTLP_HEADERS already set, skipping"
        )
        return

    credentials = get_credentials()
    datarobot_api_token = credentials.datarobot.api_token

    config = get_config()
    otlp_endpoint = config.otel.collector_base_url
    entity_id = config.otel.entity_id

    otlp_headers = (
        f"X-DataRobot-Api-Key={datarobot_api_token},X-DataRobot-Entity-Id={entity_id}"
    )
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = otlp_headers
    root_logger.info(
        f"Using OTEL_EXPORTER_OTLP_ENDPOINT: {otlp_endpoint} with X-DataRobot-Entity-Id {entity_id}"
    )


def _setup_otel_exporter() -> None:
    """Setup OpenTelemetry exporter with SimpleSpanProcessor."""
    otlp_exporter = OTLPSpanExporter()
    span_processor = SimpleSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)


def _setup_http_instrumentors() -> None:
    """Setup HTTP client instrumentors.

    This function is idempotent - it will only instrument clients once.
    """
    global _INSTRUMENTED
    if _INSTRUMENTED:
        root_logger.debug("HTTP clients already instrumented")
        return

    root_logger.info("Setting up HTTP client instrumentation")
    try:
        # Instrument requests library
        RequestsInstrumentor().instrument()
        root_logger.debug("Instrumented requests library")
    except Exception as e:
        root_logger.warning(f"Failed to instrument requests: {e}")

    try:
        # Instrument aiohttp client
        AioHttpClientInstrumentor().instrument()
        root_logger.debug("Instrumented aiohttp client")
    except Exception as e:
        root_logger.warning(f"Failed to instrument aiohttp: {e}")

    try:
        # Instrument httpx
        HTTPXClientInstrumentor().instrument()
        root_logger.debug("Instrumented httpx")
    except Exception as e:
        root_logger.warning(f"Failed to instrument httpx: {e}")

    _INSTRUMENTED = True
    root_logger.info("HTTP client instrumentation complete")


def _set_otel_attributes(span: Span, attributes: dict[str, Any]) -> None:
    """Set custom attributes on a span."""
    # Flatten nested attributes
    flattened_attrs = {}
    for key, value in attributes.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flattened_attrs[f"{key}.{sub_key}"] = sub_value
        else:
            flattened_attrs[key] = value

    # Set each attribute
    for key, value in flattened_attrs.items():
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(key, value)


def initialize_telemetry() -> Optional[Span]:
    """Initialize OpenTelemetry for the FastMCP application."""
    config = get_config()

    # If OpenTelemetry is disabled, return None
    if not config.otel.enabled:
        root_logger.info("OpenTelemetry is disabled")
        return None

    # Create resource with service name from config
    resource = Resource.create({"service.name": config.name})

    # Set up tracer provider with service name from config
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Setup environment
    _setup_otel_env_variables()

    # Setup OTEL exporter
    _setup_otel_exporter()

    # Setup HTTP client instrumentation
    _setup_http_instrumentors()

    # Create root span for the application
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span("mcp_server")

    # Add configured attributes
    if config.otel.attributes:
        root_logger.info("Setting up custom OTEL attributes")
        _set_otel_attributes(span, config.otel.attributes)

    return span


"""Helper functions for OpenTelemetry instrumentation of tools."""


def _add_parameters_to_span(
    span: Span, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    """Add function parameters as span attributes.

    Only adds simple types (str, int, float, bool) to avoid complex object serialization.
    Skips 'self' parameter for methods.
    """
    # Get parameter names
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    # Handle args (skip self for methods)
    start_idx = 1 if args and hasattr(args[0], "__class__") else 0
    for i, arg in enumerate(args[start_idx:], start=start_idx):
        if i < len(param_names):
            param_name = param_names[i]
            if isinstance(arg, (str, int, float, bool)):
                span.set_attribute(f"tool.param.{param_name}", arg)

    # Handle kwargs
    for name, value in kwargs.items():
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(f"tool.param.{name}", value)


def _get_trace_id() -> Optional[str]:
    """Get the current trace ID if available."""
    current_span = trace.get_current_span()
    if not current_span:
        return None

    context: SpanContext = current_span.get_span_context()
    if not context.is_valid:
        return None

    return format_trace_id(context.trace_id)


T = TypeVar("T", bound=Callable[..., Any])


def trace_tool(name: str | None = None) -> Callable[[T], T]:
    """Decorator to trace tool execution.

    Args:
        name: Optional name for the span. If not provided, uses the function name.

    Example:
        @trace_tool()
        async def my_tool(self, param1: str) -> str:
            return "result"

        @trace_tool("custom_name")
        async def another_tool(self, param1: str) -> str:
            return "result"
    """

    def decorator(func: T) -> T:
        def _create_span_for_tool(
            name: str | None, args: tuple[Any, ...], kwargs: dict[str, Any]
        ) -> Span:
            # Get span name from decorator arg, function name, or class method name
            span_name = name
            if not span_name:
                if args and hasattr(args[0], "__class__"):
                    # If it's a method, include the class name
                    span_name = f"{args[0].__class__.__name__}.{func.__name__}"
                else:
                    span_name = func.__name__

            # Start a new span
            tracer = trace.get_tracer(__name__)
            span = tracer.start_span(f"tool.{span_name}")

            # Add standard attributes
            span.set_attribute("tool.name", span_name)
            span.set_attribute("tool.type", "mcp")

            # Add tool parameters as span attributes
            _add_parameters_to_span(span, func, args, kwargs)

            # Add configured attributes from config
            config = get_config()
            if config.otel.attributes:
                _set_otel_attributes(span, config.otel.attributes)

            return span

        def _add_success_attribute(span: Span) -> None:
            # Add success attribute
            span.set_attribute("tool.success", True)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _create_span_for_tool(name, args, kwargs) as span:
                result = await func(*args, **kwargs)
                _add_success_attribute(span)
                return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _create_span_for_tool(name, args, kwargs) as span:
                result = func(*args, **kwargs)
                _add_success_attribute(span)
                return result

        # Use appropriate wrapper based on whether the function is async
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
