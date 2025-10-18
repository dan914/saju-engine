"""Timezone conversion logic with Delta-T calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from services.common import TraceMetadata
from services.common.saju_common import SimpleDeltaT

from ..models import TimeConversionRequest, TimeConversionResponse
from .events import TimeEventDetector


def _ensure_awareness(instant: datetime, tz_name: str) -> datetime:
    """Attach a timezone if the datetime is naive."""
    if instant.tzinfo is None:
        return instant.replace(tzinfo=ZoneInfo(tz_name))
    return instant


@dataclass(slots=True)
class TimezoneConverter:
    """Converts instants between timezones while tracking tzdb version info."""

    tzdb_version: str
    event_detector: TimeEventDetector
    delta_t_calculator: SimpleDeltaT | None = None

    def __post_init__(self):
        """Initialize delta_t_calculator if not provided."""
        if self.delta_t_calculator is None:
            object.__setattr__(self, "delta_t_calculator", SimpleDeltaT())

    def convert(self, request: TimeConversionRequest) -> TimeConversionResponse:
        src = _ensure_awareness(request.instant, request.source_tz)
        src = src.astimezone(ZoneInfo(request.source_tz))
        converted = src.astimezone(ZoneInfo(request.target_tz))
        events = self.event_detector.detect(request)

        # Calculate Delta-T for astronomical accuracy
        delta_t = self.delta_t_calculator.delta_t_seconds(
            year=request.instant.year, month=request.instant.month
        )

        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=delta_t,
            tz={
                "source": request.source_tz,
                "target": request.target_tz,
                "tzdbVersion": self.tzdb_version,
            },
            flags={"tzTransition": bool(events)},
        )
        return TimeConversionResponse(
            input=request,
            converted=converted,
            tzdb_version=self.tzdb_version,
            events=events,
            trace=trace.to_dict(),
        )
