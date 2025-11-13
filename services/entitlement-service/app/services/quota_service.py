# -*- coding: utf-8 -*-
"""
Quota Service - KST-aligned quota reset logic
Features:
- Lazy daily resets (00:00 KST)
- Monthly plan resets (subscription renewal date)
- Ledger entries for monthly resets
"""

from sqlalchemy import update, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from uuid import UUID

from ..utils.time_kst import today_kst
from ..models import Entitlement, TokenLedger
from ..instrumentation.metrics import daily_quota_reset_total, monthly_quota_reset_total


async def lazy_daily_reset_if_needed(session: AsyncSession, ent: Entitlement):
    """
    Perform lazy daily quota reset if needed (00:00 KST boundary crossed).

    Resets:
    - light_daily_used → 0
    - light_last_reset_date → today (KST)
    - ad_rewards_today → 0

    Args:
        session: Async SQLAlchemy session
        ent: Entitlement record to check/reset

    Note: This is called on every /entitlements fetch for automatic reset.
          APScheduler can also run this as a scheduled job at 00:00 KST.
    """
    tk = today_kst()

    if ent.light_last_reset_date < tk:
        # Day boundary crossed - reset daily quotas
        await session.execute(
            update(Entitlement)
            .where(Entitlement.user_id == ent.user_id)
            .values(
                light_daily_used=0,
                light_last_reset_date=tk,
                ad_rewards_today=0,
                updated_at=func.now(),
            )
        )

        daily_quota_reset_total.inc()


async def monthly_plan_reset_if_due(
    session: AsyncSession,
    ent: Entitlement,
    tier: str
):
    """
    Perform monthly plan token reset if due (subscription renewal date).

    Resets:
    - plan_tokens_available → deep_tokens_limit (refill plan bucket)
    - deep_tokens_last_reset → now
    - ad_rewards_this_month → 0

    Creates ledger entry for the refill (audit trail).

    Args:
        session: Async SQLAlchemy session
        ent: Entitlement record to check/reset
        tier: User plan tier (for ledger reason)

    Note: Renewal anchor is stored in plan_renewal_anchor field to handle
          mid-month upgrades correctly (e.g., upgrade on day 15 → reset on day 15 monthly)
    """
    now = datetime.now(timezone.utc)
    anchor = ent.plan_renewal_anchor or now
    last_reset = ent.deep_tokens_last_reset or anchor

    # Check if approximately 30 days have passed since last reset
    # For production: use dateutil.relativedelta for exact month calculations
    if (now - last_reset) >= timedelta(days=30):
        plan_limit = ent.deep_tokens_limit
        delta = plan_limit - ent.plan_tokens_available  # Tokens to refill

        if delta > 0:
            # Refill plan bucket
            await session.execute(
                update(Entitlement)
                .where(Entitlement.user_id == ent.user_id)
                .values(
                    plan_tokens_available=plan_limit,
                    deep_tokens_last_reset=now,
                    ad_rewards_this_month=0,
                    updated_at=func.now(),
                )
            )

            # Create ledger entry for the refill
            total_before = (
                ent.plan_tokens_available
                + ent.earned_tokens_available
                + ent.bonus_tokens_available
            )
            total_after = plan_limit + ent.earned_tokens_available + ent.bonus_tokens_available

            ledger = TokenLedger(
                user_id=ent.user_id,
                transaction_type="reset",
                token_delta=delta,
                tokens_before=total_before,
                tokens_after=total_after,
                reason=f"Monthly plan reset - {tier}",
            )
            session.add(ledger)

            monthly_quota_reset_total.inc()
