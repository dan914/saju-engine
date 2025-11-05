"""Factory helpers for FastAPI services in the 사주 앱 v1.4 suite.

Provides standardized FastAPI app creation with:
- RFC7807 exception handlers
- Correlation ID middleware
- Request logging middleware
- Health and metadata endpoints

References:
- Phase 3 Remediation: grand audit/phase3_remediation_plan.md (Week 2)
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

try:
    from .handlers import register_exception_handlers
    from .middleware import add_middleware, configure_logging
except ImportError:
    from handlers import register_exception_handlers
    from middleware import add_middleware, configure_logging


def create_service_app(
    *,
    app_name: str,
    version: str,
    rule_id: str,
    enable_middleware: bool = True,
    enable_handlers: bool = True,
    json_logging: bool = False,
    exclude_logging_paths: list[str] | None = None,
) -> FastAPI:
    """Create a FastAPI application with standard metadata and error handling.

    Args:
        app_name: Service name (e.g., "analysis-service")
        version: Service version (e.g., "1.4.0")
        rule_id: Rule/policy version identifier
        enable_middleware: Enable correlation ID and logging middleware
        enable_handlers: Enable RFC7807 exception handlers
        json_logging: Use JSON logging format (for production)
        exclude_logging_paths: Paths to exclude from request logging

    Returns:
        Configured FastAPI application

    Example:
        >>> from services.common.app_factory import create_service_app
        >>> app = create_service_app(
        ...     app_name="analysis-service",
        ...     version="1.4.0",
        ...     rule_id="v2.6",
        ...     json_logging=False,  # Development mode
        ... )
    """
    metadata: dict[str, Any] = {
        "app": app_name,
        "version": version,
        "rule_id": rule_id,
    }

    app = FastAPI(
        title=f"사주 앱 v1.4 — {app_name}",
        version=version,
        summary=f"{app_name} service",
        contact={"name": "Codex Team"},
    )

    # Configure logging
    configure_logging(json_format=json_logging)

    # Register exception handlers
    if enable_handlers:
        register_exception_handlers(app)

    # Add middleware (correlation ID + request logging)
    if enable_middleware:
        add_middleware(
            app,
            exclude_logging_paths=exclude_logging_paths or ["/health", "/"],
        )

    # Standard health endpoint
    @app.get("/health", tags=["internal"], name="health")
    def health() -> dict[str, Any]:  # pragma: no cover - simple pass-through
        return {"status": "ok", **metadata}

    # Metadata endpoint
    @app.get("/", tags=["meta"], name="root")
    def root() -> dict[str, Any]:  # pragma: no cover - simple pass-through
        return metadata

    return app
