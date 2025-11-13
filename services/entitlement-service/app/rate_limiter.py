# -*- coding: utf-8 -*-
"""
Redis-based rate limiting
Fixed window rate limiter (can be upgraded to token bucket with Lua script)
"""

from redis.asyncio import Redis


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


async def check_rate_limit(redis: Redis, key: str, limit: int, window_sec: int = 60):
    """
    Check and increment rate limit counter using fixed window algorithm.

    Args:
        redis: Redis client instance
        key: Rate limit key (e.g., "rl:consume:user_id")
        limit: Maximum requests allowed in window
        window_sec: Window duration in seconds (default: 60)

    Raises:
        RateLimitExceeded: If limit is exceeded

    Example:
        await check_rate_limit(redis, f"rl:consume:{user_id}", 10, 60)
    """
    cur = await redis.incr(key)

    if cur == 1:
        # First request in window - set expiry
        await redis.expire(key, window_sec)

    if cur > limit:
        # Rate limit exceeded
        ttl = await redis.ttl(key)
        ttl = max(ttl, 0)  # Handle expired keys
        raise RateLimitExceeded(retry_after=ttl)

    return cur
