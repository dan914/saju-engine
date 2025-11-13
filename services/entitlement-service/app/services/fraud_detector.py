# -*- coding: utf-8 -*-
"""
Fraud Detection Service
Features:
- 4 heuristics for ad reward fraud detection
- Confidence scoring (0.0-1.0)
- Threshold-based rejection (0.8 confidence)
"""

from zoneinfo import ZoneInfo
from datetime import timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..models import AdReward


class FraudDecision:
    """Fraud detection decision with confidence scoring."""

    def __init__(self, suspicious: bool, reason: str | None = None, confidence: float = 0.0):
        self.suspicious = suspicious
        self.reason = reason
        self.confidence = confidence

    def __repr__(self):
        return f"FraudDecision(suspicious={self.suspicious}, reason={self.reason}, confidence={self.confidence})"


async def detect_fraud(
    session: AsyncSession,
    user_id: str,
    device_id: str | None,
    user_ip: str,
    now_utc,
) -> FraudDecision:
    """
    Detect potential fraud using multiple heuristics.

    Heuristics:
    1. Rapid ad views (>= 2 within 5 minutes)
    2. IP hopping (>3 distinct IPs in 1 hour) - simplified
    3. Device mismatch (requires device binding) - scaffolded
    4. Unusual hours (0-6 AM KST)

    Threshold: confidence >= 0.8 triggers rejection

    Args:
        session: Async SQLAlchemy session
        user_id: User UUID string
        device_id: Device identifier (optional)
        user_ip: User IP address
        now_utc: Current datetime (UTC)

    Returns:
        FraudDecision with suspicious flag, reason, and confidence score
    """
    user_uuid = UUID(user_id)

    # Heuristic 1: Rapid ad views (>= 2 within 5 minutes)
    # This catches users rapidly clicking through ads
    q = await session.execute(
        select(AdReward)
        .where(AdReward.user_id == user_uuid)
        .order_by(AdReward.created_at.desc())
        .limit(3)
    )
    recent = q.scalars().all()

    if len(recent) >= 2:
        delta = (recent[0].created_at - recent[1].created_at).total_seconds()
        if delta < 300:  # 5 minutes
            return FraudDecision(True, "rapid_ad_views", 0.9)

    # Heuristic 2: IP hopping (>3 distinct IPs in 1 hour)
    # Note: Simplified implementation - production should use GROUP BY query
    # Production query:
    # SELECT COUNT(DISTINCT user_ip) FROM ad_rewards
    # WHERE user_id = ? AND created_at >= NOW() - INTERVAL '1 hour'
    #
    # For now, scaffolded for Phase 2 implementation
    # q = await session.execute(
    #     select(func.count(func.distinct(AdReward.user_ip)))
    #     .where(
    #         AdReward.user_id == user_uuid,
    #         AdReward.created_at >= now_utc - timedelta(hours=1)
    #     )
    # )
    # distinct_ips = q.scalar()
    # if distinct_ips > 3:
    #     return FraudDecision(True, "ip_hopping", 0.9)

    # Heuristic 3: Device mismatch (requires device binding)
    # Scaffolded for Phase 2 - needs user_devices table
    # Expected flow:
    # 1. User binds device on first app launch
    # 2. Check if device_id matches expected device
    # 3. Reject if mismatch with high confidence
    #
    # if device_id:
    #     expected_device = await get_user_device(session, user_uuid)
    #     if expected_device and expected_device.device_id != device_id:
    #         return FraudDecision(True, "device_mismatch", 0.85)

    # Heuristic 4: Unusual hours (0-6 AM KST)
    # Late night/early morning ad watching is suspicious
    kst_hour = now_utc.astimezone(ZoneInfo("Asia/Seoul")).hour
    if kst_hour < 6:
        return FraudDecision(True, "unusual_timing", 0.6)

    # No fraud detected
    return FraudDecision(False)
