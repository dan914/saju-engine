"""Helpers for detecting timezone transitions and policy events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..models import TimeConversionRequest, TimeEvent


@dataclass(slots=True)
class TimeEventDetector:
    """Inspect instants around timezone transitions (DST, historical policy)."""

    transition_window_hours: int = 48

    def detect(self, request: TimeConversionRequest) -> list[TimeEvent]:
        """Analyze timezone transitions relevant to the request.

        Placeholder implementation returns known policy events for Seoul/Pyongyang.
        """
        events: list[TimeEvent] = []
        instant = request.instant
        zones = {request.source_tz, request.target_tz}

        if "Asia/Seoul" in zones:
            events.append(
                TimeEvent(
                    iana="Asia/Seoul",
                    kind="transition",
                    effective_from=datetime(1988, 5, 7, 16, 0, 0),
                    notes="1987–1988 DST window",
                )
            )

        if "Asia/Pyongyang" in zones:
            events.append(
                TimeEvent(
                    iana="Asia/Pyongyang",
                    kind="policy",
                    effective_from=datetime(2015, 8, 15, 0, 0, 0),
                    notes="+08:30 adoption (2015–2018)",
                )
            )

        return events
