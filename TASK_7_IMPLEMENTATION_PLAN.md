# Task #7 Implementation Plan: Fix TimeEventDetector Hardcoded DST

**Date:** 2025-10-12
**Status:** PLANNING
**Priority:** 🟠 HIGH
**Estimated Time:** 2-3 hours

---

## 1. Problem Analysis

**Current Issue:**
- `services/tz-time-service/app/core/events.py:26-34` always returns 1987-1988 Seoul DST event
- Line 36-44 always returns 2015 Pyongyang timezone policy change
- Events are returned regardless of whether they're relevant to `request.instant`
- Violates the transition_window_hours intent (48 hours by default)

**Hardcoded Values:**
```python
# Line 31: Seoul DST (always returned if "Asia/Seoul" in zones)
effective_from=datetime(1988, 5, 7, 16, 0, 0)

# Line 41: Pyongyang +08:30 adoption (always returned if "Asia/Pyongyang" in zones)
effective_from=datetime(2015, 8, 15, 0, 0, 0)
```

**Why This Is Wrong:**
- A 2000-09-14 birth time shouldn't return 1988 DST event (12 years apart)
- Events should only be returned if within transition_window_hours (default: 48 hours)
- Currently misleads users about relevant timezone transitions

---

## 2. Solution Design

**Approach:** Filter events by temporal relevance to request.instant

**Core Logic:**
```python
def is_within_window(event_time: datetime, request_time: datetime, window_hours: int) -> bool:
    """Check if event is within window of request instant."""
    delta = abs((event_time - request_time).total_seconds())
    window_seconds = window_hours * 3600
    return delta <= window_seconds
```

**Enhanced Dataset:**
Expand historical events for better coverage:

1. **Seoul (Asia/Seoul)**:
   - 1987-05-10: DST start (+1 hour)
   - 1987-10-11: DST end (-1 hour)
   - 1988-05-08: DST start (+1 hour)
   - 1988-10-09: DST end (-1 hour)

2. **Pyongyang (Asia/Pyongyang)**:
   - 2015-08-15: UTC+08:30 adoption
   - 2018-05-05: UTC+09:00 reversion

3. **Other Korean zones** (future expansion):
   - Historical offset changes for North Korean timezone

---

## 3. Implementation Steps

### Step 1: Define Historical Events
Create a comprehensive list of timezone events with precise timestamps:

```python
# Historical timezone events for Korean zones
KOREAN_TZ_EVENTS = [
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1987, 5, 10, 2, 0, 0),
        "notes": "1987 DST start (+1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1987, 10, 11, 3, 0, 0),
        "notes": "1987 DST end (-1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 5, 8, 2, 0, 0),
        "notes": "1988 DST start (+1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 10, 9, 3, 0, 0),
        "notes": "1988 DST end (-1 hour)"
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2015, 8, 15, 0, 0, 0),
        "notes": "UTC+08:30 adoption (Pyongyang Time)"
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2018, 5, 5, 0, 0, 0),
        "notes": "UTC+09:00 reversion (reunification gesture)"
    },
]
```

### Step 2: Implement Temporal Filtering
Add window checking logic to detect() method:

```python
def _is_relevant_event(
    self,
    event_time: datetime,
    request_time: datetime,
    window_hours: int
) -> bool:
    """Check if event is within temporal window of request."""
    # Make both datetimes timezone-aware for comparison
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=ZoneInfo("UTC"))
    if request_time.tzinfo is None:
        request_time = request_time.replace(tzinfo=ZoneInfo("UTC"))

    delta_seconds = abs((event_time - request_time).total_seconds())
    window_seconds = window_hours * 3600
    return delta_seconds <= window_seconds
```

### Step 3: Update detect() Method
Replace placeholder logic with filtered event detection:

```python
def detect(self, request: TimeConversionRequest) -> list[TimeEvent]:
    """Analyze timezone transitions relevant to the request.

    Returns only events within transition_window_hours of request.instant.
    """
    relevant_events: list[TimeEvent] = []
    instant = request.instant
    zones = {request.source_tz, request.target_tz}

    # Filter KOREAN_TZ_EVENTS by zone and temporal relevance
    for event_data in KOREAN_TZ_EVENTS:
        # Check if event's zone is in request zones
        if event_data["iana"] not in zones:
            continue

        # Check if event is within temporal window
        if not self._is_relevant_event(
            event_data["effective_from"],
            instant,
            self.transition_window_hours
        ):
            continue

        # Event is relevant - add to results
        relevant_events.append(TimeEvent(**event_data))

    return relevant_events
```

### Step 4: Add tzinfo Handling
Ensure proper timezone awareness for comparisons:

```python
from zoneinfo import ZoneInfo

# At top of detect() method
if instant.tzinfo is None:
    instant = instant.replace(tzinfo=ZoneInfo("UTC"))
```

---

## 4. Expected Before/After

### BEFORE: Hardcoded (Always Returns)
```python
# Request: 2000-09-14 10:00:00 Asia/Seoul
request = TimeConversionRequest(
    instant=datetime(2000, 9, 14, 10, 0, 0),
    source_tz="Asia/Seoul",
    target_tz="UTC"
)

events = detector.detect(request)
# Returns: [TimeEvent(iana="Asia/Seoul", effective_from=1988-05-07, ...)]
# ❌ WRONG: 1988 event is 12 years away, outside 48-hour window!
```

### AFTER: Filtered by Relevance
```python
# Request: 2000-09-14 10:00:00 Asia/Seoul
request = TimeConversionRequest(
    instant=datetime(2000, 9, 14, 10, 0, 0),
    source_tz="Asia/Seoul",
    target_tz="UTC"
)

events = detector.detect(request)
# Returns: []
# ✅ CORRECT: No events within 48-hour window of 2000-09-14

# Request: 1988-05-08 02:00:00 Asia/Seoul (near DST start)
request = TimeConversionRequest(
    instant=datetime(1988, 5, 8, 2, 0, 0),
    source_tz="Asia/Seoul",
    target_tz="UTC"
)

events = detector.detect(request)
# Returns: [TimeEvent(iana="Asia/Seoul", kind="dst", effective_from=1988-05-08, notes="1988 DST start (+1 hour)")]
# ✅ CORRECT: Event within 48-hour window
```

---

## 5. Edge Cases

### Case 1: Naive Datetimes
**Issue:** request.instant might be timezone-naive
**Solution:** Add tzinfo=UTC if missing before comparison

### Case 2: Cross-Timezone Events
**Issue:** Event in UTC, request in local time
**Solution:** Convert both to UTC for comparison

### Case 3: Empty Window
**Issue:** transition_window_hours = 0
**Solution:** Only exact matches (delta == 0)

### Case 4: Multiple Events in Window
**Issue:** DST start and end both within 48 hours
**Solution:** Return all relevant events (list)

### Case 5: No Events in Dataset
**Issue:** Zone has no historical events
**Solution:** Return empty list (graceful)

---

## 6. Testing Strategy

### Unit Tests

**Test 1: Event Outside Window**
```python
def test_event_outside_window():
    detector = TimeEventDetector(transition_window_hours=48)
    request = TimeConversionRequest(
        instant=datetime(2000, 9, 14, 10, 0, 0),
        source_tz="Asia/Seoul",
        target_tz="UTC"
    )
    events = detector.detect(request)
    assert len(events) == 0, "1988 DST event should not be returned for 2000 request"
```

**Test 2: Event Within Window**
```python
def test_event_within_window():
    detector = TimeEventDetector(transition_window_hours=48)
    request = TimeConversionRequest(
        instant=datetime(1988, 5, 8, 2, 0, 0),  # DST start day
        source_tz="Asia/Seoul",
        target_tz="UTC"
    )
    events = detector.detect(request)
    assert len(events) >= 1, "Should return 1988 DST event"
    assert events[0].effective_from.year == 1988
```

**Test 3: Pyongyang Policy Event**
```python
def test_pyongyang_policy_event():
    detector = TimeEventDetector(transition_window_hours=48)
    request = TimeConversionRequest(
        instant=datetime(2015, 8, 15, 0, 0, 0),
        source_tz="Asia/Pyongyang",
        target_tz="UTC"
    )
    events = detector.detect(request)
    assert len(events) >= 1
    assert events[0].kind == "policy"
    assert "UTC+08:30" in events[0].notes
```

**Test 4: Multiple Events in Window**
```python
def test_multiple_events_in_window():
    detector = TimeEventDetector(transition_window_hours=24*30)  # 30 days
    request = TimeConversionRequest(
        instant=datetime(1987, 7, 1, 0, 0, 0),  # Between May and Oct DST
        source_tz="Asia/Seoul",
        target_tz="UTC"
    )
    events = detector.detect(request)
    # Should return both 1987-05-10 (start) and 1987-10-11 (end) if window is large enough
    assert len(events) >= 2
```

### Integration Tests

**Test 5: End-to-End Conversion**
```python
def test_conversion_with_relevant_events():
    converter = TimezoneConverter(
        tzdb_version="2025a",
        event_detector=TimeEventDetector(transition_window_hours=48)
    )
    request = TimeConversionRequest(
        instant=datetime(1988, 5, 8, 2, 0, 0),
        source_tz="Asia/Seoul",
        target_tz="UTC"
    )
    response = converter.convert(request)
    assert len(response.events) >= 1
    assert response.trace["flags"]["tzTransition"] is True
```

### Manual Verification

**Test 6: Historical Accuracy**
```bash
# Verify Seoul DST dates against historical records
python -c "
from services.tz_time_service.app.core.events import TimeEventDetector, KOREAN_TZ_EVENTS
for event in KOREAN_TZ_EVENTS:
    if event['iana'] == 'Asia/Seoul':
        print(f'{event[\"effective_from\"]}: {event[\"notes\"]}')
"
# Expected:
# 1987-05-10 02:00:00: 1987 DST start (+1 hour)
# 1987-10-11 03:00:00: 1987 DST end (-1 hour)
# 1988-05-08 02:00:00: 1988 DST start (+1 hour)
# 1988-10-09 03:00:00: 1988 DST end (-1 hour)
```

---

## 7. Risk Assessment

**Risk Level:** LOW
**Justification:**
- Changes only affect event filtering logic
- Hardcoded events remain as reference data
- Adds temporal relevance check (more restrictive)
- Reduces false positives (events outside window)

**Potential Issues:**
1. **Timezone-aware comparisons**: Need to ensure both datetimes are comparable
2. **Performance**: Iterating KOREAN_TZ_EVENTS on each request (acceptable for 6 events)
3. **Accuracy**: Historical DST dates must be verified against official records

**Mitigation:**
- Add tzinfo handling for naive datetimes
- Keep dataset small (6-10 events for Korean zones)
- Verify dates against IANA tzdata and Korean government records

---

## 8. Dependencies

**None**
This task is independent and can be completed without waiting for other tasks.

---

## 9. Success Criteria

1. ✅ KOREAN_TZ_EVENTS list created with 6 historical events
2. ✅ _is_relevant_event() method implemented with timezone-aware comparison
3. ✅ detect() method updated to filter events by temporal relevance
4. ✅ Naive datetime handling added (tzinfo check)
5. ✅ Seoul DST events (1987, 1988) only returned when within window
6. ✅ Pyongyang policy events (2015, 2018) only returned when within window
7. ✅ Test case: 2000-09-14 request returns empty list (no events)
8. ✅ Test case: 1988-05-08 request returns 1988 DST event
9. ✅ Test case: 2015-08-15 request returns Pyongyang policy event
10. ✅ All unit tests pass

---

## 10. Implementation Code

```python
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
        "notes": "1987 DST start (+1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1987, 10, 11, 3, 0, 0),
        "notes": "1987 DST end (-1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 5, 8, 2, 0, 0),
        "notes": "1988 DST start (+1 hour)"
    },
    {
        "iana": "Asia/Seoul",
        "kind": "dst",
        "effective_from": datetime(1988, 10, 9, 3, 0, 0),
        "notes": "1988 DST end (-1 hour)"
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2015, 8, 15, 0, 0, 0),
        "notes": "UTC+08:30 adoption (Pyongyang Time)"
    },
    {
        "iana": "Asia/Pyongyang",
        "kind": "policy",
        "effective_from": datetime(2018, 5, 5, 0, 0, 0),
        "notes": "UTC+09:00 reversion (reunification gesture)"
    },
]


@dataclass(slots=True)
class TimeEventDetector:
    """Inspect instants around timezone transitions (DST, historical policy)."""

    transition_window_hours: int = 48

    def _is_relevant_event(
        self,
        event_time: datetime,
        request_time: datetime
    ) -> bool:
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
            if not self._is_relevant_event(
                event_data["effective_from"],
                instant
            ):
                continue

            # Event is relevant - add to results
            relevant_events.append(TimeEvent(**event_data))

        return relevant_events
```

---

## 11. Timeline

**Total Estimated Time:** 2-3 hours

| Step | Task | Duration |
|------|------|----------|
| 1 | Create KOREAN_TZ_EVENTS dataset | 30 min |
| 2 | Implement _is_relevant_event() | 20 min |
| 3 | Update detect() method | 30 min |
| 4 | Add tzinfo handling | 15 min |
| 5 | Write unit tests | 45 min |
| 6 | Manual verification | 15 min |
| 7 | Integration testing | 20 min |
| 8 | Documentation | 15 min |

**Total:** 3 hours 10 minutes

---

## 12. Historical Event Sources

**Seoul DST (1987-1988):**
- Source: IANA tzdata, South Korean government records
- 1987: May 10 - October 11 (DST in effect)
- 1988: May 8 - October 9 (DST in effect)
- Accurate to local standard time (LST)

**Pyongyang Timezone Policy:**
- Source: KCNA (Korean Central News Agency), IANA tzdata
- 2015-08-15: Changed from UTC+09:00 to UTC+08:30 (Pyongyang Time)
- 2018-05-05: Reverted to UTC+09:00 (reunification gesture with South Korea)

**Verification:**
```bash
# Check IANA tzdata for Asia/Seoul
zdump -v Asia/Seoul | grep 1987
zdump -v Asia/Seoul | grep 1988

# Check Pyongyang timezone history
zdump -v Asia/Pyongyang | grep 2015
zdump -v Asia/Pyongyang | grep 2018
```

---

## 13. Next Steps

1. **Review:** Verify historical event dates against IANA tzdata
2. **Implement:** Apply code changes to events.py
3. **Test:** Run unit tests to verify filtering logic
4. **Verify:** Manual test with 2000-09-14 (should return empty)
5. **Verify:** Manual test with 1988-05-08 (should return DST event)
6. **Commit:** Create commit with "fix(tz-time): gate TimeEventDetector events by temporal window"

---

## Notes

- This fix aligns TimeEventDetector behavior with its documented intent (transition_window_hours)
- Reduces false positives by filtering out irrelevant historical events
- Maintains historical accuracy while improving relevance
- No breaking changes to API contract
- Can be extended later with more zones (Asia/Taipei, Asia/Tokyo, etc.)

---

**Status:** READY FOR IMPLEMENTATION
**Next Action:** Apply changes to `services/tz-time-service/app/core/events.py`
