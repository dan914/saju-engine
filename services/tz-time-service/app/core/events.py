"""Helpers for detecting timezone transitions and policy events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from ..models import TimeConversionRequest, TimeEvent

# Historical timezone events for Korean zones
# Source: IANA tzdata + Korean government records
KOREAN_TZ_EVENTS = [
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1987, 5, 10, 2, 0, 0),
        "notes": "1987 DST start (+1 hour)",
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1987, 10, 11, 3, 0, 0),
        "notes": "1987 DST end (-1 hour)",
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 5, 8, 2, 0, 0),
        "notes": "1988 DST start (+1 hour)",
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 10, 9, 3, 0, 0),
        "notes": "1988 DST end (-1 hour)",
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2015, 8, 15, 0, 0, 0),
        "notes": "UTC+08:30 adoption (Pyongyang Time)",
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2018, 5, 5, 0, 0, 0),
        "notes": "UTC+09:00 reversion (reunification gesture)",
    },
]


@dataclass(slots=True)
class TimeEventDetector:
    """Inspect instants around timezone transitions (DST, historical policy)."""

    transition_window_hours: int = 48

    def _is_relevant_event(self, event_time: datetime, request_time: datetime) -> bool:
        """Check if event is within temporal window of request.

        Args:
            event_time: When the timezone event occurred
            request_time: The instant being converted

        Returns:
            True if event is within transition_window_hours of request
        """
        # Ensure both datetimes are timezone-aware for comparison
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))
        if request_time.tzinfo is None:
            request_time = request_time.replace(tzinfo=ZoneInfo("UTC"))

        # Calculate time delta in seconds
        delta_seconds = abs((event_time - request_time).total_seconds())
        window_seconds = self.transition_window_hours * 3600

        return delta_seconds <= window_seconds

    def detect(self, request: TimeConversionRequest) -> list[TimeEvent]:
        """Analyze timezone transitions relevant to the request.

        Returns only events within transition_window_hours of request.instant.

        Args:
            request: Time conversion request with instant and timezone info

        Returns:
            List of relevant timezone events (empty if none within window)
        """
        relevant_events: list[TimeEvent] = []
        instant = request.instant
        zones = {request.source_tz, request.target_tz}

        # Ensure request instant is timezone-aware
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=ZoneInfo("UTC"))

        # Filter KOREAN_TZ_EVENTS by zone and temporal relevance
        for event_data in KOREAN_TZ_EVENTS:
            # Check if event's zone is in request zones
            if event_data["iana"] not in zones:
                continue

            # Check if event is within temporal window
            if not self._is_relevant_event(event_data["effective_from"], instant):
                continue

            # Event is relevant - add to results
            relevant_events.append(TimeEvent(**event_data))

        return relevant_events
