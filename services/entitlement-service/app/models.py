# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM Models
Matches database schema from migrations 001-005
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    TIMESTAMP,
    Text,
    Boolean,
    ForeignKey,
    Date,
    JSON,
    func,
)
from uuid import UUID, uuid4
from datetime import datetime, date
from .database import Base
from .db_types import GUID, Inet


class User(Base):
    """User accounts with subscription plan management."""
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(GUID(), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))

    plan_tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    plan_start_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    plan_end_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class Entitlement(Base):
    """User quotas and entitlements with three-bucket token system."""
    __tablename__ = "entitlements"

    user_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    # Light chat quotas (daily reset)
    light_daily_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    light_daily_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    light_last_reset_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Deep tokens (three-bucket system)
    deep_tokens_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_tokens_available: Mapped[int] = mapped_column(Integer, nullable=False)
    earned_tokens_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_tokens_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deep_tokens_last_reset: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Storage quotas
    storage_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Saved reports quotas
    saved_reports_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    saved_reports_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Ad rewards tracking
    ad_rewards_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ad_rewards_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_ad_reward_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Subscription renewal
    plan_renewal_anchor: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Metadata
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic locking


class TokenLedger(Base):
    """Immutable audit trail for all token transactions."""
    __tablename__ = "token_ledger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    token_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_before: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_after: Mapped[int] = mapped_column(Integer, nullable=False)

    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(50))
    related_entity_id: Mapped[str | None] = mapped_column(String(100))

    idempotency_key: Mapped[UUID | None] = mapped_column(GUID())
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ip_address: Mapped[str | None] = mapped_column(Inet())
    user_agent: Mapped[str | None] = mapped_column(Text)


class AdReward(Base):
    """Google AdMob Server-Side Verification (SSV) tracking."""
    __tablename__ = "ad_rewards"

    id: Mapped[UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    ad_network: Mapped[str] = mapped_column(String(50), nullable=False)
    ad_unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_amount: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    ssv_signature: Mapped[str] = mapped_column(Text, nullable=False)
    ssv_key_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ssv_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ssv_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    user_ip: Mapped[str] = mapped_column(Inet(), nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    ssv_request_hash: Mapped[str | None] = mapped_column(String(64), unique=True)


class IdempotencyKey(Base):
    """RFC-8785 canonical JSON-based idempotency for critical endpoints."""
    __tablename__ = "idempotency_keys"

    idempotency_key: Mapped[UUID] = mapped_column(GUID(), primary_key=True)
    user_id: Mapped[UUID | None] = mapped_column(
        GUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=True
    )

    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
