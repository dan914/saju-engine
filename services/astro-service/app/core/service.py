"""Domain service orchestrating solar term lookups."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from services.common import TraceMetadata

from ..models import TermEntry, TermQuery, TermResponse
from .loader import SolarTermLoader


def _with_timezone(entry: TermEntry, tz: ZoneInfo) -> TermEntry:
    """Return a shallow copy of entry with converted local_time."""
    local_time = entry.utc_time.astimezone(tz)
    return TermEntry(**entry.model_dump(exclude={"local_time"}), local_time=local_time)


class SolarTermService:
    """Coordinate precomputed terms with timezone conversion and tracing."""

    def __init__(self, loader: SolarTermLoader, tzdb_version: str = "2025a") -> None:
        self._loader = loader
        self._tzdb_version = tzdb_version

    def get_terms(self, query: TermQuery) -> TermResponse:
        """Get solar terms for a year with computed trace metadata."""
        tz = ZoneInfo(query.timezone)
        entries = [_with_timezone(entry, tz) for entry in self._loader.load_year(query.year)]

        # Calculate statistics from loaded entries
        if entries:
            delta_t_values = [e.delta_t_seconds for e in entries]
            avg_delta_t = sum(delta_t_values) / len(delta_t_values)
            delta_t_range = (
                max(delta_t_values) - min(delta_t_values) if len(delta_t_values) > 1 else 0.0
            )
            source = entries[0].source
            algo_version = entries[0].algo_version
        else:
            # Fallback for empty results (shouldn't happen with valid years)
            avg_delta_t = 0.0
            delta_t_range = 0.0
            source = "unknown"
            algo_version = "unknown"

        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=avg_delta_t,
            tz={"iana": query.timezone, "event": "none", "tzdbVersion": self._tzdb_version},
            astro={
                "primary": source,
                "algo_version": algo_version,
                "delta_t_range_seconds": delta_t_range,
                "entry_count": len(entries),
            },
        )
        return TermResponse(
            year=query.year,
            timezone=query.timezone,
            terms=entries,
            trace=trace.to_dict(),
        )
