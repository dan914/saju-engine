"""ASGI middleware for request logging, correlation IDs, and response timing.

This module provides middleware for:
- Correlation ID injection and propagation
- Structured request/response logging
- Request timing and performance metrics
- Trace header propagation

References:
- Phase 3 Remediation: grand audit/phase3_remediation_plan.md (Week 2)
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .settings import settings

logger = logging.getLogger(__name__)
try:
    from .client_identity import ProxyConfig, extract_client_ip
except Exception:  # pragma: no cover
    ProxyConfig = None  # type: ignore
    extract_client_ip = None  # type: ignore


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware for correlation ID injection and propagation.

    This middleware:
    - Extracts correlation ID from X-Correlation-ID or X-Request-ID header
    - Generates new correlation ID if none provided
    - Adds correlation ID to request.state for use by handlers
    - Adds X-Correlation-ID header to response

    Example:
        >>> from fastapi import FastAPI
        >>> from services.common.middleware import CorrelationIDMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(CorrelationIDMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and inject correlation ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with X-Correlation-ID header
        """
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid4())
        )

        # Store in request state for access by handlers
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging with timing.

    This middleware:
    - Logs all incoming requests with method, path, correlation ID
    - Measures request processing time
    - Logs response status code and timing
    - Provides structured log fields for aggregation

    Example:
        >>> from fastapi import FastAPI
        >>> from services.common.middleware import RequestLoggingMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(RequestLoggingMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        exclude_paths: list[str] | None = None,
        proxy_config: Optional[ProxyConfig] = None,
    ) -> None:
        """Initialize logging middleware.

        Args:
            app: ASGI application
            exclude_paths: Paths to exclude from logging (e.g., /health)
            proxy_config: Optional proxy header/CIDR configuration
        """
        super().__init__(app)
        self.exclude_paths = set(exclude_paths or ["/health", "/"])
        self._proxy_config = proxy_config

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log timing information.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract correlation ID from request state
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log incoming request
        start_time = time.time()
        client_host = request.client.host if request.client else None
        if self._proxy_config and extract_client_ip:
            client_host = extract_client_ip(
                request.headers,
                client_host,
                self._proxy_config,
            )

        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "event": "request_start",
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "correlation_id": correlation_id,
                "client_host": client_host,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "event": "request_complete",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "correlation_id": correlation_id,
                },
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"{request.method} {request.url.path} - ERROR ({duration_ms:.2f}ms)",
                extra={
                    "event": "request_error",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "correlation_id": correlation_id,
                    "exception_type": exc.__class__.__name__,
                },
                exc_info=True,
            )
            raise


def configure_logging(*, json_format: bool = False) -> None:
    """Configure structured logging for the application.

    Args:
        json_format: If True, use JSON logging format for structured logs.
                     If False, use standard text format.

    Example:
        >>> from services.common.middleware import configure_logging
        >>> # For development
        >>> configure_logging(json_format=False)
        >>> # For production
        >>> configure_logging(json_format=True)
    """
    if json_format:
        # JSON logging for production (structured log aggregation)
        import json
        import sys

        class JSONFormatter(logging.Formatter):
            """Custom JSON formatter for structured logging."""

            def format(self, record: logging.LogRecord) -> str:
                """Format log record as JSON.

                Args:
                    record: Log record to format

                Returns:
                    JSON-formatted log string
                """
                log_data = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                # Add extra fields
                if hasattr(record, "correlation_id"):
                    log_data["correlation_id"] = record.correlation_id
                if hasattr(record, "event"):
                    log_data["event"] = record.event
                if hasattr(record, "method"):
                    log_data["method"] = record.method
                if hasattr(record, "path"):
                    log_data["path"] = record.path
                if hasattr(record, "status_code"):
                    log_data["status_code"] = record.status_code
                if hasattr(record, "duration_ms"):
                    log_data["duration_ms"] = record.duration_ms

                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_data)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler],
        )

    else:
        # Text logging for development (human-readable)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Convenience function for adding all middleware at once
def add_middleware(
    app: ASGIApp,
    *,
    exclude_logging_paths: list[str] | None = None,
) -> None:
    """Add all standard middleware to FastAPI app.

    This function adds:
    1. CorrelationIDMiddleware (outermost - runs first)
    2. RequestLoggingMiddleware

    Args:
        app: FastAPI application instance
        exclude_logging_paths: Paths to exclude from request logging

    Example:
        >>> from fastapi import FastAPI
        >>> from services.common.middleware import add_middleware
        >>> app = FastAPI()
        >>> add_middleware(app, exclude_logging_paths=["/health", "/metrics"])
    """
    # Add middleware in reverse order (they wrap each other)
    proxy_config = None
    if ProxyConfig and extract_client_ip:
        try:
            proxy_config = ProxyConfig.from_settings(settings)
        except Exception:
            proxy_config = None

    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=exclude_logging_paths,
        proxy_config=proxy_config,
    )
    app.add_middleware(CorrelationIDMiddleware)
