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
    # currently there seem to be a problem with the custom application api token, so we are using the user api token
    # curl -X POST -H "Authorization: Bearer ..." -H "Content-Type: application/json" -d '{"entitlements": [{"name": "ENABLE_ENHANCED_SAML_SSO"}]}' https://staging.datarobot.com/api/v2/entitlements/evaluate/
    # {"message": "Invalid Authorization header"}
    api_token = (
        credentials.datarobot.user_api_token
        or credentials.datarobot.application_api_token
    )

    config = get_config()
    otlp_endpoint = config.otel_collector_base_url
    entity_id = config.otel_entity_id

    otlp_headers = f"X-DataRobot-Api-Key={api_token},X-DataRobot-Entity-Id={entity_id}"
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = otlp_headers
    root_logger.info(
        f"Using OTEL_EXPORTER_OTLP_ENDPOINT: {otlp_endpoint} with X-DataRobot-Entity-Id {entity_id}"
    )


def _setup_otel_exporter() -> None:
    """Setup OpenTelemetry exporter with SimpleSpanProcessor."""
    otlp_exporter = OTLPSpanExporter()
    span_processor = SimpleSpanProcessor(otlp_exporter)
    provider = trace.get_tracer_provider()
    # mypy: TracerProvider has add_span_processor at runtime; typing may lag
    if hasattr(provider, "add_span_processor"):
        provider.add_span_processor(span_processor)


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
    if not config.otel_enabled:
        root_logger.info("OpenTelemetry is disabled")
        return None

    # If OTEL_ENTITY_ID is not set, skip telemetry
    if not config.otel_entity_id and not os.environ.get("OTEL_EXPORTER_OTLP_HEADERS"):
        root_logger.info(
            "Neither OTEL_ENTITY_ID nor OTEL_EXPORTER_OTLP_HEADERS is set, skipping telemetry"
        )
        return None

    # Create resource with service name from config
    resource = Resource.create({"service.name": config.mcp_server_name})

    # Set up tracer provider with service name from config
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Setup environment
    _setup_otel_env_variables()

    # Setup OTEL exporter
    _setup_otel_exporter()

    # Setup HTTP client instrumentation
    if config.otel_enabled_http_instrumentors:
        _setup_http_instrumentors()

    # Create root span for the application
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span("mcp_server")

    # Add configured attributes
    if config.otel_attributes:
        root_logger.info("Setting up custom OTEL attributes")
        _set_otel_attributes(span, config.otel_attributes)

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

    # Skip 'self' parameter for methods (only if first param is named 'self')
    start_idx = 1 if args and param_names and param_names[0] == "self" else 0
    param_names = param_names[start_idx:]
    args = args[start_idx:]

    # Add positional arguments
    for name, value in zip(param_names, args):
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(f"tool.param.{name}", value)

    # Add keyword arguments
    for name, value in kwargs.items():
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(f"tool.param.{name}", value)


def get_trace_id() -> Optional[str]:
    """Get the current trace ID if available."""
    current_span = trace.get_current_span()
    if not current_span:
        return None

    context: SpanContext = current_span.get_span_context()
    if not context.is_valid:
        return None

    return str(format_trace_id(context.trace_id))


T = TypeVar("T", bound=Callable[..., Any])


def trace_execution(
    trace_name: str | None = None, trace_type: str = "tool"
) -> Callable[[T], T]:
    """Decorator to trace tool execution.

    Args:
        trace_name: Optional name for the span. If not provided, uses the function name.
        trace_type: Optional type for the span. If not provided, uses "tool".

    Example:
        @trace_execution()
        async def my_tool(self, param1: str) -> str:
            return "result"

        @trace_execution("custom_name")
        async def another_tool(self, param1: str) -> str:
            return "result"
    """

    def decorator(func: T) -> T:
        def _create_span_for_tool(
            trace_name: str | None,
            trace_type: str,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Span:
            # Get span name from decorator arg, function name, or class method name
            span_name = trace_name
            if not span_name:
                if (
                    args
                    and hasattr(args[0], "__class__")
                    and not isinstance(args[0], (str, int, float, bool))
                ):
                    # If it's a method, include the class name
                    span_name = f"{args[0].__class__.__name__}.{func.__name__}"
                else:
                    # Just use the function name without any prefix
                    span_name = func.__name__

            # Start a new span
            tracer = trace.get_tracer(__name__)
            span = tracer.start_span(f"{trace_type}.{span_name}")

            # Add standard attributes
            span.set_attribute("mcp.type", trace_type)
            span.set_attribute(f"{trace_type}.name", span_name)

            # Add tool parameters as span attributes
            _add_parameters_to_span(span, func, args, kwargs)

            # Add configured attributes from config
            config = get_config()
            if config.otel_attributes:
                _set_otel_attributes(span, config.otel_attributes)

            return span

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = _create_span_for_tool(trace_name, trace_type, args, kwargs)
            try:
                result = await func(*args, **kwargs)
                span.set_attribute(f"{trace_type}.success", True)
                return result
            except Exception as e:
                span.set_attribute(f"{trace_type}.success", False)
                span.record_exception(e)
                raise e
            finally:
                span.end()

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = _create_span_for_tool(trace_name, trace_type, args, kwargs)
            try:
                result = func(*args, **kwargs)
                span.set_attribute(f"{trace_type}.success", True)
                return result
            except Exception as e:
                span.set_attribute(f"{trace_type}.success", False)
                span.record_exception(e)
                raise e
            finally:
                span.end()

        # Use appropriate wrapper based on whether the function is async
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper  # type: ignore[return-value]

    return decorator
