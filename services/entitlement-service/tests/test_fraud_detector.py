"""Unit tests for fraud detector heuristics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.fraud_detector import detect_fraud
from .utils import create_ad_reward, create_user_with_entitlement


@pytest.mark.asyncio
async def test_detect_fraud_flags_rapid_rewards(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session)
    first = await create_ad_reward(db_session, user_id=user_id)
    second = await create_ad_reward(db_session, user_id=user_id)
    now = datetime.now(timezone.utc)
    first.created_at = now - timedelta(seconds=200)
    second.created_at = now - timedelta(seconds=100)
    await db_session.commit()

    decision = await detect_fraud(
        db_session,
        user_id,
        device_id="device",
        user_ip="127.0.0.1",
        now_utc=now,
    )
    assert decision.suspicious
    assert decision.reason == "rapid_ad_views"


@pytest.mark.asyncio
async def test_detect_fraud_flags_unusual_hours(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session)
    decision = await detect_fraud(
        db_session,
        user_id,
        device_id=None,
        user_ip="127.0.0.1",
        now_utc=datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc),
    )
    assert decision.suspicious
    assert decision.reason == "unusual_timing"
    assert decision.confidence == 0.6
