"""Lightweight load harness to exercise concurrent consume requests."""

from __future__ import annotations

import asyncio
from time import perf_counter
from uuid import uuid4

import pytest

from app.config import settings as app_settings
from .utils import create_user_with_entitlement


@pytest.mark.asyncio
async def test_consume_load_harness(api_client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(app_settings, "rate_limit_consume_rpm", 10_000)
    user_id = await create_user_with_entitlement(db_session, plan_tokens=200)

    async def issue(idx: int):
        payload = {
            "amount": 2,
            "related_entity_type": "chat",
            "related_entity_id": f"load-{idx}",
            "reason": "chat_load",
        }
        headers = {"Idempotency-Key": str(uuid4()), "X-Test-User": user_id}
        return await api_client.post("/api/v1/tokens/consume", json=payload, headers=headers)

    start = perf_counter()
    responses = await asyncio.gather(*(issue(i) for i in range(20)))
    duration = perf_counter() - start

    assert all(resp.status_code == 200 for resp in responses)
    assert duration < 5.0  # ensure harness stays lightweight
