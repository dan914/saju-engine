"""Unit tests for AdMob SSV verification helpers."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.services.ssv_verifier import (
    SSVVerificationError,
    canonicalize_query,
    ssv_request_hash,
    verify_admob_ssv,
)


def test_canonicalize_query_sorts_and_excludes_signature() -> None:
    params = {"b": "2", "signature": "abc", "a": "1"}
    result = canonicalize_query(params)
    assert result == b"a=1&b=2"


def test_ssv_request_hash_stable() -> None:
    params = {"key_id": "123", "reward_amount": "2"}
    first = ssv_request_hash(params)
    second = ssv_request_hash(params.copy())
    assert first == second


@pytest.mark.asyncio
async def test_verify_admob_ssv_valid_signature(fake_redis, monkeypatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    params = {
        "key_id": "42",
        "reward_amount": "2",
        "reward_item": "tokens",
        "timestamp": "123",
    }
    message = canonicalize_query({**params})
    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    payload = {**params, "signature": base64.b64encode(signature).decode("utf-8")}

    async_mock = AsyncMock(return_value={"keys": [{"keyId": "42", "pem": public_pem}]})
    monkeypatch.setattr("app.services.ssv_verifier.fetch_keys", async_mock)

    assert await verify_admob_ssv(fake_redis, payload)


@pytest.mark.asyncio
async def test_verify_admob_ssv_missing_key_returns_false(fake_redis, monkeypatch) -> None:
    monkeypatch.setattr("app.services.ssv_verifier.fetch_keys", AsyncMock(return_value={"keys": []}))
    payload = {"key_id": "1", "signature": "sig"}
    with pytest.raises(SSVVerificationError):
        await verify_admob_ssv(fake_redis, payload)
