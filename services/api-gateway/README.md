# API Gateway Service - WIP

**Status:** ⚠️ Work In Progress - Not Production Ready

**Version:** 0.1.0-WIP

**Estimated Effort to MVP:** 4-6 hours

---

## Current State

This service is a FastAPI skeleton that provides the basic health check endpoint via `create_service_app()` from `services.common`. It does **NOT** currently implement any business logic for routing requests to downstream services.

**What Works:**
- Health check endpoint (via common service app)
- Basic FastAPI application structure
- Service metadata (app name, version, rule_id)

**What's Missing:**
- All business logic routes
- Authentication/authorization middleware
- Rate limiting
- Request/response logging
- Comprehensive tests
- API documentation

---

## What This Service Should Do

The API Gateway is the single entry point for all client requests. It should:

1. **Route to Analysis Service:**
   - `POST /analyze` → forward to analysis-service
   - Include request validation
   - Handle response transformation

2. **Route to LLM Polish Service:**
   - `POST /chat/send` → forward to llm-polish
   - Manage streaming responses
   - Handle model routing (Light/Deep)

3. **Authentication/Authorization:**
   - Verify user tokens
   - Check entitlements (plan, tokens)
   - Return 401/403 for unauthorized requests

4. **Rate Limiting:**
   - Light chat: 3/day for free users
   - Deep chat: consume tokens
   - Track usage per user

5. **Request/Response Logging:**
   - Log all incoming requests
   - Log response status/latency
   - Track errors and retries

---

## TODO Checklist

- [ ] Add routing to analysis-service
- [ ] Add routing to llm-polish
- [ ] Add authentication/authorization middleware
- [ ] Add rate limiting (by user ID + plan)
- [ ] Add request/response logging
- [ ] Add comprehensive tests (unit + integration)
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Add CORS configuration
- [ ] Add error handling middleware
- [ ] Add health checks for downstream services
- [ ] Add circuit breaker for service failures
- [ ] Add request tracing/correlation IDs

---

## Implementation Notes

### Example: Routing to Analysis Service

```python
from fastapi import APIRouter, Depends, HTTPException
import httpx

router = APIRouter(tags=["analysis"])

@router.post("/analyze")
async def analyze_saju(
    request: AnalysisRequest,
    user_id: str = Depends(get_current_user),
):
    """Forward analysis request to analysis-service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://analysis-service:8000/analyze",
                json=request.dict(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis service error: {str(e)}"
        )
```

### Example: Rate Limiting

```python
from fastapi import Request, HTTPException
from redis import Redis
from datetime import datetime, timedelta

redis_client = Redis(host="redis", port=6379)

async def check_rate_limit(request: Request, user_id: str):
    """Check if user has exceeded rate limit."""
    key = f"rate_limit:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
    current = redis_client.get(key)

    if current and int(current) >= 3:
        raise HTTPException(
            status_code=429,
            detail="Daily light chat limit reached (3/day)"
        )

    redis_client.incr(key)
    redis_client.expire(key, timedelta(days=1))
```

### Example: Authentication Middleware

```python
from fastapi import Header, HTTPException
import jwt

async def get_current_user(authorization: str = Header(...)):
    """Verify JWT token and extract user ID."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
```

---

## Testing Strategy

1. **Unit Tests:**
   - Test route handlers in isolation
   - Mock downstream service calls
   - Verify error handling

2. **Integration Tests:**
   - Start all services (docker-compose)
   - Test end-to-end request flows
   - Verify authentication/rate limiting

3. **Load Tests:**
   - Simulate concurrent users
   - Measure P50/P95/P99 latency
   - Verify rate limiting under load

---

## Dependencies

**Required Services:**
- analysis-service (port 8000)
- llm-polish (port 8001)
- Redis (for rate limiting)
- Auth service (for token verification)

**Python Packages:**
- fastapi
- httpx (async HTTP client)
- python-jose[cryptography] (JWT)
- redis
- pydantic

---

## Next Steps

1. Implement authentication middleware (1 hour)
2. Add routing to analysis-service (1 hour)
3. Add routing to llm-polish (1.5 hours)
4. Implement rate limiting (1 hour)
5. Add comprehensive tests (2 hours)
6. Add API documentation (0.5 hours)

**Total Estimated Effort:** 4-6 hours
