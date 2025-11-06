"""Shared fixtures for astro-service tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICES_ROOT = PROJECT_ROOT / "services"
COMMON_ROOT = SERVICES_ROOT / "common"
SERVICE_MODULE_ROOT = SERVICES_ROOT / "astro-service"

for candidate in (PROJECT_ROOT, SERVICES_ROOT, COMMON_ROOT, SERVICE_MODULE_ROOT):
    path_str = str(candidate.resolve())
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def api_client() -> TestClient:
    """Session-scoped TestClient for astro-service."""
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
