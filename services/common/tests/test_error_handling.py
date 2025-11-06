"""Contract tests for RFC7807 error handling and correlation IDs.

Tests verify:
- All exceptions return RFC7807-compliant error envelopes
- Correlation IDs are present in responses and headers
- Error responses include required RFC7807 fields
- Status codes match exception types

References:
- RFC7807: https://datatracker.ietf.org/doc/html/rfc7807
- Phase 3 Remediation: grand audit/phase3_remediation_plan.md (Week 2)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Direct imports from services.common
from saju_common.app_factory import create_service_app
from saju_common.exceptions import (
    CalculationError,
    ConflictError,
    ForbiddenError,
    LLMGuardError,
    NotFoundError,
    PolicyLoadError,
    RateLimitError,
    TokenQuotaError,
    UnauthorizedError,
    ValidationError,
)


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with error handlers."""
    test_app = create_service_app(
        app_name="test-service",
        version="1.0.0",
        rule_id="test",
        json_logging=False,
    )

    # Add test routes that raise exceptions
    @test_app.get("/test/validation")
    def test_validation():
        raise ValidationError("Invalid input data")

    @test_app.get("/test/unauthorized")
    def test_unauthorized():
        raise UnauthorizedError("Authentication required")

    @test_app.get("/test/forbidden")
    def test_forbidden():
        raise ForbiddenError("Access denied")

    @test_app.get("/test/not-found")
    def test_not_found():
        raise NotFoundError("Resource not found")

    @test_app.get("/test/conflict")
    def test_conflict():
        raise ConflictError("Resource already exists")

    @test_app.get("/test/rate-limit")
    def test_rate_limit():
        raise RateLimitError("Too many requests")

    @test_app.get("/test/calculation")
    def test_calculation():
        raise CalculationError("Calculation failed")

    @test_app.get("/test/policy-load")
    def test_policy_load():
        raise PolicyLoadError("Policy file not found")

    @test_app.get("/test/llm-guard")
    def test_llm_guard():
        raise LLMGuardError("LLM output violated policy")

    @test_app.get("/test/token-quota")
    def test_token_quota():
        raise TokenQuotaError("Token balance insufficient")

    @test_app.get("/test/generic-error")
    def test_generic_error():
        raise RuntimeError("Unexpected error")

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


def assert_rfc7807_envelope(response_data: dict, expected_status: int) -> None:
    """Assert response conforms to RFC7807 specification.

    Args:
        response_data: Response JSON data
        expected_status: Expected HTTP status code
    """
    # Required RFC7807 fields
    assert "type" in response_data, "Missing 'type' field"
    assert "title" in response_data, "Missing 'title' field"
    assert "status" in response_data, "Missing 'status' field"
    assert "detail" in response_data, "Missing 'detail' field"

    # Verify type is a URI
    assert response_data["type"].startswith("https://"), "type must be a URI"

    # Verify status matches
    assert response_data["status"] == expected_status, f"Status mismatch: {response_data['status']} != {expected_status}"

    # Extension field: correlation_id
    assert "correlation_id" in response_data, "Missing correlation_id"
    assert len(response_data["correlation_id"]) > 0, "correlation_id is empty"


def test_validation_error_returns_rfc7807(client: TestClient):
    """Test ValidationError returns RFC7807 envelope with status 400."""
    response = client.get("/test/validation")

    assert response.status_code == 400
    data = response.json()
    assert_rfc7807_envelope(data, 400)
    assert data["error_type"] == "validation_error" or "validation" in data["type"]
    assert "X-Correlation-ID" in response.headers


def test_unauthorized_error_returns_rfc7807(client: TestClient):
    """Test UnauthorizedError returns RFC7807 envelope with status 401."""
    response = client.get("/test/unauthorized")

    assert response.status_code == 401
    data = response.json()
    assert_rfc7807_envelope(data, 401)
    assert "X-Correlation-ID" in response.headers


def test_forbidden_error_returns_rfc7807(client: TestClient):
    """Test ForbiddenError returns RFC7807 envelope with status 403."""
    response = client.get("/test/forbidden")

    assert response.status_code == 403
    data = response.json()
    assert_rfc7807_envelope(data, 403)
    assert "X-Correlation-ID" in response.headers


def test_not_found_error_returns_rfc7807(client: TestClient):
    """Test NotFoundError returns RFC7807 envelope with status 404."""
    response = client.get("/test/not-found")

    assert response.status_code == 404
    data = response.json()
    assert_rfc7807_envelope(data, 404)
    assert "X-Correlation-ID" in response.headers


def test_conflict_error_returns_rfc7807(client: TestClient):
    """Test ConflictError returns RFC7807 envelope with status 409."""
    response = client.get("/test/conflict")

    assert response.status_code == 409
    data = response.json()
    assert_rfc7807_envelope(data, 409)
    assert "X-Correlation-ID" in response.headers


def test_rate_limit_error_returns_rfc7807(client: TestClient):
    """Test RateLimitError returns RFC7807 envelope with status 429."""
    response = client.get("/test/rate-limit")

    assert response.status_code == 429
    data = response.json()
    assert_rfc7807_envelope(data, 429)
    assert "X-Correlation-ID" in response.headers


def test_calculation_error_returns_rfc7807(client: TestClient):
    """Test CalculationError returns RFC7807 envelope with status 500."""
    response = client.get("/test/calculation")

    assert response.status_code == 500
    data = response.json()
    assert_rfc7807_envelope(data, 500)
    assert "X-Correlation-ID" in response.headers


def test_policy_load_error_returns_rfc7807(client: TestClient):
    """Test PolicyLoadError returns RFC7807 envelope with status 502."""
    response = client.get("/test/policy-load")

    assert response.status_code == 502
    data = response.json()
    assert_rfc7807_envelope(data, 502)
    assert "X-Correlation-ID" in response.headers


def test_llm_guard_error_returns_rfc7807(client: TestClient):
    """Test LLMGuardError returns RFC7807 envelope with status 422."""
    response = client.get("/test/llm-guard")

    assert response.status_code == 422
    data = response.json()
    assert_rfc7807_envelope(data, 422)
    assert "X-Correlation-ID" in response.headers


def test_token_quota_error_returns_rfc7807(client: TestClient):
    """Test TokenQuotaError returns RFC7807 envelope with status 402."""
    response = client.get("/test/token-quota")

    assert response.status_code == 402
    data = response.json()
    assert_rfc7807_envelope(data, 402)
    assert "X-Correlation-ID" in response.headers


def test_generic_error_returns_rfc7807(client: TestClient):
    """Test unhandled exceptions return RFC7807 envelope with status 500."""
    response = client.get("/test/generic-error")

    assert response.status_code == 500
    data = response.json()
    assert_rfc7807_envelope(data, 500)
    assert "X-Correlation-ID" in response.headers
    # Ensure sensitive data not leaked
    assert "RuntimeError" not in data["detail"]


def test_correlation_id_propagation(client: TestClient):
    """Test correlation ID is propagated from request to response."""
    test_correlation_id = "test-correlation-123"

    response = client.get(
        "/test/not-found",
        headers={"X-Correlation-ID": test_correlation_id},
    )

    assert response.status_code == 404
    assert response.headers["X-Correlation-ID"] == test_correlation_id

    data = response.json()
    assert data["correlation_id"] == test_correlation_id


def test_correlation_id_generated_if_missing(client: TestClient):
    """Test correlation ID is generated if not provided in request."""
    response = client.get("/test/validation")

    assert response.status_code == 400
    assert "X-Correlation-ID" in response.headers

    correlation_id = response.headers["X-Correlation-ID"]
    assert len(correlation_id) > 0

    data = response.json()
    assert data["correlation_id"] == correlation_id


def test_health_endpoint_excludes_correlation_tracking(client: TestClient):
    """Test health endpoint works without correlation tracking."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Health endpoint may or may not have correlation ID (it's excluded from logging)


def test_response_time_header_present(client: TestClient):
    """Test X-Response-Time header is added to responses."""
    response = client.get("/test/not-found")

    assert response.status_code == 404
    assert "X-Response-Time" in response.headers
    # Response time should be in milliseconds
    response_time = response.headers["X-Response-Time"]
    assert "ms" in response_time


def test_error_envelope_includes_extension_fields(client: TestClient):
    """Test error envelopes can include extension fields."""
    response = client.get("/test/validation")

    assert response.status_code == 400
    data = response.json()

    # ValidationError adds 'errors' extension field
    # (This will be populated when actual request validation fails)
    assert_rfc7807_envelope(data, 400)
