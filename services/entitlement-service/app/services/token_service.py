# -*- coding: utf-8 -*-
"""
Token Service - Core token consumption logic
Features:
- Three-bucket token system (earned → bonus → plan)
- Optimistic locking with automatic retry
- Business-entity uniqueness (prevents double-deduction)
- Complete audit trail
"""

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from uuid import UUID

from ..models import Entitlement, TokenLedger


class OptimisticLockError(Exception):
    """Raised when optimistic lock version check fails."""
    pass


class InsufficientTokensError(Exception):
    """Raised when user has insufficient tokens."""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient tokens: need {required}, have {available}")


# CRITICAL: Spend order ensures fairness (use free tokens before paid plan tokens)
BUCKET_ORDER = ("earned", "bonus", "plan")


async def compute_bucket_draw(available: dict, amount: int) -> dict:
    """
    Compute how much to draw from each bucket according to BUCKET_ORDER.

    Args:
        available: Dict with keys "earned", "bonus", "plan" (current balances)
        amount: Total tokens to consume

    Returns:
        Dict with keys "earned", "bonus", "plan" (amounts to draw from each)

    Raises:
        InsufficientTokensError: If total available < amount

    Example:
        >>> await compute_bucket_draw({"earned": 5, "bonus": 0, "plan": 10}, 7)
        {"earned": 5, "bonus": 0, "plan": 2}
    """
    remaining = amount
    draw = {"earned": 0, "bonus": 0, "plan": 0}

    for bucket in BUCKET_ORDER:
        take = min(available[bucket], remaining)
        draw[bucket] = take
        remaining -= take

        if remaining == 0:
            break

    if remaining > 0:
        total_available = sum(available.values())
        raise InsufficientTokensError(required=amount, available=total_available)

    return draw


async def consume_tokens_once(
    session: AsyncSession,
    user_id: str,
    amount: int,
    idem_key: str | None,
    related_type: str | None,
    related_id: str | None,
    reason: str,
    ip: str | None,
    ua: str | None,
) -> TokenLedger:
    """
    Consume tokens exactly once using dual idempotency.

    Features:
    - Business-entity uniqueness (same entity can only be charged once)
    - Idempotency-Key header support (replay detection)
    - Optimistic locking with three bucket preconditions
    - Atomic ledger insertion

    Args:
        session: Async SQLAlchemy session
        user_id: User UUID (string)
        amount: Tokens to consume (positive integer)
        idem_key: Idempotency-Key header value (UUID string or None)
        related_type: Entity type (e.g., "chat", "report")
        related_id: Entity ID (e.g., message_id, report_id)
        reason: Human-readable reason for audit trail
        ip: User IP address (for audit)
        ua: User-Agent header (for audit)

    Returns:
        TokenLedger record (either newly created or replayed)

    Raises:
        OptimisticLockError: If concurrent modification detected
        InsufficientTokensError: If user has insufficient tokens
        ValueError: If entitlement record not found
    """
    # Step 1: Business-entity idempotency check (CRITICAL)
    # Same business entity (e.g., chat message) can only be charged once,
    # even if client uses different Idempotency-Key headers
    if related_type and related_id:
        existing = await session.execute(
            select(TokenLedger).where(
                TokenLedger.user_id == UUID(user_id),
                TokenLedger.transaction_type == "consume",
                TokenLedger.related_entity_type == related_type,
                TokenLedger.related_entity_id == related_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            # Already charged for this entity - replay success
            return row

    # Step 2: Read current entitlement balances (no FOR UPDATE needed)
    ent = await session.get(Entitlement, UUID(user_id), with_for_update=False)
    if ent is None:
        raise ValueError(f"Entitlement not found for user {user_id}")

    # Step 3: Compute bucket draw amounts
    avail = {
        "earned": ent.earned_tokens_available,
        "bonus": ent.bonus_tokens_available,
        "plan": ent.plan_tokens_available,
    }
    draw = await compute_bucket_draw(avail, amount)

    # Step 4: Optimistic update with version check + bucket preconditions
    # This prevents both lost updates AND negative balances
    stmt = (
        update(Entitlement)
        .where(
            Entitlement.user_id == UUID(user_id),
            Entitlement.version == ent.version,  # Optimistic lock
            Entitlement.earned_tokens_available >= draw["earned"],  # Prevent race
            Entitlement.bonus_tokens_available >= draw["bonus"],  # Prevent race
            Entitlement.plan_tokens_available >= draw["plan"],  # Prevent race
        )
        .values(
            earned_tokens_available=Entitlement.earned_tokens_available - draw["earned"],
            bonus_tokens_available=Entitlement.bonus_tokens_available - draw["bonus"],
            plan_tokens_available=Entitlement.plan_tokens_available - draw["plan"],
            version=Entitlement.version + 1,
            updated_at=func.now(),
        )
        .returning(
            Entitlement.earned_tokens_available,
            Entitlement.bonus_tokens_available,
            Entitlement.plan_tokens_available,
        )
    )

    res = await session.execute(stmt)
    row = res.first()

    if row is None:
        # Concurrent modification or insufficient balance
        raise OptimisticLockError("Concurrent modification or insufficient balance")

    # Step 5: Calculate before/after totals for ledger
    tokens_before = sum(avail.values())
    tokens_after = sum(row)  # Three returned columns (earned, bonus, plan)
    delta = tokens_after - tokens_before  # Should be -amount

    # Step 6: Insert ledger entry (idempotent via unique constraints)
    ledger = TokenLedger(
        user_id=UUID(user_id),
        transaction_type="consume",
        token_delta=delta,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        reason=reason,
        related_entity_type=related_type,
        related_entity_id=related_id,
        idempotency_key=UUID(idem_key) if idem_key else None,
        ip_address=ip,
        user_agent=ua,
    )

    session.add(ledger)

    try:
        await session.flush()
    except Exception:
        # Idempotency replay: check both idempotency_key and business entity
        if idem_key:
            lr = await session.execute(
                select(TokenLedger).where(TokenLedger.idempotency_key == UUID(idem_key))
            )
            existing = lr.scalar_one_or_none()
            if existing:
                return existing

        if related_type and related_id:
            lr = await session.execute(
                select(TokenLedger).where(
                    TokenLedger.user_id == UUID(user_id),
                    TokenLedger.transaction_type == "consume",
                    TokenLedger.related_entity_type == related_type,
                    TokenLedger.related_entity_id == related_id,
                )
            )
            existing = lr.scalar_one_or_none()
            if existing:
                return existing

        # Not an idempotency conflict - re-raise
        raise

    await session.commit()
    return ledger
