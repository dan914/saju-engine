"""Rate limiting middleware for API gateway and services.

This module provides rate limiting functionality using the token bucket algorithm
with Redis backend for distributed rate limiting across multiple service instances.

Features:
- Token bucket algorithm for smooth rate limiting
- Redis backend for distributed coordination
- Per-user, per-IP, and global rate limits
- Configurable limits via settings
- Graceful degradation when Redis unavailable
- Support for different rate limit tiers (free, plus, pro)

Configuration:
    Enable rate limiting via settings:
    >>> from saju_common import settings
    >>> settings.enable_rate_limiting = True
    >>> settings.redis_url = "redis://localhost:6379"

Usage:
    >>> from saju_common.rate_limit import RateLimitMiddleware
    >>> from fastapi import FastAPI
    >>> app = FastAPI()
    >>> app.add_middleware(RateLimitMiddleware)

References:
- Week 4 Task 8: Implement gateway rate limiting
- Token bucket algorithm: https://en.wikipedia.org/wiki/Token_bucket
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Rate limit defaults (requests per minute)
DEFAULT_RATE_LIMITS = {
    "free": 10,      # 10 requests/minute
    "plus": 60,      # 60 requests/minute
    "pro": 300,      # 300 requests/minute
    "anonymous": 5,  # 5 requests/minute for unauthenticated
}


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window: int,
        retry_after: int,
        message: Optional[str] = None,
    ):
        """Initialize rate limit exception.

        Args:
            limit: Maximum requests allowed in window
            window: Time window in seconds
            retry_after: Seconds until next request allowed
            message: Optional custom message
        """
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        self.message = message or f"Rate limit exceeded: {limit} requests per {window}s"
        super().__init__(self.message)


class TokenBucketRateLimiter:
    """Token bucket rate limiter with Redis backend.

    The token bucket algorithm allows for burst traffic while maintaining
    an average rate limit. Tokens are added to the bucket at a fixed rate,
    and each request consumes one token.

    Attributes:
        capacity: Maximum tokens in bucket (burst capacity)
        refill_rate: Tokens added per second
        redis_client: Optional Redis client for distributed limiting
    """

    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        redis_client: Optional[object] = None,
    ):
        """Initialize token bucket rate limiter.

        Args:
            capacity: Maximum tokens (allows burst of this many requests)
            refill_rate: Tokens refilled per second (average rate limit)
            redis_client: Optional Redis client for distributed limiting
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.redis_client = redis_client

        # In-memory fallback when Redis unavailable
        self._local_buckets: dict[str, dict] = {}

    def _get_bucket_redis(self, key: str) -> tuple[float, float]:
        """Get bucket state from Redis.

        Args:
            key: Unique identifier for this bucket (e.g., "user:123")

        Returns:
            Tuple of (tokens, last_update_time)
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not available")

        pipeline = self.redis_client.pipeline()
        tokens_key = f"ratelimit:{key}:tokens"
        time_key = f"ratelimit:{key}:time"

        pipeline.get(tokens_key)
        pipeline.get(time_key)
        results = pipeline.execute()

        if results[0] is None:
            # Initialize new bucket
            return float(self.capacity), time.time()

        tokens = float(results[0])
        last_update = float(results[1])
        return tokens, last_update

    def _set_bucket_redis(self, key: str, tokens: float, last_update: float) -> None:
        """Set bucket state in Redis.

        Args:
            key: Unique identifier for this bucket
            tokens: Current token count
            last_update: Last update timestamp
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not available")

        pipeline = self.redis_client.pipeline()
        tokens_key = f"ratelimit:{key}:tokens"
        time_key = f"ratelimit:{key}:time"

        # Set with expiry (2x the refill time for full bucket)
        expiry = int(self.capacity / self.refill_rate * 2)

        pipeline.setex(tokens_key, expiry, str(tokens))
        pipeline.setex(time_key, expiry, str(last_update))
        pipeline.execute()

    def _get_bucket_local(self, key: str) -> tuple[float, float]:
        """Get bucket state from local memory (fallback).

        Args:
            key: Unique identifier for this bucket

        Returns:
            Tuple of (tokens, last_update_time)
        """
        if key not in self._local_buckets:
            return float(self.capacity), time.time()

        bucket = self._local_buckets[key]
        return bucket["tokens"], bucket["last_update"]

    def _set_bucket_local(self, key: str, tokens: float, last_update: float) -> None:
        """Set bucket state in local memory (fallback).

        Args:
            key: Unique identifier for this bucket
            tokens: Current token count
            last_update: Last update timestamp
        """
        self._local_buckets[key] = {
            "tokens": tokens,
            "last_update": last_update,
        }

    def check_rate_limit(self, key: str, cost: int = 1) -> tuple[bool, int]:
        """Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for this bucket (e.g., "user:123" or "ip:1.2.3.4")
            cost: Number of tokens to consume (default: 1)

        Returns:
            Tuple of (allowed, retry_after_seconds)
            - allowed: True if request is allowed, False if rate limited
            - retry_after_seconds: Seconds to wait before next request (0 if allowed)

        Example:
            >>> limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
            >>> allowed, retry_after = limiter.check_rate_limit("user:123")
            >>> if not allowed:
            >>>     raise RateLimitExceeded(10, 60, retry_after)
        """
        try:
            # Try Redis first
            if self.redis_client:
                tokens, last_update = self._get_bucket_redis(key)
            else:
                tokens, last_update = self._get_bucket_local(key)

            # Calculate tokens to add since last update
            now = time.time()
            elapsed = now - last_update
            tokens_to_add = elapsed * self.refill_rate
            new_tokens = min(self.capacity, tokens + tokens_to_add)

            # Check if enough tokens available
            if new_tokens >= cost:
                # Consume tokens and allow request
                new_tokens -= cost

                if self.redis_client:
                    self._set_bucket_redis(key, new_tokens, now)
                else:
                    self._set_bucket_local(key, new_tokens, now)

                return True, 0

            # Not enough tokens - calculate retry time
            tokens_needed = cost - new_tokens
            retry_after = int(tokens_needed / self.refill_rate) + 1

            return False, retry_after

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting.

    This middleware:
    - Enforces rate limits based on user tier or IP address
    - Uses token bucket algorithm for smooth limiting
    - Adds rate limit headers to responses
    - Returns 429 Too Many Requests when limit exceeded
    - Gracefully degrades when Redis unavailable

    Example:
        >>> from fastapi import FastAPI
        >>> from saju_common.rate_limit import RateLimitMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(RateLimitMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis_client: Optional[object] = None,
        rate_limits: Optional[dict[str, int]] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        """Initialize rate limiting middleware.

        Args:
            app: ASGI application
            redis_client: Optional Redis client for distributed limiting
            rate_limits: Optional custom rate limits (requests per minute)
            exclude_paths: Paths to exclude from rate limiting (e.g., /health)
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limits = rate_limits or DEFAULT_RATE_LIMITS
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics", "/"])

        # Create rate limiters for each tier
        self._limiters: dict[str, TokenBucketRateLimiter] = {}
        for tier, limit_per_minute in self.rate_limits.items():
            # Convert per-minute limit to per-second refill rate
            refill_rate = limit_per_minute / 60.0
            capacity = max(limit_per_minute // 6, 5)  # Allow small bursts

            self._limiters[tier] = TokenBucketRateLimiter(
                capacity=capacity,
                refill_rate=refill_rate,
                redis_client=redis_client,
            )

    def _get_user_tier(self, request: Request) -> str:
        """Extract user tier from request.

        Args:
            request: Incoming HTTP request

        Returns:
            User tier (free, plus, pro, or anonymous)
        """
        # Check if user is authenticated
        user = getattr(request.state, "user", None)
        if not user:
            return "anonymous"

        # Extract tier from user object
        return getattr(user, "tier", "free")

    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate unique rate limit key for request.

        Args:
            request: Incoming HTTP request

        Returns:
            Unique key for rate limiting (e.g., "user:123" or "ip:1.2.3.4")
        """
        # Use user ID if authenticated
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        # Fall back to IP address
        if request.client and request.client.host:
            client_ip = request.client.host
        else:
            # Fallback for test clients or missing client info
            client_ip = "testclient"

        return f"ip:{client_ip}"

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and enforce rate limits.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response (200 OK or 429 Too Many Requests)
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get user tier and rate limit key
        tier = self._get_user_tier(request)
        key = self._get_rate_limit_key(request)

        # Get limiter for this tier
        limiter = self._limiters.get(tier, self._limiters["anonymous"])

        # Check rate limit
        allowed, retry_after = limiter.check_rate_limit(key)

        # Add rate limit headers
        limit = self.rate_limits[tier]
        remaining = int(limiter.capacity) if allowed else 0

        if not allowed:
            # Rate limit exceeded - return 429
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "type": "https://datatracker.ietf.org/doc/html/rfc6585#section-4",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                    "instance": request.url.path,
                    "limit": limit,
                    "window": 60,
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                    "Retry-After": str(retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + (60 - (time.time() % 60)))
        )

        return response


def setup_rate_limiting(
    redis_url: Optional[str] = None,
    rate_limits: Optional[dict[str, int]] = None,
) -> Optional[object]:
    """Initialize Redis client for rate limiting.

    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379")
        rate_limits: Optional custom rate limits

    Returns:
        Redis client if successful, None otherwise

    Example:
        >>> redis_client = setup_rate_limiting("redis://localhost:6379")
        >>> app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
    """
    if not redis_url:
        logger.info("Rate limiting: Redis URL not provided, using local fallback")
        return None

    try:
        import redis

        client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        client.ping()
        logger.info(f"Rate limiting: Connected to Redis at {redis_url}")
        return client

    except ImportError:
        logger.warning(
            "Rate limiting: redis package not installed. "
            "Install with: pip install redis"
        )
        return None

    except Exception as e:
        logger.warning(f"Rate limiting: Failed to connect to Redis: {e}")
        return None


# Convenience exports
__all__ = [
    "RateLimitMiddleware",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "setup_rate_limiting",
    "DEFAULT_RATE_LIMITS",
]
