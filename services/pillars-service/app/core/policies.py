"""Boundary policy helpers (e.g., zi-start-23)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(slots=True)
class DayBoundaryPolicy:
    """Apply KR_classic_v1.4 day boundary rules (子時 23:00)."""

    epsilon: timedelta = timedelta(milliseconds=1)

    def day_start(self, local_dt: datetime, timezone: str) -> datetime:
        """Return the local datetime representing the day start (23:00 previous day)."""
        tz = ZoneInfo(timezone)
        localized = local_dt.astimezone(tz)
        target = localized.replace(hour=23, minute=0, second=0, microsecond=0)
        if localized.time() < time(23, 0):
            target -= timedelta(days=1)
        return target
