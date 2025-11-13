# -*- coding: utf-8 -*-
"""
KST Timezone Utilities
Helper functions for Asia/Seoul timezone operations
"""

from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def now_utc() -> datetime:
    """Get current time in UTC with timezone awareness."""
    return datetime.now(timezone.utc)


def now_kst() -> datetime:
    """Get current time in KST with timezone awareness."""
    return datetime.now(KST)


def today_kst() -> date:
    """Get current date in KST timezone."""
    return datetime.now(KST).date()


def midnight_kst(dt: datetime | None = None) -> datetime:
    """
    Get midnight (00:00:00) in KST for given datetime.

    Args:
        dt: DateTime to get midnight for (defaults to now)

    Returns:
        Midnight datetime in KST timezone
    """
    base = dt.astimezone(KST) if dt else datetime.now(KST)
    return base.replace(hour=0, minute=0, second=0, microsecond=0)


def to_kst(dt: datetime) -> datetime:
    """Convert datetime to KST timezone."""
    return dt.astimezone(KST)


def from_kst_date(d: date) -> datetime:
    """Convert KST date to datetime at midnight KST."""
    return datetime(d.year, d.month, d.day, tzinfo=KST)
