"""Unit tests for quota reset helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import Entitlement, TokenLedger
from app.services.quota_service import lazy_daily_reset_if_needed, monthly_plan_reset_if_due
from .utils import create_user_with_entitlement


@pytest.mark.asyncio
async def test_lazy_daily_reset_clears_counters(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session)
    ent = await db_session.get(Entitlement, UUID(user_id))
    ent.light_daily_used = 4
    ent.ad_rewards_today = 2
    ent.light_last_reset_date = date.today() - timedelta(days=1)
    await db_session.commit()

    await lazy_daily_reset_if_needed(db_session, ent)
    await db_session.commit()
    await db_session.refresh(ent)

    assert ent.light_daily_used == 0
    assert ent.ad_rewards_today == 0
    assert ent.light_last_reset_date == date.today()


@pytest.mark.asyncio
async def test_monthly_plan_reset_refills_plan_bucket_and_adds_ledger(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=40)
    ent = await db_session.get(Entitlement, UUID(user_id))
    ent.plan_tokens_available = 5
    ent.deep_tokens_last_reset = datetime.now(timezone.utc) - timedelta(days=40)
    await db_session.commit()

    await monthly_plan_reset_if_due(db_session, ent, tier="premium")
    await db_session.commit()
    await db_session.refresh(ent)

    assert ent.plan_tokens_available == ent.deep_tokens_limit

    result = await db_session.execute(
        select(TokenLedger).where(TokenLedger.user_id == UUID(user_id))
    )
    ledgers = result.scalars().all()
    assert len(ledgers) == 1
    assert ledgers[0].reason.startswith("Monthly plan reset")
