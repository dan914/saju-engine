"""Domain exceptions and RFC7807 error envelope for 사주 앱 services.

This module provides:
- Domain-specific exception hierarchy
- RFC7807 Problem Details error envelope
- Correlation ID support for traceability
- FastAPI exception handlers

References:
- RFC7807: https://datatracker.ietf.org/doc/html/rfc7807
- Phase 3 Remediation: grand audit/phase3_remediation_plan.md (Week 2)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4


class SajuBaseException(Exception):
    """Base exception for all 사주 앱 domain errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling and RFC7807 envelope generation.
    """

    status_code: int = 500
    error_type: str = "internal_error"
    title: str = "Internal Server Error"

    def __init__(
        self,
        detail: str,
        *,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        title: Optional[str] = None,
        correlation_id: Optional[str] = None,
        instance: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize exception with RFC7807 fields.

        Args:
            detail: Human-readable explanation specific to this occurrence
            status_code: HTTP status code (overrides class default)
            error_type: URI identifying the problem type (overrides class default)
            title: Short, human-readable summary (overrides class default)
            correlation_id: Request correlation ID for tracing
            instance: URI reference identifying the specific occurrence
            **kwargs: Additional extension members for RFC7807 envelope
        """
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code or self.__class__.status_code
        self.error_type = error_type or self.__class__.error_type
        self.title = title or self.__class__.title
        self.correlation_id = correlation_id or str(uuid4())
        self.instance = instance
        self.extensions = kwargs

    def to_rfc7807(self) -> Dict[str, Any]:
        """Convert exception to RFC7807 Problem Details JSON.

        Returns:
            Dictionary conforming to RFC7807 specification with:
            - type: URI identifying the problem type
            - title: Short, human-readable summary
            - status: HTTP status code
            - detail: Human-readable explanation
            - instance: URI reference to specific occurrence
            - correlation_id: Request correlation ID (extension)
            - Additional extension members from self.extensions
        """
        envelope: Dict[str, Any] = {
            "type": f"https://api.saju.app/errors/{self.error_type}",
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }

        if self.instance:
            envelope["instance"] = self.instance

        # Add correlation ID for traceability
        envelope["correlation_id"] = self.correlation_id

        # Add any extension members
        envelope.update(self.extensions)

        return envelope


# ============================================================================
# Client Error Exceptions (4xx)
# ============================================================================

class ValidationError(SajuBaseException):
    """Request validation failed (400 Bad Request).

    Use when:
    - Required fields are missing
    - Field values are malformed
    - Business rule validation fails
    """

    status_code = 400
    error_type = "validation_error"
    title = "Validation Error"


class UnauthorizedError(SajuBaseException):
    """Authentication required or failed (401 Unauthorized).

    Use when:
    - No authentication credentials provided
    - Invalid or expired authentication token
    - Authentication scheme not supported
    """

    status_code = 401
    error_type = "unauthorized"
    title = "Unauthorized"


class ForbiddenError(SajuBaseException):
    """Authenticated but not authorized (403 Forbidden).

    Use when:
    - User authenticated but lacks permissions
    - Resource access denied by policy
    - Token/entitlement quota exceeded
    """

    status_code = 403
    error_type = "forbidden"
    title = "Forbidden"


class NotFoundError(SajuBaseException):
    """Resource not found (404 Not Found).

    Use when:
    - Requested resource doesn't exist
    - User profile not found
    - Policy file missing
    """

    status_code = 404
    error_type = "not_found"
    title = "Not Found"


class ConflictError(SajuBaseException):
    """Request conflicts with current state (409 Conflict).

    Use when:
    - Resource already exists (duplicate creation)
    - Version conflict (optimistic locking)
    - State transition not allowed
    """

    status_code = 409
    error_type = "conflict"
    title = "Conflict"


class RateLimitError(SajuBaseException):
    """Rate limit exceeded (429 Too Many Requests).

    Use when:
    - API rate limit exceeded
    - Token consumption limit reached
    - Light daily quota exhausted
    """

    status_code = 429
    error_type = "rate_limit_exceeded"
    title = "Rate Limit Exceeded"


# ============================================================================
# Server Error Exceptions (5xx)
# ============================================================================

class InternalError(SajuBaseException):
    """Internal server error (500 Internal Server Error).

    Use when:
    - Unexpected exception occurred
    - System state inconsistent
    - Unhandled error condition
    """

    status_code = 500
    error_type = "internal_error"
    title = "Internal Server Error"


class ServiceUnavailableError(SajuBaseException):
    """Service temporarily unavailable (503 Service Unavailable).

    Use when:
    - Downstream service unavailable
    - Database connection failed
    - Maintenance mode active
    """

    status_code = 503
    error_type = "service_unavailable"
    title = "Service Unavailable"


class DependencyError(SajuBaseException):
    """Dependency service failure (502 Bad Gateway).

    Use when:
    - Upstream service returned error
    - External API call failed
    - Policy file loading failed
    """

    status_code = 502
    error_type = "dependency_error"
    title = "Dependency Error"


# ============================================================================
# Domain-Specific Exceptions
# ============================================================================

class PolicyLoadError(DependencyError):
    """Policy file loading or validation failed.

    Use when:
    - Policy JSON parse error
    - Policy schema validation failed
    - Policy signature verification failed
    """

    error_type = "policy_load_error"
    title = "Policy Load Error"


class CalculationError(InternalError):
    """Calculation engine error (pillars, analysis, luck).

    Use when:
    - Invalid input to calculation engine
    - Calculation logic assertion failed
    - Unexpected calculation result
    """

    error_type = "calculation_error"
    title = "Calculation Error"


class LLMGuardError(ForbiddenError):
    """LLM Guard policy violation.

    Use when:
    - LLM output fails DETERMINISM check
    - TRACE_INTEGRITY violation detected
    - POLICY_BOUND constraint violated
    - HARM_GUARD triggered
    """

    status_code = 422
    error_type = "llm_guard_violation"
    title = "LLM Guard Violation"


class TokenQuotaError(ForbiddenError):
    """Token or entitlement quota exceeded.

    Use when:
    - Deep token balance insufficient
    - Light daily quota exhausted
    - Storage quota exceeded
    """

    status_code = 402
    error_type = "token_quota_exceeded"
    title = "Token Quota Exceeded"


# ============================================================================
# Exception to HTTP Status Code Mapping
# ============================================================================

EXCEPTION_STATUS_MAP: Dict[type, int] = {
    ValidationError: 400,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    RateLimitError: 429,
    InternalError: 500,
    DependencyError: 502,
    ServiceUnavailableError: 503,
    PolicyLoadError: 502,
    CalculationError: 500,
    LLMGuardError: 422,
    TokenQuotaError: 402,
}


def get_status_code(exc: Exception) -> int:
    """Get HTTP status code for exception.

    Args:
        exc: Exception instance

    Returns:
        HTTP status code (defaults to 500 for unknown exceptions)
    """
    if isinstance(exc, SajuBaseException):
        return exc.status_code
    return EXCEPTION_STATUS_MAP.get(type(exc), 500)
