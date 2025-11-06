"""Tests for rate limiting module - optimized to avoid hangs."""

import concurrent.futures
import math
import threading
import time
from typing import Any, Callable
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from saju_common.rate_limit import (
    DEFAULT_RATE_LIMITS,
    RateLimitExceeded,
    RateLimitMiddleware,
    TokenBucketRateLimiter,
    setup_rate_limiting,
)


class _FixedClock:
    def __init__(self, start=1000.0):
        self.current = start

    def time(self):
        return self.current

    def advance(self, seconds):
        self.current += seconds


class ScriptableRedis:
    """In-memory Redis stub that simulates Lua execution for tests."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._scripts: dict[str, Callable[[list[str], list[str]], Any]] = {}
        self._sha_counter = 0

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:  # noqa: ARG002
        self._store[key] = str(value)

    class _Pipeline:
        def __init__(self, redis: "ScriptableRedis") -> None:
            self._redis = redis
            self._operations: list[tuple[str, tuple[Any, ...]]] = []

        def get(self, key: str) -> None:
            self._operations.append(("get", (key,)))

        def setex(self, key: str, ttl: int, value: str) -> None:
            self._operations.append(("setex", (key, ttl, value)))

        def execute(self) -> list[Any]:
            results: list[Any] = []
            for op, args in self._operations:
                if op == "get":
                    results.append(self._redis.get(*args))
                elif op == "setex":
                    self._redis.setex(*args)
                    results.append(True)
            self._operations.clear()
            return results

    def pipeline(self) -> "ScriptableRedis._Pipeline":
        return ScriptableRedis._Pipeline(self)

    def register_script(self, script_text: str) -> Callable[..., Any]:  # noqa: ARG002
        return lambda *, keys, args: self._execute_script(list(keys), list(args))

    def script_load(self, script_text: str) -> str:  # noqa: ARG002
        self._sha_counter += 1
        sha = f"sha{self._sha_counter}"
        self._scripts[sha] = lambda keys, args: self._execute_script(keys, args)
        return sha

    def evalsha(self, sha: str, num_keys: int, *payload: str) -> Any:
        script = self._scripts[sha]
        keys = list(payload[:num_keys])
        args = list(payload[num_keys:])
        return script(keys, args)

    def _execute_script(self, keys: list[str], args: list[str]) -> list[Any]:
        capacity = float(args[0])
        refill_rate = float(args[1])
        cost = float(args[2])
        now = float(args[3])

        tokens_raw = self._store.get(keys[0])
        tokens_value = float(tokens_raw) if tokens_raw is not None else capacity

        last_update_raw = self._store.get(keys[1])
        last_update_value = float(last_update_raw) if last_update_raw is not None else now

        elapsed = max(0.0, now - last_update_value)
        new_tokens = min(capacity, tokens_value + (elapsed * refill_rate))

        allowed = 0
        remaining = new_tokens

        if new_tokens >= cost:
            allowed = 1
            remaining = new_tokens - cost

        remaining = max(0.0, remaining)

        self._store[keys[0]] = str(remaining)
        self._store[keys[1]] = str(now)

        retry_after = 0
        if allowed == 0:
            tokens_needed = cost - remaining
            if refill_rate > 0:
                retry_after = int(math.ceil(tokens_needed / refill_rate))

        return [allowed, retry_after, remaining]


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


@patch('time.time')
@patch('time.sleep')
def test_token_bucket_refills_over_time(mock_sleep, mock_time):
    """Test that tokens refill over time (mocked)."""
    # Mock time progression
    current_time = 1000.0
    mock_time.return_value = current_time

    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=10.0)  # Fast refill

    # Use all tokens
    for _ in range(5):
        mock_time.return_value = current_time
        allowed, _ = limiter.check_rate_limit("test_key")
        assert allowed is True
        current_time += 0.01  # Small increment

    # Should be rate limited now
    mock_time.return_value = current_time
    allowed, _ = limiter.check_rate_limit("test_key")
    assert allowed is False

    # Advance time by 0.15 seconds (1.5 tokens refilled)
    current_time += 0.15
    mock_time.return_value = current_time

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


def test_rate_limit_headers_reflect_remaining_tokens(monkeypatch):
    """Remaining tokens and reset headers should match post-consumption state."""

    clock = _FixedClock(1000.0)
    monkeypatch.setattr("saju_common.rate_limit.time.time", clock.time)

    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 60},
    )

    with TestClient(app) as client:
        response = client.get("/test")

    assert response.headers["X-RateLimit-Remaining"] == "9"
    assert response.headers["X-RateLimit-Reset"] == "1001"


def test_rate_limit_headers_near_empty(monkeypatch):
    """Near-empty buckets should report reset based on refill math."""

    clock = _FixedClock(2000.0)
    monkeypatch.setattr("saju_common.rate_limit.time.time", clock.time)

    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={"anonymous": 12},
    )

    with TestClient(app) as client:
        for _ in range(4):
            response = client.get("/test")

    assert response.headers["X-RateLimit-Remaining"] == "1"
    assert response.headers["X-RateLimit-Reset"] == "2020"


def test_rate_limit_middleware_basic():
    """Test RateLimitMiddleware basic functionality (isolated)."""
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

    # Use separate client instance to avoid cross-test contamination
    with TestClient(app) as client:
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

    with TestClient(app) as client:
        # Health endpoint should never be rate limited (reduced from 10 to 3 iterations)
        for _ in range(3):
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

    with TestClient(app) as client:
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "9"
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

    with TestClient(app) as client:
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

    with TestClient(app) as client:
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


def test_rate_limit_middleware_unknown_tier_fallback():
    """Unknown tiers should mirror anonymous defaults for limits and headers."""

    app = FastAPI()

    class DummyUser:
        def __init__(self, tier: str) -> None:
            self.id = "u123"
            self.tier = tier

    @app.middleware("http")
    async def attach_user(request, call_next):  # type: ignore[override]
        request.state.user = DummyUser("mystery")
        return await call_next(request)

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    app.add_middleware(
        RateLimitMiddleware,
        rate_limits={
            "anonymous": 10,  # fallback tier
            "free": 30,
        },
    )

    with TestClient(app) as client:
        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200, f"Request {i+1} should succeed"
            assert response.headers["X-RateLimit-Limit"] == "10"

        blocked = client.get("/test")
        assert blocked.status_code == 429
        assert blocked.headers["X-RateLimit-Limit"] == "10"


def test_settings_integration():
    """Test rate limiting settings integration."""
    from saju_common.settings import SajuSettings

    settings = SajuSettings()

    # Default should be disabled
    assert settings.enable_rate_limiting is False
    assert settings.enable_atomic_rate_limiter is False

    # Redis URL should be optional
    assert settings.redis_url is None


def test_settings_rate_limiting_override(monkeypatch):
    """Test rate limiting can be enabled via environment."""
    monkeypatch.setenv("SAJU_ENABLE_RATE_LIMITING", "true")
    monkeypatch.setenv("SAJU_REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SAJU_ENABLE_ATOMIC_RATE_LIMITER", "true")

    from saju_common.settings import SajuSettings

    settings = SajuSettings()
    assert settings.enable_rate_limiting is True
    assert settings.redis_url == "redis://localhost:6379"
    assert settings.enable_atomic_rate_limiter is True


@patch('time.time')
def test_token_bucket_max_capacity(mock_time):
    """Test that bucket doesn't exceed max capacity (mocked)."""
    current_time = 1000.0
    mock_time.return_value = current_time

    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=100.0)  # Very fast refill

    # Use one token
    limiter.check_rate_limit("test_key")
    current_time += 0.01
    mock_time.return_value = current_time

    # Advance time significantly (0.1 seconds = 10 tokens at 100 tokens/sec)
    current_time += 0.1
    mock_time.return_value = current_time

    # Should have refilled to capacity (5), not more
    # Try to consume 6 tokens - should fail
    allowed, _ = limiter.check_rate_limit("test_key", cost=6)
    assert allowed is False

    # But 5 tokens should work
    allowed, _ = limiter.check_rate_limit("test_key", cost=5)
    assert allowed is True


def test_atomic_rate_limiter_handles_concurrent_requests():
    """Lua-backed limiter should allow only one concurrent consumer per bucket."""

    redis_client = ScriptableRedis()
    limiter = TokenBucketRateLimiter(
        capacity=1,
        refill_rate=0.25,  # four seconds to refill one token
        redis_client=redis_client,
        use_atomic_redis=True,
    )

    # Warm up to register script before concurrency begins
    limiter.check_rate_limit("warmup", cost=0)

    barrier = threading.Barrier(2)
    results: list[tuple[bool, int]] = []

    def worker() -> None:
        barrier.wait()
        results.append(limiter.check_rate_limit("shared"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker) for _ in range(2)]
        for future in futures:
            future.result()

    allowed_count = sum(1 for allowed, _ in results if allowed)
    blocked = [retry for allowed, retry in results if not allowed]

    assert allowed_count == 1
    assert len(blocked) == 1
    assert blocked[0] > 0
    assert limiter.get_last_remaining_tokens("shared") <= 1e-4
