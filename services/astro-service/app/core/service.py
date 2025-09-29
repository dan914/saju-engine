"""Domain service orchestrating solar term lookups."""
from __future__ import annotations

from zoneinfo import ZoneInfo

from ..models import TermEntry, TermQuery, TermResponse
from .loader import SolarTermLoader
from services.common import TraceMetadata


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
        tz = ZoneInfo(query.timezone)
        entries = [
            _with_timezone(entry, tz)
            for entry in self._loader.load_year(query.year)
        ]
        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=57.4,
            tz={"iana": query.timezone, "event": "none", "tzdbVersion": "2025a"},
            astro={"primary": "AstronomyEngine", "diffSeconds": 0.0},
        )
        return TermResponse(
            year=query.year,
            timezone=query.timezone,
            terms=entries,
            trace=trace.to_dict(),
        )
