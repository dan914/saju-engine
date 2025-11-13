"""Test helpers for entitlement service."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdReward, Entitlement, TokenLedger, User


async def create_user_with_entitlement(
    session: AsyncSession,
    *,
    user_id: str | None = None,
    plan_tier: str = "premium",
    plan_tokens: int = 100,
    earned_tokens: int = 0,
    bonus_tokens: int = 0,
    light_daily_limit: int = 5,
) -> str:
    """Insert a user + entitlement row for tests and return user_id."""
    now = datetime.now(timezone.utc)
    today = date.today()
    resolved_id = user_id or str(uuid4())
    user = User(
        user_id=UUID(resolved_id) if isinstance(resolved_id, str) else resolved_id,
        email=f"{resolved_id}@example.com",
        display_name="Test User",
        plan_tier=plan_tier,
        plan_start_date=now,
        plan_end_date=now + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )
    entitlement = Entitlement(
        user_id=user.user_id,
        light_daily_limit=light_daily_limit,
        light_daily_used=0,
        light_last_reset_date=today,
        deep_tokens_limit=plan_tokens,
        plan_tokens_available=plan_tokens,
        earned_tokens_available=earned_tokens,
        bonus_tokens_available=bonus_tokens,
        deep_tokens_last_reset=now - timedelta(days=1),
        storage_limit_mb=1024,
        storage_used_bytes=0,
        saved_reports_limit=10,
        saved_reports_count=0,
        ad_rewards_today=0,
        ad_rewards_this_month=0,
        last_ad_reward_at=None,
        plan_renewal_anchor=now - timedelta(days=15),
        updated_at=now,
        version=1,
    )
    # Insert user first to satisfy foreign key constraint
    session.add(user)
    await session.flush()
    # Now insert entitlement with valid user_id reference
    session.add(entitlement)
    await session.commit()
    return str(user.user_id)


async def create_token_ledger(
    session: AsyncSession,
    *,
    user_id: str,
    token_delta: int,
    reason: str,
    related_type: str | None = None,
    related_id: str | None = None,
) -> TokenLedger:
    """Insert a ledger entry for refund tests."""
    ledger = TokenLedger(
        user_id=UUID(user_id),
        transaction_type="consume" if token_delta < 0 else "reward",
        token_delta=token_delta,
        tokens_before=100,
        tokens_after=100 + token_delta,
        reason=reason,
        related_entity_type=related_type,
        related_entity_id=related_id,
    )
    session.add(ledger)
    await session.commit()
    await session.refresh(ledger)
    return ledger


async def create_ad_reward(
    session: AsyncSession,
    *,
    user_id: str,
    status: str = "pending",
    reward_amount: int = 2,
) -> AdReward:
    """Insert a pending ad reward for claim flow tests."""
    now = datetime.now(timezone.utc)
    reward = AdReward(
        user_id=UUID(user_id),
        ad_network="admob",
        ad_unit_id="unit-test",
        reward_amount=reward_amount,
        ssv_signature="sig",
        ssv_key_id=111,
        ssv_verified=True,
        ssv_verified_at=now,
        user_ip="127.0.0.1",
        user_agent="pytest",
        device_id="device",
        status=status,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        ssv_request_hash=str(uuid4()),
    )
    session.add(reward)
    await session.commit()
    await session.refresh(reward)
    return reward

