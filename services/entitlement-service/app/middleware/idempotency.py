# -*- coding: utf-8 -*-
"""
RFC-8785 Canonical JSON Idempotency Middleware
Features:
- Deterministic JSON hashing (canonical key ordering)
- Request body caching (24h TTL)
- Replay detection with conflict handling
- Automatic response replay
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import json
from canonicaljson import encode_canonical_json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from ..models import IdempotencyKey


IDEMPOTENT_ENDPOINTS = (
    "/api/v1/tokens/consume",
    "/api/v1/tokens/reward/claim",
    "/api/v1/tokens/refund",
)


async def extract_body(request: Request) -> bytes:
    """
    Extract and cache request body.

    Request.body() can only be called once, so we cache it in request.state
    """
    if hasattr(request.state, "cached_body"):
        return request.state.cached_body

    body = await request.body()
    request.state.cached_body = body
    return body


async def idempotency_middleware(request: Request, call_next):
    """
    RFC-8785 canonical JSON idempotency middleware.

    Flow:
    1. Check if endpoint requires idempotency
    2. Extract Idempotency-Key header
    3. Compute RFC-8785 canonical hash of request body
    4. Check database for existing idempotency key
    5. If exists:
       - If body hash matches: replay cached response
       - If body hash differs: return 409 Conflict
    6. If not exists:
       - Proceed with request
       - Cache response with idempotency key (24h TTL)

    Args:
        request: FastAPI Request
        call_next: Next middleware/endpoint handler

    Returns:
        Response (either cached or fresh)

    Headers:
        Idempotency-Key: UUID (required for idempotent endpoints)
        X-Idempotent-Replay: "true"|"false"|"mismatch" (added to response)
    """
    # Only process POST requests to idempotent endpoints
    if request.method != "POST":
        return await call_next(request)

    if request.url.path not in IDEMPOTENT_ENDPOINTS:
        return await call_next(request)

    # Extract Idempotency-Key header
    idem = request.headers.get("Idempotency-Key")
    if not idem:
        # Idempotency-Key required but missing - proceed without idempotency
        # (endpoint will handle missing key error)
        return await call_next(request)

    # Validate UUID format
    try:
        idem_uuid = UUID(idem)
    except (ValueError, AttributeError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "INVALID_IDEMPOTENCY_KEY",
                "message": "Idempotency-Key must be a valid UUID"
            }
        )

    # Extract and hash request body (RFC-8785 canonical JSON)
    body_bytes = await extract_body(request)

    try:
        body_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        body_json = {}

    # Compute canonical hash (deterministic across clients)
    canonical = encode_canonical_json(body_json)
    request_hash = hashlib.sha256(canonical).hexdigest()

    # Lookup existing idempotency key in database
    # Note: request.app.state.db is an async session factory (set in startup)
    async with request.app.state.db() as session:
        rec = await session.get(IdempotencyKey, idem_uuid)

        if rec:
            # Idempotency key exists - check for conflicts
            if rec.request_hash != request_hash:
                # Body mismatch - reject with 409 Conflict
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": "IDEMPOTENCY_CONFLICT",
                        "message": "Request body differs from cached request for this Idempotency-Key",
                        "idempotency_key": str(idem_uuid),
                    },
                    headers={"X-Idempotent-Replay": "mismatch"}
                )

            # Body matches - replay cached response
            return JSONResponse(
                status_code=rec.response_status,
                content=rec.response_body,
                headers={"X-Idempotent-Replay": "true"}
            )

    # No existing idempotency key - proceed with request
    response: Response = await call_next(request)

    # Cache response for future replays (only JSON responses)
    try:
        # Read response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        content = json.loads(response_body.decode("utf-8"))
    except Exception:
        # Non-JSON response or read error - skip caching
        return response

    # Store idempotency key with response
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=24)

    async with request.app.state.db() as session:
        ik = IdempotencyKey(
            idempotency_key=idem_uuid,
            user_id=UUID(request.state.user_id) if hasattr(request.state, "user_id") else None,
            endpoint=request.url.path,
            request_hash=request_hash,
            response_status=response.status_code,
            response_body=content,
            created_at=now,
            expires_at=expires,
        )
        session.add(ik)
        await session.commit()

    # Rebuild response with cached body
    new_response = JSONResponse(
        status_code=response.status_code,
        content=content,
        headers=dict(response.headers)
    )
    new_response.headers["X-Idempotent-Replay"] = "false"

    return new_response
