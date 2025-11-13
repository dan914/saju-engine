"""Unit tests for RFC-8785 idempotency middleware."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import SessionLocal
from app.middleware.idempotency import idempotency_middleware


def _build_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.state.db = SessionLocal
    test_app.middleware("http")(idempotency_middleware)

    @test_app.post("/api/v1/tokens/consume")
    async def echo(request: Request):  # pragma: no cover - executed via TestClient
        request.state.user_id = request.headers["x-test-user"]
        payload = await request.json()
        return {"ok": True, "payload": payload}

    return test_app


def test_idempotency_replays_cached_response(test_user_id):
    app = _build_test_app()
    client = TestClient(app)
    idem_key = "f21d0130-f801-4bfb-9a2d-1765f7a8b010"
    payload = {"amount": 3, "reason": "test"}

    first = client.post(
        "/api/v1/tokens/consume",
        json=payload,
        headers={"Idempotency-Key": idem_key, "X-Test-User": test_user_id},
    )
    assert first.status_code == 200
    assert first.headers["X-Idempotent-Replay"] == "false"

    second = client.post(
        "/api/v1/tokens/consume",
        json=payload,
        headers={"Idempotency-Key": idem_key, "X-Test-User": test_user_id},
    )
    assert second.status_code == 200
    assert second.headers["X-Idempotent-Replay"] == "true"
    assert second.json() == first.json()


def test_idempotency_conflict_detected(test_user_id):
    app = _build_test_app()
    client = TestClient(app)
    idem_key = "bcab0b46-7381-4da2-98f3-0d61da13d8e4"

    client.post(
        "/api/v1/tokens/consume",
        json={"amount": 3},
        headers={"Idempotency-Key": idem_key, "X-Test-User": test_user_id},
    )

    conflict = client.post(
        "/api/v1/tokens/consume",
        json={"amount": 4},
        headers={"Idempotency-Key": idem_key, "X-Test-User": test_user_id},
    )
    assert conflict.status_code == 409
    assert conflict.headers["X-Idempotent-Replay"] == "mismatch"
