"""OpenTelemetry tracing integration for distributed observability.

This module provides OpenTelemetry integration for:
- Distributed tracing across microservices
- Automatic span creation for HTTP requests
- Custom instrumentation for business logic
- Integration with Jaeger, Zipkin, or other OTLP-compatible backends

Configuration:
    Enable tracing via settings:
    >>> from saju_common import settings
    >>> settings.enable_tracing = True
    >>> settings.service_name = "analysis-service"

    Or via environment variables:
    >>> export SAJU_ENABLE_TRACING=true
    >>> export SAJU_SERVICE_NAME=analysis-service
    >>> export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

Usage:
    >>> from saju_common.tracing import setup_tracing, trace_function
    >>> # In application startup
    >>> setup_tracing()
    >>>
    >>> # Decorate functions for automatic tracing
    >>> @trace_function("calculate_strength")
    >>> def calculate_strength(pillars):
    >>>     # Your code here
    >>>     pass

References:
- OpenTelemetry Python: https://opentelemetry.io/docs/instrumentation/python/
- Week 4 Task 7: Integrate OpenTelemetry/structured logging
"""

from __future__ import annotations

import functools
import logging
import os
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional
from urllib.parse import urlparse

from .settings import settings

logger = logging.getLogger(__name__)


def _parse_otlp_headers(raw_headers: Optional[str]) -> dict[str, str]:
    if not raw_headers:
        return {}

    parsed: dict[str, str] = {}
    for entry in raw_headers.split(","):
        if not entry:
            continue
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        key = key.strip()
        if not key:
            continue
        parsed[key] = value.strip()
    return parsed


def _infer_otlp_protocol(endpoint: str, protocol_hint: Optional[str]) -> str:
    if protocol_hint:
        hint = protocol_hint.lower()
        if hint in {"http", "http/protobuf", "http/proto"}:
            return "http"
        if hint in {"grpc", "grpc/protobuf"}:
            return "grpc"

    parsed = urlparse(endpoint)

    if parsed.scheme in {"grpc", "grpcs"}:
        return "grpc"

    if parsed.port == 4318 or parsed.path.rstrip("/") == "/v1/traces":
        return "http"

    return "grpc"


def _create_otlp_exporter(
    *,
    endpoint: str,
    headers: dict[str, str],
    protocol_hint: Optional[str],
    grpc_exporter_cls,
    http_exporter_cls,
):
    protocol = _infer_otlp_protocol(endpoint, protocol_hint)

    exporter_kwargs = {"endpoint": endpoint}
    if headers:
        exporter_kwargs["headers"] = headers

    if protocol == "http":
        return http_exporter_cls(**exporter_kwargs), "http"

    return grpc_exporter_cls(**exporter_kwargs), "grpc"

# Type stubs for when OpenTelemetry is not installed
TracerProvider = Any
Tracer = Any
Span = Any

# Global tracer instance
_tracer: Optional[Tracer] = None
_tracing_enabled = False


def setup_tracing(
    service_name: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> bool:
    """Initialize OpenTelemetry tracing.

    This function:
    - Configures the OpenTelemetry SDK
    - Sets up OTLP exporter (if endpoint provided)
    - Instruments FastAPI automatically
    - Creates global tracer for manual instrumentation

    Args:
        service_name: Service name for tracing (defaults to settings.service_name)
        endpoint: OTLP exporter endpoint (defaults to OTEL_EXPORTER_OTLP_ENDPOINT env var)

    Returns:
        True if tracing was successfully initialized, False otherwise

    Example:
        >>> # Automatic configuration from settings
        >>> setup_tracing()
        >>>
        >>> # Manual configuration
        >>> setup_tracing(
        >>>     service_name="analysis-service",
        >>>     endpoint="http://localhost:4317"
        >>> )
    """
    global _tracer, _tracing_enabled

    # Check if tracing is enabled in settings
    if not settings.enable_tracing:
        logger.info("OpenTelemetry tracing disabled (SAJU_ENABLE_TRACING=false)")
        _tracing_enabled = False
        return False

    # Import OpenTelemetry dependencies (optional dependency)
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter as OTLPGRPCSpanExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as OTLPHTTPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        logger.warning(
            "OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp"
        )
        _tracing_enabled = False
        return False

    # Determine service name
    final_service_name = service_name or settings.service_name or "saju-service"

    # Create resource with service name
    resource = Resource(attributes={SERVICE_NAME: final_service_name})

    # Create and set tracer provider
    provider = TracerProvider(resource=resource)

    otlp_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    otlp_headers = _parse_otlp_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))
    otlp_protocol_hint = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL")

    if otlp_endpoint:
        try:
            exporter, protocol = _create_otlp_exporter(
                endpoint=otlp_endpoint,
                headers=otlp_headers,
                protocol_hint=otlp_protocol_hint,
                grpc_exporter_cls=OTLPGRPCSpanExporter,
                http_exporter_cls=OTLPHTTPSpanExporter,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OpenTelemetry OTLP %s exporter configured: %s",
                protocol.upper(),
                otlp_endpoint,
            )
        except Exception as exc:
            logger.warning(
                "Failed to configure OTLP exporter (%s): %s",
                otlp_endpoint,
                exc,
            )

    # Add console exporter for development (only if log level is DEBUG)
    if settings.log_level == "DEBUG":
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.debug("OpenTelemetry console exporter enabled (DEBUG mode)")

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Create global tracer
    _tracer = trace.get_tracer(__name__)
    _tracing_enabled = True

    # Auto-instrument FastAPI
    try:
        FastAPIInstrumentor.instrument()
        logger.info(f"OpenTelemetry tracing initialized for '{final_service_name}'")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")

    return True


def get_tracer() -> Optional[Tracer]:
    """Get the global tracer instance.

    Returns:
        Tracer instance if tracing is enabled, None otherwise

    Example:
        >>> tracer = get_tracer()
        >>> if tracer:
        >>>     with tracer.start_as_current_span("my_operation"):
        >>>         # Your code here
        >>>         pass
    """
    return _tracer if _tracing_enabled else None


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
) -> Iterator[Optional[Span]]:
    """Context manager for manual span creation.

    Args:
        name: Span name (should be concise, e.g., "calculate_strength")
        attributes: Optional attributes to add to span

    Yields:
        Span instance if tracing is enabled, None otherwise

    Example:
        >>> with trace_span("calculate_pillars", {"user_id": "123"}):
        >>>     pillars = calculate_four_pillars(birth_dt)
        >>>     # Span automatically closed
    """
    tracer = get_tracer()

    if not tracer:
        # Tracing disabled, yield None and continue execution
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span


def trace_function(
    span_name: Optional[str] = None,
    attributes: Optional[Callable[[Any], dict[str, Any]]] = None,
) -> Callable:
    """Decorator for automatic function tracing.

    Args:
        span_name: Custom span name (defaults to function name)
        attributes: Optional function to extract attributes from function args

    Returns:
        Decorated function with automatic span creation

    Example:
        >>> @trace_function("strength_evaluation")
        >>> def evaluate_strength(pillars):
        >>>     # Function automatically traced
        >>>     return strength_score
        >>>
        >>> # With custom attributes
        >>> @trace_function(
        >>>     "pillar_calculation",
        >>>     attributes=lambda args, kwargs: {"user_id": kwargs.get("user_id")}
        >>> )
        >>> def calculate_pillars(birth_dt, user_id=None):
        >>>     # Span includes user_id attribute
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        name = span_name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract attributes if function provided
            attrs = attributes(args, kwargs) if attributes else None

            with trace_span(name, attrs) as span:
                # Add function metadata
                if span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract attributes if function provided
            attrs = attributes(args, kwargs) if attributes else None

            with trace_span(name, attrs) as span:
                # Add function metadata
                if span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attribute(key: str, value: Any) -> None:
    """Add attribute to current active span.

    Args:
        key: Attribute key
        value: Attribute value (must be serializable)

    Example:
        >>> with trace_span("calculate_strength"):
        >>>     strength_score = evaluate(pillars)
        >>>     add_span_attribute("strength.score", strength_score)
        >>>     add_span_attribute("strength.level", "신약")
    """
    if not _tracing_enabled:
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    except Exception as e:
        logger.debug(f"Failed to add span attribute: {e}")


def add_span_event(name: str, attributes: Optional[dict[str, Any]] = None) -> None:
    """Add event to current active span.

    Events are point-in-time occurrences during span lifetime.

    Args:
        name: Event name
        attributes: Optional event attributes

    Example:
        >>> with trace_span("process_analysis"):
        >>>     add_span_event("policy_loaded", {"policy": "strength_v2"})
        >>>     result = analyze(pillars)
        >>>     add_span_event("analysis_complete", {"score": result.score})
    """
    if not _tracing_enabled:
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})
    except Exception as e:
        logger.debug(f"Failed to add span event: {e}")


def record_exception(exception: Exception) -> None:
    """Record exception in current active span.

    Args:
        exception: Exception instance to record

    Example:
        >>> with trace_span("risky_operation"):
        >>>     try:
        >>>         result = dangerous_function()
        >>>     except ValueError as e:
        >>>         record_exception(e)
        >>>         raise
    """
    if not _tracing_enabled:
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
    except Exception as e:
        logger.debug(f"Failed to record exception: {e}")


# Convenience exports
__all__ = [
    "setup_tracing",
    "get_tracer",
    "trace_span",
    "trace_function",
    "add_span_attribute",
    "add_span_event",
    "record_exception",
]
