"""Test configuration for analysis-service suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def api_client() -> TestClient:
    """Shared FastAPI test client with warmed singletons."""
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
