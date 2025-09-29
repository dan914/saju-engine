"""Factory helpers for FastAPI services in the 사주 앱 v1.4 suite."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI


def create_service_app(*, app_name: str, version: str, rule_id: str) -> FastAPI:
    """Create a FastAPI application with standard metadata and health endpoints."""
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

    @app.get("/health", tags=["internal"], name="health")
    def health() -> dict[str, Any]:  # pragma: no cover - simple pass-through
        return {"status": "ok", **metadata}

    @app.get("/", tags=["meta"], name="root")
    def root() -> dict[str, Any]:  # pragma: no cover - simple pass-through
        return metadata

    return app
