"""Resolve local datetime to UTC applying zi-start-23 day boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.common import TraceMetadata


@dataclass(slots=True)
class TimeResolver:
    """Resolve local times to UTC considering historical timezone rules."""

    epsilon_ms: int = 1
    transition_window_hours: int = 48

    def resolve(self, local_dt: datetime, timezone: str) -> tuple[datetime, TraceMetadata]:
        tz = ZoneInfo(timezone)
        localized = local_dt.replace(tzinfo=tz)
        utc_dt = localized.astimezone(ZoneInfo("UTC"))

        flags = {"tzTransition": self._has_recent_transition(localized)}
        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=57.4,
            tz={"iana": timezone, "event": "none", "tzdbVersion": "2025a"},
            boundary_policy="LCRO",
            epsilon_seconds=self.epsilon_ms / 1000,
            flags=flags,
        )
        return utc_dt, trace

    def _has_recent_transition(self, localized: datetime) -> bool:
        """Detect tz offset changes within the transition window."""
        tz = localized.tzinfo
        if tz is None:
            return False
        current_offset = localized.utcoffset()
        for delta_hours in (-self.transition_window_hours, self.transition_window_hours):
            moment = localized + timedelta(hours=delta_hours)
            if moment.utcoffset() != current_offset:
                return True
        return False


@dataclass(slots=True)
class DayBoundaryCalculator:
    """Compute day start using midnight (00:00) as boundary."""

    epsilon_ms: int = 1

    def compute(self, local_dt: datetime, timezone: str) -> datetime:
        tz = ZoneInfo(timezone)
        localized = local_dt.replace(tzinfo=tz)
        # Day starts at midnight (00:00) of the same calendar day
        boundary = localized.replace(hour=0, minute=0, second=0, microsecond=0)
        return boundary
