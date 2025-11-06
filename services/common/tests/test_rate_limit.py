"""Tests for rate limiting module."""

import time

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from saju_common.rate_limit import (
    DEFAULT_RATE_LIMITS,
    RateLimitExceeded,
    RateLimitMiddleware,
    TokenBucketRateLimiter,
    setup_rate_limiting,
)


def test_default_rate_limits():
    """Test that default rate limits are defined."""
    assert "free" in DEFAULT_RATE_LIMITS
    assert "plus" in DEFAULT_RATE_LIMITS
    assert "pro" in DEFAULT_RATE_LIMITS
    assert "anonymous" in DEFAULT_RATE_LIMITS

    assert DEFAULT_RATE_LIMITS["anonymous"] < DEFAULT_RATE_LIMITS["free"]
    assert DEFAULT_RATE_LIMITS["free"] < DEFAULT_RATE_LIMITS["plus"]
    assert DEFAULT_RATE_LIMITS["plus"] < DEFAULT_RATE_LIMITS["pro"]


def test_rate_limit_exceeded_exception():
    """Test RateLimitExceeded exception creation."""
    exc = RateLimitExceeded(limit=10, window=60, retry_after=30)

    assert exc.limit == 10
    assert exc.window == 60
    assert exc.retry_after == 30
    assert "Rate limit exceeded" in str(exc)


def test_token_bucket_initialization():
    """Test TokenBucketRateLimiter initialization."""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

    assert limiter.capacity == 10
    assert limiter.refill_rate == 1.0
    assert limiter.redis_client is None


def test_token_bucket_allows_requests_under_limit():
    """Test that requests under limit are allowed."""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

    # First request should be allowed
    allowed, retry_after = limiter.check_rate_limit("test_key")
    assert allowed is True
    assert retry_after == 0


def test_token_bucket_blocks_requests_over_limit():
    """Test that requests over limit are blocked."""
    limiter = TokenBucketRateLimiter(capacity=2, refill_rate=0.1)  # Very low limit

    # Use up the capacity
    limiter.check_rate_limit("test_key")
    limiter.check_rate_limit("test_key")

    # Third request should be blocked
    allowed, retry_after = limiter.check_rate_limit("test_key")
    assert allowed is False
    assert retry_after > 0


def test_token_bucket_refills_over_time():
    """Test that tokens refill over time."""
    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=10.0)  # Fast refill

    # Use all tokens
    for _ in range(5):
        allowed, _ = limiter.check_rate_limit("test_key")
        assert allowed is True

    # Should be rate limited now
    allowed, _ = limiter.check_rate_limit("test_key")
    assert allowed is False

    # Wait for refill (0.1 seconds = 1 token at 10 tokens/sec)
    time.sleep(0.15)

    # Should be allowed again
    allowed, retry_after = limiter.check_rate_limit("test_key")
    assert allowed is True
    assert retry_after == 0


def test_token_bucket_separate_keys():
    """Test that different keys have separate buckets."""
    limiter = TokenBucketRateLimiter(capacity=1, refill_rate=0.1)

    # First key
    allowed, _ = limiter.check_rate_limit("key1")
    assert allowed is True

    # First key again - should be blocked
    allowed, _ = limiter.check_rate_limit("key1")
    assert allowed is False

    # Second key - should still be allowed
    allowed, _ = limiter.check_rate_limit("key2")
    assert allowed is True


def test_token_bucket_custom_cost():
    """Test token bucket with custom token cost."""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

    # Consume 5 tokens
    allowed, _ = limiter.check_rate_limit("test_key", cost=5)
    assert allowed is True

    # Try to consume 6 more tokens - should fail (only 5 remaining)
    allowed, _ = limiter.check_rate_limit("test_key", cost=6)
    assert allowed is False

    # Consume 5 tokens - should succeed
    allowed, retry_after = limiter.check_rate_limit("test_key", cost=5)
    assert allowed is True
    assert retry_after == 0


def test_setup_rate_limiting_no_redis():
    """Test rate limiting setup without Redis."""
    client = setup_rate_limiting(redis_url=None)
    assert client is None


def test_rate_limit_middleware_basic():
    """Test RateLimitMiddleware basic functionality."""
    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    # Add rate limiting with very low limit
    # Note: 6 requests/min = 0.1 requests/sec, capacity = max(6//6, 5) = 5
    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 6},  # 6 requests/minute, capacity=5
    )

    client = TestClient(app)

    # First 5 requests should succeed (burst capacity)
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200, f"Request {i+1} should succeed"
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rate_limit_middleware_excludes_health():
    """Test that health endpoints are excluded from rate limiting."""
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 1},  # Very low limit
    )

    client = TestClient(app)

    # Health endpoint should never be rate limited
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers


def test_rate_limit_middleware_headers():
    """Test that rate limit headers are added correctly."""
    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 60},  # 60 requests/minute
    )

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_middleware_429_response():
    """Test 429 response format."""
    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 6},  # capacity=5
    )

    client = TestClient(app)

    # Exhaust limit (5 requests for capacity=5)
    for _ in range(5):
        client.get("/test")

    # Get 429 response
    response = client.get("/test")
    assert response.status_code == 429

    data = response.json()
    assert data["type"] == "https://datatracker.ietf.org/doc/html/rfc6585#section-4"
    assert data["title"] == "Too Many Requests"
    assert data["status"] == 429
    assert "Rate limit exceeded" in data["detail"]
    assert "limit" in data
    assert "retry_after" in data

    assert "Retry-After" in response.headers
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_middleware_user_tier():
    """Test rate limiting works with different limits per tier."""

    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={
            "anonymous": 6,   # capacity=5
            "free": 12,       # capacity=5
            "plus": 30,       # capacity=5
            "pro": 60,        # capacity=10
        },
    )

    client = TestClient(app)

    # Test anonymous (capacity=5)
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200, f"Anonymous request {i+1} should succeed"

    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429, "Anonymous request 6 should be rate limited"

    # Verify rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "6"  # Limit is 6 requests/min
    assert "Retry-After" in response.headers


def test_settings_integration():
    """Test rate limiting settings integration."""
    from saju_common.settings import SajuSettings

    settings = SajuSettings()

    # Default should be disabled
    assert settings.enable_rate_limiting is False

    # Redis URL should be optional
    assert settings.redis_url is None


def test_settings_rate_limiting_override(monkeypatch):
    """Test rate limiting can be enabled via environment."""
    monkeypatch.setenv("SAJU_ENABLE_RATE_LIMITING", "true")
    monkeypatch.setenv("SAJU_REDIS_URL", "redis://localhost:6379")

    from saju_common.settings import SajuSettings

    settings = SajuSettings()
    assert settings.enable_rate_limiting is True
    assert settings.redis_url == "redis://localhost:6379"


def test_token_bucket_max_capacity():
    """Test that bucket doesn't exceed max capacity."""
    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=100.0)  # Very fast refill

    # Use one token
    limiter.check_rate_limit("test_key")

    # Wait for refill
    time.sleep(0.1)

    # Should have refilled to capacity (5), not more
    # Try to consume 6 tokens - should fail
    allowed, _ = limiter.check_rate_limit("test_key", cost=6)
    assert allowed is False

    # But 5 tokens should work
    allowed, _ = limiter.check_rate_limit("test_key", cost=5)
    assert allowed is True
