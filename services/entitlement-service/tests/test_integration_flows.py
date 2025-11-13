"""Integration tests covering consume, refund, and reward flows."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models import Entitlement, TokenLedger
from .utils import create_ad_reward, create_user_with_entitlement


@pytest.mark.asyncio
async def test_consume_endpoint_handles_idempotency(api_client, db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=20)
    idem_key = str(uuid4())
    payload = {
        "amount": 5,
        "related_entity_type": "chat",
        "related_entity_id": "cid-1",
        "reason": "chat_test",
    }
    headers = {"Idempotency-Key": idem_key, "X-Test-User": user_id}

    first = await api_client.post("/api/v1/tokens/consume", json=payload, headers=headers)
    assert first.status_code == 200, first.text
    data = first.json()
    assert data["success"]

    second = await api_client.post("/api/v1/tokens/consume", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["ledger_id"] == data["ledger_id"]

    ent = await db_session.get(Entitlement, UUID(user_id))
    assert ent.plan_tokens_available == 15


@pytest.mark.asyncio
async def test_refund_endpoint_restores_tokens(api_client, db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=15)
    payload = {
        "amount": 5,
        "related_entity_type": "chat",
        "related_entity_id": "cid-2",
        "reason": "chat_token",
    }
    headers = {"Idempotency-Key": str(uuid4()), "X-Test-User": user_id}
    consume_resp = await api_client.post("/api/v1/tokens/consume", json=payload, headers=headers)
    ledger_id = consume_resp.json()["ledger_id"]

    refund = await api_client.post(
        "/api/v1/tokens/refund",
        json={"ledger_id": ledger_id, "reason": "support"},
        headers={"X-Test-User": user_id},
    )
    assert refund.status_code == 200
    data = refund.json()
    assert data["success"] is True
    assert data["tokens_after"] == 15


@pytest.mark.asyncio
async def test_reward_claim_grants_tokens(api_client, db_session) -> None:
    user_id = await create_user_with_entitlement(db_session, plan_tokens=10, earned_tokens=0)
    reward = await create_ad_reward(db_session, user_id=user_id)

    resp = await api_client.post(
        "/api/v1/tokens/reward/claim",
        json={"reward_id": str(reward.id)},
        headers={"X-Test-User": user_id},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"]
    assert body["tokens_granted"] == 2

    result = await db_session.execute(
        select(TokenLedger).where(TokenLedger.related_entity_id == str(reward.id))
    )
    ledgers = result.scalars().all()
    assert ledgers and ledgers[0].transaction_type == "reward"

    ent = await db_session.get(Entitlement, UUID(user_id))
    assert ent.earned_tokens_available == 2
