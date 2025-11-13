"""Unit tests for token service bucket logic and consumption."""

from __future__ import annotations

from uuid import UUID

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models import Entitlement
from app.services.token_service import (
    InsufficientTokensError,
    compute_bucket_draw,
    consume_tokens_once,
)
from .utils import create_user_with_entitlement


@pytest.mark.asyncio
async def test_compute_bucket_draw_prefers_earned_then_bonus() -> None:
    draw = await compute_bucket_draw({"earned": 3, "bonus": 5, "plan": 10}, amount=6)
    assert draw == {"earned": 3, "bonus": 3, "plan": 0}


@pytest.mark.asyncio
async def test_compute_bucket_draw_raises_when_insufficient() -> None:
    with pytest.raises(InsufficientTokensError):
        await compute_bucket_draw({"earned": 1, "bonus": 0, "plan": 2}, amount=10)


@pytest.mark.asyncio
@given(
    earned=st.integers(min_value=0, max_value=50),
    bonus=st.integers(min_value=0, max_value=50),
    plan=st.integers(min_value=0, max_value=200),
    amount=st.integers(min_value=0, max_value=300),
)
@settings(max_examples=100)
async def test_compute_bucket_draw_never_overdraws(
    earned: int, bonus: int, plan: int, amount: int
) -> None:
    available = {"earned": earned, "bonus": bonus, "plan": plan}
    total = earned + bonus + plan
    if amount > total:
        with pytest.raises(InsufficientTokensError):
            await compute_bucket_draw(available, amount)
        return
    draw = await compute_bucket_draw(available, amount)
    assert sum(draw.values()) == amount
    for bucket, value in draw.items():
        assert value <= available[bucket]


@pytest.mark.asyncio
async def test_consume_tokens_once_updates_buckets(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=50, earned_tokens=5)
    ledger = await consume_tokens_once(
        session=db_session,
        user_id=user_id,
        amount=6,
        idem_key=None,
        related_type="chat",
        related_id="msg1",
        reason="chat_message",
        ip="127.0.0.1",
        ua="pytest",
    )
    assert ledger.token_delta == -6
    ent = await db_session.get(Entitlement, UUID(user_id))
    assert ent.plan_tokens_available == 49
    assert ent.earned_tokens_available == 0


@pytest.mark.asyncio
async def test_consume_tokens_once_is_idempotent(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=20)
    ledger = await consume_tokens_once(
        session=db_session,
        user_id=user_id,
        amount=4,
        idem_key="1c9a8d60-1e94-4d41-96f1-1c4e0c8aab81",
        related_type="chat",
        related_id="msg-77",
        reason="chat_message",
        ip=None,
        ua=None,
    )
    replay = await consume_tokens_once(
        session=db_session,
        user_id=user_id,
        amount=4,
        idem_key="1c9a8d60-1e94-4d41-96f1-1c4e0c8aab81",
        related_type="chat",
        related_id="msg-77",
        reason="chat_message",
        ip=None,
        ua=None,
    )
    assert replay.id == ledger.id


@pytest.mark.asyncio
async def test_consume_tokens_once_retries_on_conflict(db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=3)
    await consume_tokens_once(
        session=db_session,
        user_id=user_id,
        amount=3,
        idem_key=None,
        related_type=None,
        related_id=None,
        reason="chat_message",
        ip=None,
        ua=None,
    )
    with pytest.raises(InsufficientTokensError):
        await consume_tokens_once(
            session=db_session,
            user_id=user_id,
            amount=1,
            idem_key=None,
            related_type=None,
            related_id=None,
            reason="chat_message",
            ip=None,
            ua=None,
        )
