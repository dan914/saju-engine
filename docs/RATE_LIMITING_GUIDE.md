# Rate Limiting Guide

This document explains how the token bucket limiter works after the recent
hardening changes, including the Redis credential redaction and the atomic Lua
path.

## Header Semantics

Every response processed by `RateLimitMiddleware` exposes the following RFC
6585-compliant headers:

| Header | Description |
| --- | --- |
| `X-RateLimit-Limit` | Tier-specific configured limit (requests per minute). Unknown tiers fall back to `anonymous`. |
| `X-RateLimit-Remaining` | Tokens remaining after the current request. Derived from the updated token balance, not capacity. |
| `X-RateLimit-Reset` | Epoch seconds when the bucket will refill to capacity: `now + ceil((capacity - remaining)/refill_rate)`. |
| `Retry-After` | Only set on 429 responses; indicates seconds until another request is allowed. |


`X-RateLimit-Remaining` is derived from the current token counter (floored to an integer).
`X-RateLimit-Reset` advances by the exact refill horizon, so a half-empty bucket will report only the
seconds required to regain full capacity rather than the next minute boundary.
## Logging Hygiene

To prevent accidental leakage of Redis credentials, log messages now flow
through `_redact_redis_credentials`. Examples:

```python
logger.info("Rate limiting: Connected to Redis at %s", redis_url)
# -> Rate limiting: Connected to Redis at redis://***@host:6379/0

logger.error("Rate limit check failed: %s", exc)
# Any redis://user:pass@host strings inside `exc` are masked.
```

## Atomic Redis Mode

- Controlled by `SAJU_ENABLE_ATOMIC_RATE_LIMITER` (default `false`).
- When enabled and a Redis client is present, the limiter loads
  `saju_common/token_bucket.lua` and performs an atomic `EVALSHA` per request.
- Fallback: registration failures revert to the pipeline-based implementation
  while logging a warning.

### Lua Script Arguments

1. `capacity` – maximum tokens
2. `refill_rate` – tokens per second
3. `cost` – tokens to consume
4. `now` – current timestamp (float seconds)
5. `ttl` – key TTL (precomputed from capacity/refill rate)

The script returns `[allowed, retry_after, remaining_tokens]`.

## Testing Checklist

- `pytest services/common/tests/test_rate_limit.py` for base behaviours.
- `pytest saju-engine/tests/test_rate_limit.py` for logging redaction coverage.
- Optional: run the load test described in `docs/RATE_LIMIT_LOAD_TEST_PLAN.md`
  to validate atomic mode under concurrent load.

## Operational Guidance

- Always enable staging feature flags first; verify Redis metrics and logs.
- Monitor 429 trends and `X-RateLimit-Remaining` telemetry after deployment.
- Perform a credential audit after rollout to ensure logs remain sanitized.
