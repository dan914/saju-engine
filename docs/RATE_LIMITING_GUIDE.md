## Rate Limiting Guide

**Created:** 2025-11-06
**Version:** 1.0
**Related:** Week 4 Task 8 - Implement gateway rate limiting

## Overview

The saju-engine project includes comprehensive rate limiting infrastructure using the token bucket algorithm with optional Redis backend for distributed coordination.

### Features

- **Token Bucket Algorithm** - Smooth rate limiting with burst capacity
- **Distributed Coordination** - Redis backend for multi-instance deployments
- **Tier-Based Limits** - Different limits for free, plus, pro, and anonymous users
- **Graceful Degradation** - Falls back to in-memory when Redis unavailable
- **RFC 6585 Compliance** - Standard 429 Too Many Requests responses
- **Rate Limit Headers** - X-RateLimit-* headers for client awareness

## Architecture

```
┌─────────────────────────────────────────────────┐
│              API Gateway                         │
│  ┌─────────────────────────────────────────┐   │
│  │     RateLimitMiddleware                  │   │
│  │  ┌────────────┐  ┌────────────────────┐ │   │
│  │  │ Get User   │→ │ TokenBucket        │ │   │
│  │  │ Tier       │  │ RateLimiter        │ │   │
│  │  └────────────┘  └────┬───────────────┘ │   │
│  └───────────────────────┼──────────────────┘   │
└──────────────────────────┼──────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         ↓                                   ↓
    ┌─────────┐                        ┌──────────┐
    │  Redis  │ (distributed)          │ In-Memory│ (fallback)
    │ Backend │                        │  Buckets │
    └─────────┘                        └──────────┘
```

## Quick Start

### 1. Enable Rate Limiting

**Via Environment Variables:**
```bash
export SAJU_ENABLE_RATE_LIMITING=true
export SAJU_REDIS_URL=redis://localhost:6379
```

**Via Settings:**
```python
from saju_common import settings

settings.enable_rate_limiting = True
settings.redis_url = "redis://localhost:6379"
```

### 2. Initialize in Application

```python
from fastapi import FastAPI
from saju_common import RateLimitMiddleware, setup_rate_limiting

app = FastAPI()

# Option 1: With Redis (distributed)
redis_client = setup_rate_limiting("redis://localhost:6379")
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

# Option 2: Without Redis (single instance)
app.add_middleware(RateLimitMiddleware)
```

### 3. Customize Rate Limits

```python
from saju_common import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_client,
    rate_limits={
        "anonymous": 10,   # 10 requests/minute
        "free": 60,        # 60 requests/minute
        "plus": 300,       # 300 requests/minute
        "pro": 600,        # 600 requests/minute
    },
    exclude_paths=["/health", "/metrics", "/"],
)
```

## Token Bucket Algorithm

### How It Works

The token bucket algorithm provides smooth rate limiting:

1. **Bucket Initialization**: Each user/IP gets a bucket with maximum capacity
2. **Token Refill**: Tokens are added to the bucket at a fixed rate (e.g., 1 token/second)
3. **Request Consumption**: Each request consumes 1 token
4. **Allow/Deny**: Request allowed if tokens available, denied otherwise

### Burst Capacity

The algorithm allows for short bursts:

```python
# 60 requests/minute = 1 request/second
# Capacity = max(60/6, 5) = 10 tokens

# Allows burst of 10 requests immediately
# Then refills at 1 token/second (60/minute)
```

### Example Behavior

```
Time    Tokens  Action          Result
0s      10      Request         ✓ (9 left)
0.1s    9       Request         ✓ (8 left)
0.2s    8       Request         ✓ (7 left)
...
1.0s    1       Request         ✓ (0 left)
1.1s    0       Request         ✗ Rate Limited
2.0s    1       (refilled)
2.1s    1       Request         ✓ (0 left)
```

## Default Rate Limits

```python
DEFAULT_RATE_LIMITS = {
    "anonymous": 5,    # 5 requests/minute  (unauthenticated)
    "free": 10,        # 10 requests/minute (free tier)
    "plus": 60,        # 60 requests/minute (plus tier)
    "pro": 300,        # 300 requests/minute (pro tier)
}
```

### Capacity Calculation

```python
capacity = max(limit_per_minute // 6, 5)

# Examples:
# 60/min  → capacity = max(10, 5) = 10
# 300/min → capacity = max(50, 5) = 50
# 6/min   → capacity = max(1, 5) = 5
```

## Rate Limit Headers

### Request Headers (Optional)

Clients can send correlation for tracking:
```http
GET /api/endpoint HTTP/1.1
X-Correlation-ID: custom-id-12345
```

### Response Headers (Always)

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1699228800
X-Correlation-ID: custom-id-12345
X-Response-Time: 145.23ms
```

### 429 Response Headers

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699228860
Retry-After: 30
Content-Type: application/json

{
  "type": "https://datatracker.ietf.org/doc/html/rfc6585#section-4",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit exceeded. Please retry after 30 seconds.",
  "instance": "/api/endpoint",
  "limit": 60,
  "window": 60,
  "retry_after": 30
}
```

## Redis Backend

### Setup Redis

**Docker:**
```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

**Docker Compose:**
```yaml
version: '3'
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-data:
```

### Redis Key Structure

```
ratelimit:{key}:tokens   → Current token count
ratelimit:{key}:time     → Last update timestamp

# Examples:
ratelimit:user:123:tokens     → "8.5"
ratelimit:user:123:time       → "1699228845.123"
ratelimit:ip:192.168.1.1:tokens → "5.0"
ratelimit:ip:192.168.1.1:time   → "1699228850.456"
```

### Redis Connection

```python
from saju_common import setup_rate_limiting

# Basic connection
redis_client = setup_rate_limiting("redis://localhost:6379")

# With password
redis_client = setup_rate_limiting("redis://:password@localhost:6379")

# With database selection
redis_client = setup_rate_limiting("redis://localhost:6379/1")

# Redis Sentinel
redis_client = setup_rate_limiting("redis+sentinel://localhost:26379/mymaster")
```

## User Tier Detection

The middleware automatically detects user tier from `request.state.user`:

```python
from fastapi import Request, Depends

# Your authentication dependency
async def get_current_user(request: Request):
    # Your auth logic here
    user = authenticate(request)
    return user

@app.get("/protected")
async def protected_endpoint(user=Depends(get_current_user), request: Request):
    # Set user in request state (middleware reads this)
    request.state.user = user

    # User object should have:
    # - id: str (unique identifier)
    # - tier: str (one of: "free", "plus", "pro")

    return {"user": user.tier}
```

### Tier Resolution Logic

```python
def _get_user_tier(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if not user:
        return "anonymous"

    return getattr(user, "tier", "free")
```

### Key Generation Logic

```python
def _get_rate_limit_key(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"  # Authenticated

    client_ip = request.client.host if request.client else "testclient"
    return f"ip:{client_ip}"  # Anonymous
```

## Advanced Usage

### Custom Token Cost

```python
from saju_common import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(capacity=100, refill_rate=1.0)

# Normal request (1 token)
allowed, retry_after = limiter.check_rate_limit("user:123")

# Expensive operation (10 tokens)
allowed, retry_after = limiter.check_rate_limit("user:123", cost=10)
```

### Programmatic Rate Limit Checks

```python
from fastapi import Request, HTTPException
from saju_common import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

@app.post("/expensive-operation")
async def expensive_operation(request: Request):
    user_id = request.state.user.id

    # Check if user can perform expensive operation
    allowed, retry_after = limiter.check_rate_limit(
        f"user:{user_id}:expensive",
        cost=5  # Costs 5 tokens
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after}s",
            headers={"Retry-After": str(retry_after)}
        )

    # Perform expensive operation
    return {"status": "processing"}
```

### Multiple Rate Limiters

```python
from saju_common import TokenBucketRateLimiter

# Per-user limiter (60/min)
user_limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)

# Global limiter (1000/min for entire service)
global_limiter = TokenBucketRateLimiter(capacity=100, refill_rate=16.67)

@app.post("/api/endpoint")
async def endpoint(request: Request):
    user_id = request.state.user.id

    # Check global limit first
    allowed, _ = global_limiter.check_rate_limit("global")
    if not allowed:
        raise HTTPException(429, "Service rate limit exceeded")

    # Check per-user limit
    allowed, retry_after = user_limiter.check_rate_limit(f"user:{user_id}")
    if not allowed:
        raise HTTPException(429, f"User rate limit exceeded. Retry in {retry_after}s")

    return {"status": "ok"}
```

## Monitoring & Debugging

### Enable Debug Logging

```python
import logging

logging.getLogger("saju_common.rate_limit").setLevel(logging.DEBUG)
```

### Check Redis State

```bash
# Connect to Redis
redis-cli

# List all rate limit keys
KEYS ratelimit:*

# Check specific user's tokens
GET ratelimit:user:123:tokens
GET ratelimit:user:123:time

# Monitor rate limit activity
MONITOR
```

### Metrics to Track

1. **Rate Limit Hit Rate**: % of requests that hit 429
2. **Retry-After Distribution**: How long users wait
3. **Tier Distribution**: Requests per tier
4. **Redis Performance**: Connection pool usage

## Testing

### Unit Tests

```python
from saju_common import TokenBucketRateLimiter

def test_rate_limiting():
    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=1.0)

    # First 5 requests allowed
    for _ in range(5):
        allowed, _ = limiter.check_rate_limit("test_key")
        assert allowed is True

    # 6th request blocked
    allowed, retry_after = limiter.check_rate_limit("test_key")
    assert allowed is False
    assert retry_after > 0
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_rate_limit_middleware():
    client = TestClient(app)

    # Make requests until rate limited
    for i in range(10):
        response = client.get("/api/endpoint")
        if response.status_code == 429:
            assert i >= 5  # Hit limit after 5+ requests
            assert "Retry-After" in response.headers
            break
```

## Production Deployment

### Recommended Configuration

```bash
# Enable rate limiting
export SAJU_ENABLE_RATE_LIMITING=true

# Redis for distributed rate limiting
export SAJU_REDIS_URL=redis://redis-cluster:6379

# Custom rate limits
export RATE_LIMIT_ANONYMOUS=5
export RATE_LIMIT_FREE=10
export RATE_LIMIT_PLUS=60
export RATE_LIMIT_PRO=300
```

### Docker Compose Example

```yaml
version: '3'
services:
  api-gateway:
    image: saju-gateway:latest
    environment:
      - SAJU_ENABLE_RATE_LIMITING=true
      - SAJU_REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:latest
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  redis-data:
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rate-limit-config
data:
  SAJU_ENABLE_RATE_LIMITING: "true"
  SAJU_REDIS_URL: "redis://redis-service:6379"
  RATE_LIMIT_ANONYMOUS: "5"
  RATE_LIMIT_FREE: "10"
  RATE_LIMIT_PLUS: "60"
  RATE_LIMIT_PRO: "300"
```

## Troubleshooting

### Rate Limiting Not Working

**Check Settings:**
```python
from saju_common import settings

print(f"Rate limiting enabled: {settings.enable_rate_limiting}")
print(f"Redis URL: {settings.redis_url}")
```

**Check Redis Connection:**
```python
from saju_common import setup_rate_limiting

redis_client = setup_rate_limiting("redis://localhost:6379")
if redis_client:
    print("Redis connected")
else:
    print("Redis connection failed - using local fallback")
```

### Inconsistent Rate Limits

**Problem**: Different limits on different instances

**Solution**: Ensure all instances use same Redis backend

```python
# All instances must point to same Redis
redis_client = setup_rate_limiting("redis://shared-redis:6379")
```

### Redis Memory Issues

**Problem**: Redis running out of memory

**Solution**: Configure eviction policy

```bash
# Redis configuration
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### High Latency

**Problem**: Rate limiting adds latency

**Optimization**:
```python
# Use connection pooling
import redis

pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=pool)
```

## Best Practices

1. **Always Use Redis in Production** - Local fallback is for development only
2. **Set Appropriate Limits** - Balance user experience with resource protection
3. **Monitor 429 Rates** - High rates indicate limits too strict
4. **Exclude Health Checks** - Don't rate limit monitoring endpoints
5. **Log Rate Limit Events** - Track when users hit limits
6. **Provide Clear Retry-After** - Help clients back off gracefully
7. **Consider Burst Capacity** - Allow short bursts for better UX

## Further Reading

- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [RFC 6585 - Additional HTTP Status Codes](https://datatracker.ietf.org/doc/html/rfc6585)
- [Redis Rate Limiting Patterns](https://redis.io/docs/manual/patterns/rate-limiter/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/advanced/middleware/)

---

**Version:** 1.0
**Last Updated:** 2025-11-06
**Maintainer:** Backend Infrastructure Team
