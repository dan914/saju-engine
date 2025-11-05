"""FastAPI exception handlers with RFC7807 error envelopes.

This module provides FastAPI exception handlers that return RFC7807-compliant
error responses with correlation IDs for distributed tracing.

References:
- RFC7807: https://datatracker.ietf.org/doc/html/rfc7807
- Phase 3 Remediation: grand audit/phase3_remediation_plan.md (Week 2)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from .exceptions import (
        SajuBaseException,
        ValidationError,
        get_status_code,
    )
except ImportError:
    from exceptions import (
        SajuBaseException,
        ValidationError,
        get_status_code,
    )

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register RFC7807 exception handlers with FastAPI app.

    This function registers handlers for:
    - SajuBaseException (all domain exceptions)
    - Pydantic ValidationError (request validation)
    - FastAPI RequestValidationError (request validation)
    - Starlette HTTPException (HTTP errors)
    - Generic Exception (catch-all)

    Args:
        app: FastAPI application instance

    Example:
        >>> from fastapi import FastAPI
        >>> from services.common.handlers import register_exception_handlers
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """

    @app.exception_handler(SajuBaseException)
    async def saju_exception_handler(
        request: Request, exc: SajuBaseException
    ) -> JSONResponse:
        """Handle all SajuBaseException domain errors.

        Returns RFC7807 Problem Details JSON with correlation ID.
        """
        correlation_id = getattr(exc, "correlation_id", None)

        # Add correlation ID to request state for logging middleware
        if correlation_id and hasattr(request.state, "correlation_id"):
            request.state.correlation_id = correlation_id

        logger.warning(
            f"{exc.__class__.__name__}: {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "status_code": exc.status_code,
                "error_type": exc.error_type,
                "path": request.url.path,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_rfc7807(),
            headers={"X-Correlation-ID": correlation_id} if correlation_id else {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI request validation errors.

        Converts Pydantic validation errors to RFC7807 format.
        """
        correlation_id = getattr(request.state, "correlation_id", None)

        # Extract validation error details
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Request validation failed: {len(errors)} errors",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "errors": errors,
            },
        )

        # Convert to RFC7807 ValidationError
        validation_error = ValidationError(
            detail=f"Request validation failed with {len(errors)} error(s)",
            correlation_id=correlation_id,
            errors=errors,  # Extension member
        )

        return JSONResponse(
            status_code=validation_error.status_code,
            content=validation_error.to_rfc7807(),
            headers={
                "X-Correlation-ID": correlation_id
            } if correlation_id else {},
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors.

        Converts Pydantic model validation errors to RFC7807 format.
        """
        correlation_id = getattr(request.state, "correlation_id", None)

        # Extract validation error details
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Pydantic validation failed: {len(errors)} errors",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "errors": errors,
            },
        )

        validation_error = ValidationError(
            detail=f"Data validation failed with {len(errors)} error(s)",
            correlation_id=correlation_id,
            errors=errors,
        )

        return JSONResponse(
            status_code=validation_error.status_code,
            content=validation_error.to_rfc7807(),
            headers={
                "X-Correlation-ID": correlation_id
            } if correlation_id else {},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions.

        Converts standard HTTP exceptions to RFC7807 format.
        """
        correlation_id = getattr(request.state, "correlation_id", None)

        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )

        # Create RFC7807 envelope
        error_envelope: Dict[str, Any] = {
            "type": f"https://api.saju.app/errors/http_{exc.status_code}",
            "title": _get_status_title(exc.status_code),
            "status": exc.status_code,
            "detail": str(exc.detail),
        }

        if correlation_id:
            error_envelope["correlation_id"] = correlation_id

        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope,
            headers={
                "X-Correlation-ID": correlation_id
            } if correlation_id else {},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions.

        Catch-all handler for unexpected exceptions. Returns 500 Internal
        Server Error with sanitized error message (no sensitive data).
        """
        correlation_id = getattr(request.state, "correlation_id", None)

        logger.exception(
            f"Unhandled exception: {exc.__class__.__name__}",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "exception_type": exc.__class__.__name__,
            },
        )

        # Create generic RFC7807 envelope (sanitized)
        error_envelope: Dict[str, Any] = {
            "type": "https://api.saju.app/errors/internal_error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
        }

        if correlation_id:
            error_envelope["correlation_id"] = correlation_id

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope,
            headers={
                "X-Correlation-ID": correlation_id
            } if correlation_id else {},
        )


def _get_status_title(status_code: int) -> str:
    """Get human-readable title for HTTP status code.

    Args:
        status_code: HTTP status code

    Returns:
        Human-readable status title
    """
    status_titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return status_titles.get(status_code, f"HTTP {status_code}")
