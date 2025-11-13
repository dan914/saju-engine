# -*- coding: utf-8 -*-
"""
AdMob Server-Side Verification (SSV) Service
Features:
- ECDSA signature verification (Google AdMob public keys)
- Canonical query string generation (prevents bypass)
- Public key caching (24h TTL in Redis)
- Request hash deduplication
"""

import base64
import hashlib
import json
from typing import Dict

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from redis.asyncio import Redis


ADMOB_KEYS_URL = "https://www.gstatic.com/admob/reward/verifier-keys.json"
CACHE_KEY = "admob:ssv:keys"
CACHE_TTL = 24 * 3600  # 24 hours


class SSVVerificationError(Exception):
    """Raised when AdMob SSV verification fails."""


def canonicalize_query(params: Dict[str, str]) -> bytes:
    """
    Generate canonical query string for SSV signature verification.

    Excludes 'signature' parameter and sorts by key name.

    Args:
        params: Query parameters dict

    Returns:
        Canonical query string as bytes

    Example:
        >>> canonicalize_query({"key_id": "123", "reward_amount": "2", "signature": "..."})
        b"key_id=123&reward_amount=2"
    """
    # Exclude signature from message
    items = [(k, v) for k, v in params.items() if k != "signature"]

    # Sort by key name
    items.sort(key=lambda kv: kv[0])

    # Build querystring: k=v&k=v
    # Note: AdMob uses raw concatenation without URL encoding
    return "&".join([f"{k}={v}" for k, v in items]).encode("utf-8")


async def fetch_keys(redis: Redis) -> dict:
    """
    Fetch Google AdMob public keys (with Redis caching).

    Keys are cached for 24 hours to reduce latency and API calls.

    Args:
        redis: Redis client instance

    Returns:
        Keys document from Google: {"keys": [{"keyId": 123, "pem": "...", ...}]}

    Raises:
        httpx.HTTPStatusError: If Google API call fails
    """
    # Check cache first
    cached = await redis.get(CACHE_KEY)
    if cached:
        return json.loads(cached)

    # Fetch from Google
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(ADMOB_KEYS_URL)
        resp.raise_for_status()
        data = resp.json()

        # Cache for 24 hours
        await redis.set(CACHE_KEY, json.dumps(data), ex=CACHE_TTL)

        return data


async def verify_admob_ssv(redis: Redis, params: Dict[str, str]) -> bool:
    """
    Verify Google AdMob Server-Side Verification (SSV) signature.

    Flow:
    1. Fetch public keys from Google (with caching)
    2. Find key matching key_id parameter
    3. Generate canonical message from query params
    4. Verify ECDSA signature with SHA-256

    Args:
        redis: Redis client for key caching
        params: SSV callback query parameters (must include key_id, signature)

    Returns:
        True if signature is valid, False otherwise

    Example params:
        {
            "ad_network": "admob",
            "ad_unit_id": "ca-app-pub-xxx/yyy",
            "reward_amount": "2",
            "reward_item": "tokens",
            "custom_data": "user_123",
            "key_id": "3335741209",
            "signature": "MEYCIQDi3..."
        }
    """
    key_id = str(params.get("key_id"))
    sig_b64 = params.get("signature")

    if not key_id or not sig_b64:
        raise SSVVerificationError("SSV payload missing key_id or signature")

    try:
        # Fetch public keys
        keys_doc = await fetch_keys(redis)

        # Find matching key
        key = next(
            (k for k in keys_doc.get("keys", []) if str(k.get("keyId")) == key_id),
            None,
        )
        if not key:
            raise SSVVerificationError(f"Unknown key_id {key_id}")

        # Load PEM public key
        pem = key["pem"]
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))

        # Generate canonical message
        message = canonicalize_query(params)

        # Decode signature
        sig = base64.b64decode(sig_b64)

        # Verify ECDSA signature with SHA-256
        pub.verify(sig, message, ec.ECDSA(hashes.SHA256()))

        return True

    except InvalidSignature as exc:  # pragma: no cover - cryptography raises this
        raise SSVVerificationError("Invalid SSV signature") from exc
    except Exception as exc:  # pragma: no cover - network/crypto errors
        raise SSVVerificationError("Failed to verify SSV signature") from exc


def ssv_request_hash(params: Dict[str, str]) -> str:
    """
    Generate SHA-256 hash of canonical SSV request.

    Used for deduplication (prevents duplicate AdMob callbacks).

    Args:
        params: SSV query parameters

    Returns:
        Hex string SHA-256 hash

    Example:
        >>> ssv_request_hash({"key_id": "123", "reward_amount": "2", ...})
        "a3c4d5e6f7..."
    """
    msg = canonicalize_query(params)
    return hashlib.sha256(msg).hexdigest()
