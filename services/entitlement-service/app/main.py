# -*- coding: utf-8 -*-
"""
Entitlement Service - FastAPI Application

Complete server with 6 endpoints:
1. GET /api/v1/entitlements - Fetch user entitlements with KST-aligned resets
2. POST /api/v1/tokens/consume - Consume tokens with optimistic locking
3. POST /api/v1/tokens/reward/ssv - Verify AdMob SSV signature
4. POST /api/v1/tokens/reward/claim - Claim verified ad reward
5. POST /api/v1/tokens/refund - Refund tokens (support/admin)
6. POST /api/v1/admin/entitlements/reset - Admin monthly reset

Features:
- RFC-8785 idempotency middleware
- Firebase JWT authentication
- Redis rate limiting
- Prometheus metrics
- APScheduler for scheduled resets
"""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.common.firebase_jwt import FirebaseJWTVerifier, JWTVerificationError

from .config import settings
from .database import engine
from .models import User, Entitlement, TokenLedger, AdReward
from .services.token_service import (
    consume_tokens_once,
    OptimisticLockError,
    InsufficientTokensError,
)
from .services.quota_service import lazy_daily_reset_if_needed, monthly_plan_reset_if_due
from .services.ssv_verifier import verify_admob_ssv, SSVVerificationError
from .services.fraud_detector import detect_fraud, FraudDecision
from .rate_limiter import check_rate_limit, RateLimitExceeded
from .middleware.idempotency import idempotency_middleware
from .instrumentation.metrics import (
    token_consume_total,
    token_consume_errors,
    token_consume_duration,
    entitlement_fetch_duration,
    ad_reward_total,
    ad_reward_fraud,
)

# Logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool: Optional[Redis] = None

# Database session factory
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)

# APScheduler for scheduled resets
scheduler = AsyncIOScheduler()

firebase_jwt_verifier = FirebaseJWTVerifier(
    issuer=settings.jwt_issuer,
    audience=settings.jwt_audience,
    jwks_url=settings.firebase_jwks_url,
    cache_ttl=settings.firebase_jwks_cache_seconds,
    clock_skew_seconds=settings.jwt_clock_skew_seconds,
)


@dataclass
class AuthenticatedUser:
    """Represents an authenticated caller."""

    user_id: str
    claims: Dict[str, Any]
    token: str


# -----------------------------------------------------------------------------
# Lifecycle Management
# -----------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global redis_pool

    # Startup
    logger.info("Starting Entitlement Service v%s", settings.version)

    # Redis connection
    redis_pool = Redis.from_url(settings.redis_url, decode_responses=False)
    await redis_pool.ping()
    logger.info("Redis connected: %s", settings.redis_url)

    # Database connection
    app.state.db = SessionLocal
    logger.info("Database connected: %s", settings.database_url.split("@")[-1])

    # APScheduler: Daily reset at 00:00 KST
    if scheduler.running:
        scheduler.shutdown(wait=False)

    scheduler.add_job(
        scheduled_daily_reset,
        "cron",
        hour=0,
        minute=0,
        timezone=settings.timezone,
        id="daily_reset",
    )
    scheduler.start()
    logger.info("Scheduler started: daily reset at 00:00 %s", settings.timezone)

    yield

    # Shutdown
    logger.info("Shutting down Entitlement Service")
    await redis_pool.aclose()
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# Middleware
app.middleware("http")(idempotency_middleware)


# -----------------------------------------------------------------------------
# Scheduled Jobs
# -----------------------------------------------------------------------------


async def scheduled_daily_reset():
    """Scheduled job: Reset daily quotas for all users at 00:00 KST."""
    logger.info("Running scheduled daily reset...")

    async with SessionLocal() as session:
        # Reset all entitlements (light_daily_used, ad_rewards_today)
        result = await session.execute(
            update(Entitlement).values(
                light_daily_used=0,
                ad_rewards_today=0,
                light_last_reset_date=func.current_date(),
                updated_at=func.now(),
            )
        )
        await session.commit()
        logger.info("Daily reset completed: %d users", result.rowcount)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class EntitlementsResponse(BaseModel):
    """Response: GET /api/v1/entitlements"""

    user_id: str
    plan_tier: str
    plan_tokens_available: int
    earned_tokens_available: int
    bonus_tokens_available: int
    total_tokens: int
    light_daily_limit: int
    light_daily_used: int
    light_daily_left: int
    deep_tokens_limit: int
    ad_rewards_today: int
    ad_rewards_this_month: int
    ad_cooldown_seconds: int
    ad_daily_cap: int
    ad_monthly_cap: int
    ads_suggest: bool


class ConsumeRequest(BaseModel):
    """Request: POST /api/v1/tokens/consume"""

    amount: int = Field(..., gt=0, description="Tokens to consume (positive)")
    related_entity_type: Optional[str] = Field(
        None, description="Entity type (e.g., 'chat', 'report')"
    )
    related_entity_id: Optional[str] = Field(
        None, description="Entity ID (e.g., message_id)"
    )
    reason: str = Field(..., description="Human-readable reason")


class ConsumeResponse(BaseModel):
    """Response: POST /api/v1/tokens/consume"""

    success: bool
    ledger_id: int
    tokens_before: int
    tokens_after: int
    token_delta: int
    idempotent_replay: bool


class SSVVerifyRequest(BaseModel):
    """Request: POST /api/v1/tokens/reward/ssv"""

    signature: str
    key_id: int
    timestamp: str
    user_id: str
    reward_amount: int
    custom_data: Optional[str] = None


class SSVVerifyResponse(BaseModel):
    """Response: POST /api/v1/tokens/reward/ssv"""

    verified: bool
    reward_id: str
    message: str


class RewardClaimRequest(BaseModel):
    """Request: POST /api/v1/tokens/reward/claim"""

    reward_id: str


class RewardClaimResponse(BaseModel):
    """Response: POST /api/v1/tokens/reward/claim"""

    success: bool
    tokens_granted: int
    earned_tokens_available: int
    fraud_detected: bool
    fraud_reason: Optional[str] = None


class RefundRequest(BaseModel):
    """Request: POST /api/v1/tokens/refund"""

    ledger_id: int
    reason: str


class RefundResponse(BaseModel):
    """Response: POST /api/v1/tokens/refund"""

    success: bool
    tokens_refunded: int
    tokens_after: int


class AdminResetRequest(BaseModel):
    """Request: POST /api/v1/admin/entitlements/reset"""

    user_id: str
    reset_type: str = Field(..., description="'daily' or 'monthly'")


class AdminResetResponse(BaseModel):
    """Response: POST /api/v1/admin/entitlements/reset"""

    success: bool
    message: str


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------


def _extract_user_id(claims: Dict[str, Any]) -> str:
    for key in ("uid", "user_id", "sub"):
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise HTTPException(status_code=401, detail="Token missing subject")


def _has_admin_role(claims: Dict[str, Any]) -> bool:
    """Determine whether the claims contain the required admin role."""

    claim_value = claims.get(settings.admin_role_claim)
    required = settings.admin_role_value.lower()

    if isinstance(claim_value, list):
        return any(str(item).lower() == required for item in claim_value)
    if isinstance(claim_value, str):
        return claim_value.lower() == required
    if isinstance(claim_value, bool):
        return claim_value and required in {"true", "1", "admin"}
    return False


async def get_db() -> AsyncSession:
    """Dependency: Database session."""
    async with SessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    """Dependency: Redis connection."""
    return redis_pool


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_debug_user: Optional[str] = Header(None),
) -> AuthenticatedUser:
    """Dependency: Extract and verify the caller's Firebase identity."""

    if settings.auth_debug_header_enabled and x_debug_user:
        logger.debug("Debug auth enabled - using X-Debug-User=%s", x_debug_user)
        return AuthenticatedUser(
            user_id=x_debug_user,
            claims={"debug": True},
            token="debug",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    try:
        claims = await firebase_jwt_verifier.verify(token)
    except JWTVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return AuthenticatedUser(
        user_id=_extract_user_id(claims),
        claims=claims,
        token=token,
    )


async def get_admin_user(
    authorization: Optional[str] = Header(None),
    x_debug_user: Optional[str] = Header(None),
) -> AuthenticatedUser:
    """Dependency: Ensure the caller has admin privileges."""

    user = await get_current_user(
        authorization=authorization,
        x_debug_user=x_debug_user,
    )

    if not _has_admin_role(user.claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "healthy",
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/entitlements", response_model=EntitlementsResponse)
async def get_entitlements(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    GET /api/v1/entitlements - Fetch user entitlements with lazy resets.

    Features:
    - Lazy daily reset (00:00 KST boundary)
    - Monthly plan reset (subscription renewal date)
    - Rate limiting (60 RPM)
    - Prometheus metrics
    """
    with entitlement_fetch_duration.time():
        # Rate limiting
        user_id = current_user.user_id

        try:
            await check_rate_limit(
                redis,
                f"entitlements:{user_id}",
                settings.rate_limit_entitlements_rpm,
                window_sec=60,
            )
        except RateLimitExceeded as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {e.retry_after}s",
            )

        # Fetch user and entitlement
        user = await session.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        ent = await session.get(Entitlement, UUID(user_id))
        if not ent:
            raise HTTPException(status_code=404, detail="Entitlement not found")

        # Lazy daily reset
        await lazy_daily_reset_if_needed(session, ent)

        # Monthly plan reset (if due)
        await monthly_plan_reset_if_due(session, ent, user.plan_tier)

        # Refresh entitlement after resets
        await session.refresh(ent)

        # Calculate total tokens
        total_tokens = (
            ent.plan_tokens_available
            + ent.earned_tokens_available
            + ent.bonus_tokens_available
        )

        # Calculate light daily left
        light_daily_left = max(0, ent.light_daily_limit - ent.light_daily_used)

        # Ad suggestion (cooldown check)
        # TODO: Check last ad reward timestamp in Redis for cooldown
        ads_suggest = (
            ent.ad_rewards_today < settings.ad_daily_cap
            and ent.ad_rewards_this_month < settings.ad_monthly_cap
        )

        await session.commit()

        return EntitlementsResponse(
            user_id=user_id,
            plan_tier=user.plan_tier,
            plan_tokens_available=ent.plan_tokens_available,
            earned_tokens_available=ent.earned_tokens_available,
            bonus_tokens_available=ent.bonus_tokens_available,
            total_tokens=total_tokens,
            light_daily_limit=ent.light_daily_limit,
            light_daily_used=ent.light_daily_used,
            light_daily_left=light_daily_left,
            deep_tokens_limit=ent.deep_tokens_limit,
            ad_rewards_today=ent.ad_rewards_today,
            ad_rewards_this_month=ent.ad_rewards_this_month,
            ad_cooldown_seconds=settings.ad_cooldown_seconds,
            ad_daily_cap=settings.ad_daily_cap,
            ad_monthly_cap=settings.ad_monthly_cap,
            ads_suggest=ads_suggest,
        )


@app.post("/api/v1/tokens/consume", response_model=ConsumeResponse)
async def consume_tokens(
    request: ConsumeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
):
    """
    POST /api/v1/tokens/consume - Consume tokens with optimistic locking.

    Features:
    - Three-bucket draw (earned → bonus → plan)
    - Optimistic locking with automatic retry
    - Business-entity uniqueness (prevents double-deduction)
    - Idempotency-Key header support
    - Rate limiting (10 RPM)
    - Prometheus metrics
    """
    with token_consume_duration.time():
        user_id = current_user.user_id
        # Rate limiting
        try:
            await check_rate_limit(
                redis,
                f"consume:{user_id}",
                settings.rate_limit_consume_rpm,
                window_sec=60,
            )
        except RateLimitExceeded as e:
            token_consume_errors.labels(error_code="RATE_LIMIT").inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {e.retry_after}s",
            )

        # Validate Idempotency-Key
        if idempotency_key:
            try:
                UUID(idempotency_key)
            except ValueError:
                token_consume_errors.labels(error_code="INVALID_IDEMPOTENCY_KEY").inc()
                raise HTTPException(
                    status_code=400, detail="Idempotency-Key must be a valid UUID"
                )

        # Retry loop (up to 3 attempts)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ledger = await consume_tokens_once(
                    session=session,
                    user_id=user_id,
                    amount=request.amount,
                    idem_key=idempotency_key,
                    related_type=request.related_entity_type,
                    related_id=request.related_entity_id,
                    reason=request.reason,
                    ip=x_forwarded_for,
                    ua=user_agent,
                )

                # Success
                token_consume_total.labels(
                    action="consume",
                    plan="unknown",  # TODO: Fetch user plan
                    idempotent=str(idempotency_key is not None),
                ).inc()

                # Check if replay (ledger already existed)
                idempotent_replay = ledger.created_at < datetime.now(timezone.utc).replace(
                    second=0, microsecond=0
                )

                return ConsumeResponse(
                    success=True,
                    ledger_id=ledger.id,
                    tokens_before=ledger.tokens_before,
                    tokens_after=ledger.tokens_after,
                    token_delta=ledger.token_delta,
                    idempotent_replay=idempotent_replay,
                )

            except OptimisticLockError:
                # Retry
                logger.warning("Optimistic lock collision (attempt %d)", attempt + 1)
                if attempt == max_retries - 1:
                    token_consume_errors.labels(error_code="OPTIMISTIC_LOCK").inc()
                    raise HTTPException(
                        status_code=409, detail="Concurrent modification detected"
                    )
                continue

            except InsufficientTokensError as e:
                token_consume_errors.labels(error_code="INSUFFICIENT_TOKENS").inc()
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "INSUFFICIENT_TOKENS",
                        "required": e.required,
                        "available": e.available,
                    },
                )


@app.post("/api/v1/tokens/reward/ssv", response_model=SSVVerifyResponse)
async def verify_reward_ssv(
    request: SSVVerifyRequest,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    POST /api/v1/tokens/reward/ssv - Verify AdMob SSV signature.

    Features:
    - ECDSA signature verification with Google public keys
    - Request hash deduplication
    - Fraud detection (4 heuristics)
    - Rate limiting (3 RPM)
    """
    # Rate limiting
    try:
        await check_rate_limit(
            redis,
            f"reward_ssv:{request.user_id}",
            settings.rate_limit_reward_rpm,
            window_sec=60,
        )
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {e.retry_after}s",
        )

    # Verify SSV signature
    ssv_params = {
        "signature": request.signature,
        "key_id": str(request.key_id),
        "timestamp": request.timestamp,
        "user_id": request.user_id,
        "reward_amount": str(request.reward_amount),
    }
    if request.custom_data:
        ssv_params["custom_data"] = request.custom_data

    try:
        await verify_admob_ssv(redis, ssv_params)
    except SSVVerificationError as e:
        ad_reward_total.labels(status="ssv_failed").inc()
        raise HTTPException(status_code=400, detail=str(e))

    # Check for duplicate SSV request (hash-based)
    import hashlib

    ssv_request_hash = hashlib.sha256(
        f"{request.signature}{request.timestamp}{request.user_id}".encode()
    ).hexdigest()

    existing = await session.execute(
        select(AdReward).where(AdReward.ssv_request_hash == ssv_request_hash)
    )
    if existing.scalar_one_or_none():
        ad_reward_total.labels(status="duplicate").inc()
        raise HTTPException(status_code=409, detail="Duplicate SSV request")

    # Create pending ad reward
    reward = AdReward(
        user_id=UUID(request.user_id),
        ssv_signature=request.signature,
        ssv_key_id=request.key_id,
        ssv_request_hash=ssv_request_hash,
        status="pending",
    )
    session.add(reward)
    await session.commit()

    ad_reward_total.labels(status="ssv_verified").inc()

    return SSVVerifyResponse(
        verified=True,
        reward_id=str(reward.id),
        message="SSV verified. Call /tokens/reward/claim to claim reward.",
    )


@app.post("/api/v1/tokens/reward/claim", response_model=RewardClaimResponse)
async def claim_reward(
    request: RewardClaimRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    POST /api/v1/tokens/reward/claim - Claim verified ad reward.

    Features:
    - Fraud detection (rapid views, IP hopping, unusual hours)
    - Cooldown and daily/monthly caps
    - Earned tokens bucket update
    - Ledger entry creation
    """
    # Fetch pending reward
    reward = await session.get(AdReward, UUID(request.reward_id))
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    user_id = current_user.user_id

    if reward.user_id != UUID(user_id):
        raise HTTPException(status_code=403, detail="Reward belongs to another user")

    if reward.status != "pending":
        raise HTTPException(
            status_code=409, detail=f"Reward already {reward.status}"
        )

    # Fraud detection
    from datetime import datetime, timezone
    fraud = await detect_fraud(
        session=session,
        user_id=str(user_id),
        device_id=reward.device_id,
        user_ip=str(reward.user_ip),
        now_utc=datetime.now(timezone.utc)
    )
    if fraud.suspicious and fraud.confidence >= 0.8:
        # Mark as fraud
        reward.status = "fraud"
        reward.fraud_reason = fraud.reason
        await session.commit()

        ad_reward_total.labels(status="fraud").inc()
        ad_reward_fraud.labels(reason=fraud.reason).inc()

        return RewardClaimResponse(
            success=False,
            tokens_granted=0,
            earned_tokens_available=0,
            fraud_detected=True,
            fraud_reason=fraud.reason,
        )

    # Fetch entitlement
    ent = await session.get(Entitlement, UUID(user_id))
    if not ent:
        raise HTTPException(status_code=404, detail="Entitlement not found")

    # Check daily/monthly caps
    if ent.ad_rewards_today >= settings.ad_daily_cap:
        raise HTTPException(status_code=429, detail="Daily ad cap reached")

    if ent.ad_rewards_this_month >= settings.ad_monthly_cap:
        raise HTTPException(status_code=429, detail="Monthly ad cap reached")

    # Grant tokens (fixed 2 tokens per ad)
    tokens_granted = 2
    total_before = (
        ent.plan_tokens_available
        + ent.earned_tokens_available
        + ent.bonus_tokens_available
    )

    await session.execute(
        update(Entitlement)
        .where(Entitlement.user_id == UUID(user_id))
        .values(
            earned_tokens_available=Entitlement.earned_tokens_available + tokens_granted,
            ad_rewards_today=Entitlement.ad_rewards_today + 1,
            ad_rewards_this_month=Entitlement.ad_rewards_this_month + 1,
            updated_at=func.now(),
        )
    )

    # Create ledger entry
    ledger = TokenLedger(
        user_id=UUID(user_id),
        transaction_type="reward",
        token_delta=tokens_granted,
        tokens_before=total_before,
        tokens_after=total_before + tokens_granted,
        reason=f"Ad reward - {reward.id}",
        related_entity_type="ad_reward",
        related_entity_id=str(reward.id),
    )
    session.add(ledger)

    # Mark reward as granted
    reward.status = "granted"
    await session.commit()

    # Refresh entitlement
    await session.refresh(ent)

    ad_reward_total.labels(status="granted").inc()

    return RewardClaimResponse(
        success=True,
        tokens_granted=tokens_granted,
        earned_tokens_available=ent.earned_tokens_available,
        fraud_detected=False,
        fraud_reason=None,
    )


@app.post("/api/v1/tokens/refund", response_model=RefundResponse)
async def refund_tokens(
    request: RefundRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    POST /api/v1/tokens/refund - Refund tokens (support/admin use case).

    Features:
    - Reverses consume transaction
    - Restores original bucket balances
    - Creates refund ledger entry
    """
    # Fetch original ledger entry
    original = await session.get(TokenLedger, request.ledger_id)
    if not original:
        raise HTTPException(status_code=404, detail="Ledger entry not found")

    user_id = current_user.user_id

    if original.user_id != UUID(user_id):
        raise HTTPException(
            status_code=403, detail="Ledger entry belongs to another user"
        )

    if original.transaction_type != "consume":
        raise HTTPException(status_code=400, detail="Can only refund consume transactions")

    # Check if already refunded
    existing_refund = await session.execute(
        select(TokenLedger).where(
            TokenLedger.user_id == UUID(user_id),
            TokenLedger.transaction_type == "refund",
            TokenLedger.related_entity_type == "ledger",
            TokenLedger.related_entity_id == str(original.id),
        )
    )
    if existing_refund.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already refunded")

    # Fetch entitlement
    ent = await session.get(Entitlement, UUID(user_id))
    if not ent:
        raise HTTPException(status_code=404, detail="Entitlement not found")

    # Refund tokens (reverse the delta)
    refund_amount = abs(original.token_delta)  # Delta is negative for consume
    total_before = (
        ent.plan_tokens_available
        + ent.earned_tokens_available
        + ent.bonus_tokens_available
    )

    # Refund to plan bucket (simplification - production should reverse original draw)
    await session.execute(
        update(Entitlement)
        .where(Entitlement.user_id == UUID(user_id))
        .values(
            plan_tokens_available=Entitlement.plan_tokens_available + refund_amount,
            updated_at=func.now(),
        )
    )

    # Create refund ledger entry
    ledger = TokenLedger(
        user_id=UUID(user_id),
        transaction_type="refund",
        token_delta=refund_amount,
        tokens_before=total_before,
        tokens_after=total_before + refund_amount,
        reason=request.reason,
        related_entity_type="ledger",
        related_entity_id=str(original.id),
    )
    session.add(ledger)
    await session.commit()

    # Refresh entitlement
    await session.refresh(ent)
    tokens_after = (
        ent.plan_tokens_available
        + ent.earned_tokens_available
        + ent.bonus_tokens_available
    )

    return RefundResponse(
        success=True,
        tokens_refunded=refund_amount,
        tokens_after=tokens_after,
    )


@app.post("/api/v1/admin/entitlements/reset", response_model=AdminResetResponse)
async def admin_reset_entitlements(
    request: AdminResetRequest,
    session: AsyncSession = Depends(get_db),
    admin_user: AuthenticatedUser = Depends(get_admin_user),
):
    """
    POST /api/v1/admin/entitlements/reset - Admin monthly reset.

    Admin-only endpoint for manual quota resets.
    TODO: Add admin authentication/authorization.
    """
    logger.info(
        "Admin reset requested by %s for user %s", admin_user.user_id, request.user_id
    )

    # Fetch entitlement
    ent = await session.get(Entitlement, UUID(request.user_id))
    if not ent:
        raise HTTPException(status_code=404, detail="Entitlement not found")

    # Fetch user for plan tier
    user = await session.get(User, UUID(request.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.reset_type == "daily":
        # Daily reset
        await lazy_daily_reset_if_needed(session, ent)
        await session.commit()
        return AdminResetResponse(
            success=True,
            message=f"Daily quota reset for user {request.user_id}",
        )

    elif request.reset_type == "monthly":
        # Monthly reset
        await monthly_plan_reset_if_due(session, ent, user.plan_tier)
        await session.commit()
        return AdminResetResponse(
            success=True,
            message=f"Monthly plan reset for user {request.user_id}",
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset_type. Must be 'daily' or 'monthly'",
        )
