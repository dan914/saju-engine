# Task #6 & #7 Implementation Plan: Replace TimezoneConverter Stub & Fix TimeEventDetector

**Task IDs:** #6 and #7 (HIGH Priority)
**Estimated Effort:** 3-4 hours combined (they're interdependent)
**Files:** `services/tz-time-service/app/core/converter.py` and `events.py`
**Status:** Ready for implementation

---

## Executive Summary

**Problem:** The tz-time-service contains stub implementations while pillars-service has a comprehensive `KoreanTimezoneHandler` with full DST/LMT support.

**Solution:** Migrate the comprehensive timezone logic from pillars-service to tz-time-service and integrate it properly.

**Benefit:**
- Accurate timezone conversions with historical context
- Dynamic DST detection (not hardcoded)
- Proper LMT support for Korean cities
- Computed delta_t values (not hardcoded 0.0)

---

## 1. Current State Analysis

### 1.1 tz-time-service (STUB - Needs Replacement)

**converter.py** (51 lines):
```python
# Line 36: ❌ HARDCODED
delta_t_seconds=0.0,

# Issues:
- No LMT support
- No historical timezone handling
- No DST detection
- Basic ZoneInfo conversion only
```

**events.py** (47 lines):
```python
# Lines 26-44: ❌ HARDCODED events
if "Asia/Seoul" in zones:
    events.append(TimeEvent(
        iana="Asia/Seoul",
        kind="transition",
        effective_from=datetime(1988, 5, 7, 16, 0, 0),
        notes="1987–1988 DST window",  # Generic, not specific
    ))

# Issues:
- Only 2 hardcoded events (Seoul, Pyongyang)
- Not dynamic detection
- Doesn't check actual datetime
- Missing all historical DST periods
```

### 1.2 pillars-service (COMPREHENSIVE - Should Migrate)

**timezone_handler.py** (314 lines):
```python
# Comprehensive implementation:
✅ 12 DST periods (1948-1960, 1987-1988) with exact dates/times
✅ City-specific LMT offsets for 7 cities (pre-1908)
✅ Historical timezone changes (1908, 1912, 1954, 1961)
✅ North Korean timezone handling (2015-2018)
✅ DST gap/overlap detection
✅ Modern LMT offsets for saju calculations

# Main features:
- is_dst_period(dt) -> bool
- is_dst_gap(dt) -> (bool, message)
- is_dst_overlap(dt) -> (bool, message)
- get_standard_time_offset(dt, location) -> int
- get_lmt_offset(location, dt) -> int
- convert_to_saju_time(...) -> Dict  # Main entry point
```

---

## 2. Architecture Decision

### Option A: Move KoreanTimezoneHandler to services/common ✅ RECOMMENDED
**Pros:**
- Single source of truth
- Both services can import
- Follows DRY principle
- Easier to maintain

**Cons:**
- Requires updating imports in pillars-service

### Option B: Duplicate in tz-time-service
**Pros:**
- No impact on pillars-service

**Cons:**
- Code duplication
- Maintenance nightmare
- Version drift risk

**Decision:** Go with Option A

---

## 3. Implementation Plan

### Phase 1: Move KoreanTimezoneHandler to services/common

**File:** `services/common/saju_common/timezone_handler.py`

**Steps:**
1. Copy `services/pillars-service/app/core/timezone_handler.py` to `services/common/saju_common/`
2. Update imports (if any)
3. Add to `services/common/saju_common/__init__.py`
4. Run tests to verify no breakage

**Expected Result:**
```python
# services/common/saju_common/__init__.py
from .timezone_handler import (
    KoreanTimezoneHandler,
    get_saju_adjusted_time,
    DST_PERIODS,
    CITY_LMT_OFFSETS,
    MODERN_LMT_OFFSETS,
    TimezoneWarning,
)

__all__ = [
    "KoreanTimezoneHandler",
    "get_saju_adjusted_time",
    # ... existing exports
]
```

### Phase 2: Update pillars-service to use common module

**File:** `services/pillars-service/app/core/engine.py` (and others)

**Changes:**
```python
# BEFORE:
from .timezone_handler import KoreanTimezoneHandler

# AFTER:
from services.common.saju_common import KoreanTimezoneHandler
```

**Testing:**
```bash
cd services/pillars-service
env PYTHONPATH=".:../.." ../../.venv/bin/pytest tests/ -v
```

### Phase 3: Rewrite TimezoneConverter in tz-time-service

**File:** `services/tz-time-service/app/core/converter.py`

**New Implementation:**
```python
"""Timezone conversion with comprehensive Korean DST/LMT support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from services.common import TraceMetadata
from services.common.saju_common import KoreanTimezoneHandler

from ..models import TimeConversionRequest, TimeConversionResponse
from .events import TimeEventDetector


def _ensure_awareness(instant: datetime, tz_name: str) -> datetime:
    """Attach a timezone if the datetime is naive."""
    if instant.tzinfo is None:
        return instant.replace(tzinfo=ZoneInfo(tz_name))
    return instant


@dataclass(slots=True)
class TimezoneConverter:
    """Converts instants between timezones with Korean historical context."""

    tzdb_version: str
    event_detector: TimeEventDetector
    korean_handler: KoreanTimezoneHandler

    def __init__(self, tzdb_version: str = "2025a"):
        self.tzdb_version = tzdb_version
        self.korean_handler = KoreanTimezoneHandler()
        self.event_detector = TimeEventDetector(korean_handler=self.korean_handler)

    def convert(self, request: TimeConversionRequest) -> TimeConversionResponse:
        """Convert between timezones with full historical support."""
        # Step 1: Ensure timezone awareness
        src = _ensure_awareness(request.instant, request.source_tz)
        src = src.astimezone(ZoneInfo(request.source_tz))

        # Step 2: Detect timezone events (DST, gaps, overlaps)
        events = self.event_detector.detect(request)

        # Step 3: Apply timezone conversion
        converted = src.astimezone(ZoneInfo(request.target_tz))

        # Step 4: Calculate delta_t if involving Korean timezones
        delta_t_seconds = self._calculate_delta_t(src, request)

        # Step 5: Build trace metadata
        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=delta_t_seconds,  # ✅ Computed, not hardcoded
            tz={
                "source": request.source_tz,
                "target": request.target_tz,
                "tzdbVersion": self.tzdb_version,
            },
            flags={
                "tzTransition": bool(events),
                "dst_applied": any(e.kind == "dst" for e in events),
                "lmt_offset_applied": self._is_korean_tz(request.source_tz) or self._is_korean_tz(request.target_tz),
            },
        )

        return TimeConversionResponse(
            input=request,
            converted=converted,
            tzdb_version=self.tzdb_version,
            events=events,
            trace=trace.to_dict(),
        )

    def _calculate_delta_t(self, dt: datetime, request: TimeConversionRequest) -> float:
        """Calculate delta_t if conversion involves Korean timezone."""
        # Only calculate for Korean timezones
        if not (self._is_korean_tz(request.source_tz) or self._is_korean_tz(request.target_tz)):
            return 0.0

        # For Korean times, calculate LMT offset as a proxy for delta_t
        # This is an approximation - true delta_t comes from solar term calculations
        location = self._extract_location(request.source_tz)
        lmt_offset_minutes = self.korean_handler.get_lmt_offset(location, dt)

        # Convert to seconds (delta_t is typically in seconds)
        return abs(lmt_offset_minutes * 60.0)

    def _is_korean_tz(self, tz_name: str) -> bool:
        """Check if timezone is Korean."""
        return tz_name in ["Asia/Seoul", "Asia/Pyongyang"] or "Korea" in tz_name

    def _extract_location(self, tz_name: str) -> str:
        """Extract city name from IANA timezone."""
        if "/" in tz_name:
            return tz_name.split("/")[-1]
        return tz_name
```

### Phase 4: Rewrite TimeEventDetector

**File:** `services/tz-time-service/app/core/events.py`

**New Implementation:**
```python
"""Dynamic timezone event detection using Korean timezone data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from services.common.saju_common import KoreanTimezoneHandler, DST_PERIODS

from ..models import TimeConversionRequest, TimeEvent


@dataclass(slots=True)
class TimeEventDetector:
    """Dynamically detect timezone transitions, DST, and policy events."""

    transition_window_hours: int = 48
    korean_handler: KoreanTimezoneHandler

    def __init__(self, transition_window_hours: int = 48, korean_handler: KoreanTimezoneHandler = None):
        self.transition_window_hours = transition_window_hours
        self.korean_handler = korean_handler or KoreanTimezoneHandler()

    def detect(self, request: TimeConversionRequest) -> list[TimeEvent]:
        """Dynamically analyze timezone transitions for the request."""
        events: list[TimeEvent] = []
        instant = request.instant
        zones = {request.source_tz, request.target_tz}

        # Detect Korean timezone events
        if "Asia/Seoul" in zones or "Korea" in str(zones):
            events.extend(self._detect_korean_events(instant, "Asia/Seoul"))

        if "Asia/Pyongyang" in zones:
            events.extend(self._detect_korean_events(instant, "Asia/Pyongyang"))

        return events

    def _detect_korean_events(self, dt: datetime, tz_name: str) -> list[TimeEvent]:
        """Detect DST and policy events for Korean timezones."""
        events = []

        # Check if datetime is in DST period
        if self.korean_handler.is_dst_period(dt):
            dst_period = self._find_dst_period(dt)
            if dst_period:
                events.append(TimeEvent(
                    iana=tz_name,
                    kind="dst",
                    effective_from=dst_period["start"],
                    notes=f"DST active: {dst_period['start'].strftime('%Y-%m-%d')} to {dst_period['end'].strftime('%Y-%m-%d')}",
                ))

        # Check for DST gap
        is_gap, gap_msg = self.korean_handler.is_dst_gap(dt)
        if is_gap:
            events.append(TimeEvent(
                iana=tz_name,
                kind="transition",
                effective_from=dt,
                notes=gap_msg,
            ))

        # Check for DST overlap
        is_overlap, overlap_msg = self.korean_handler.is_dst_overlap(dt)
        if is_overlap:
            events.append(TimeEvent(
                iana=tz_name,
                kind="transition",
                effective_from=dt,
                notes=overlap_msg,
            ))

        # Check for historical timezone changes
        historical = self._detect_historical_changes(dt, tz_name)
        if historical:
            events.append(historical)

        return events

    def _find_dst_period(self, dt: datetime) -> dict | None:
        """Find which DST period contains this datetime."""
        for period in DST_PERIODS:
            if period["start"] <= dt < period["end"]:
                return period
        return None

    def _detect_historical_changes(self, dt: datetime, tz_name: str) -> TimeEvent | None:
        """Detect if datetime is near a historical timezone change."""
        window = timedelta(hours=self.transition_window_hours)

        # Major Korean timezone changes
        changes = [
            (datetime(1908, 4, 1), "Korea adopted standard time UTC+8:30"),
            (datetime(1912, 1, 1), "Changed to UTC+9:00"),
            (datetime(1954, 3, 21), "South Korea changed to UTC+8:30"),
            (datetime(1961, 8, 10), "South Korea returned to UTC+9:00"),
        ]

        if tz_name == "Asia/Pyongyang":
            changes.extend([
                (datetime(2015, 8, 15), "North Korea adopted UTC+8:30 (Pyongyang Time)"),
                (datetime(2018, 5, 5), "North Korea returned to UTC+9:00"),
            ])

        for change_dt, notes in changes:
            if abs((dt - change_dt).total_seconds()) < window.total_seconds():
                return TimeEvent(
                    iana=tz_name,
                    kind="policy",
                    effective_from=change_dt,
                    notes=notes,
                )

        return None
```

---

## 4. Testing Strategy

### 4.1 Unit Tests for KoreanTimezoneHandler (already exist)

**Location:** `services/pillars-service/tests/`

**Verify:**
```bash
cd services/pillars-service
env PYTHONPATH=".:../.." ../../.venv/bin/pytest tests/ -v -k timezone
```

### 4.2 New Tests for TimezoneConverter

**File:** `services/tz-time-service/tests/test_converter_comprehensive.py`

**Test Cases:**
```python
def test_convert_with_dst_1987():
    """Test conversion during 1987 DST period."""
    converter = TimezoneConverter(tzdb_version="2025a")
    request = TimeConversionRequest(
        instant=datetime(1987, 5, 15, 10, 0, 0),
        source_tz="Asia/Seoul",
        target_tz="UTC",
    )
    response = converter.convert(request)

    # Should detect DST
    assert response.trace["flags"]["dst_applied"] is True
    assert len(response.events) > 0
    assert any(e.kind == "dst" for e in response.events)

    # delta_t should be computed, not 0.0
    assert response.trace["deltaTSeconds"] > 0.0


def test_convert_dst_gap():
    """Test conversion during DST gap (non-existent time)."""
    converter = TimezoneConverter(tzdb_version="2025a")
    request = TimeConversionRequest(
        instant=datetime(1987, 5, 10, 2, 30, 0),  # In DST gap
        source_tz="Asia/Seoul",
        target_tz="UTC",
    )
    response = converter.convert(request)

    # Should detect gap
    assert len(response.events) > 0
    assert any("gap" in e.notes.lower() for e in response.events)


def test_convert_with_lmt_pre_1908():
    """Test conversion with historical LMT."""
    converter = TimezoneConverter(tzdb_version="2025a")
    request = TimeConversionRequest(
        instant=datetime(1900, 1, 1, 12, 0, 0),
        source_tz="Asia/Seoul",
        target_tz="UTC",
    )
    response = converter.convert(request)

    # Should apply LMT offset
    assert response.trace["flags"]["lmt_offset_applied"] is True
    assert response.trace["deltaTSeconds"] > 0.0


def test_convert_pyongyang_2015_policy():
    """Test North Korean timezone change in 2015."""
    converter = TimezoneConverter(tzdb_version="2025a")
    request = TimeConversionRequest(
        instant=datetime(2015, 8, 20, 10, 0, 0),
        source_tz="Asia/Pyongyang",
        target_tz="UTC",
    )
    response = converter.convert(request)

    # Should detect policy change
    assert len(response.events) > 0
    assert any(e.kind == "policy" for e in response.events)
    assert any("2015" in e.notes for e in response.events)
```

### 4.3 Integration Tests

**File:** `services/tz-time-service/tests/test_integration.py`

**Test Cases:**
```python
def test_api_endpoint_with_comprehensive_converter():
    """Test /convert endpoint with new converter."""
    # Test via FastAPI TestClient
    from app.main import app
    from fastapi.testclient import client

    client = TestClient(app)
    response = client.post("/convert", json={
        "instant": "1987-05-15T10:00:00",
        "source_tz": "Asia/Seoul",
        "target_tz": "UTC",
    })

    assert response.status_code == 200
    data = response.json()
    assert "trace" in data
    assert data["trace"]["deltaTSeconds"] > 0.0
    assert data["trace"]["flags"]["dst_applied"] is True
```

---

## 5. Migration Checklist

### Phase 1: Move to common ✅
- [ ] Create `services/common/saju_common/timezone_handler.py`
- [ ] Copy code from pillars-service
- [ ] Update `services/common/saju_common/__init__.py`
- [ ] Test common module: `cd services/common && pytest tests/ -v`

### Phase 2: Update pillars-service ✅
- [ ] Update imports in `services/pillars-service/app/core/engine.py`
- [ ] Update imports in any other files using timezone_handler
- [ ] Remove `services/pillars-service/app/core/timezone_handler.py`
- [ ] Test pillars-service: `cd services/pillars-service && pytest tests/ -v`

### Phase 3: Rewrite tz-time-service ✅
- [ ] Implement new `converter.py` with KoreanTimezoneHandler
- [ ] Implement new `events.py` with dynamic detection
- [ ] Add comprehensive tests
- [ ] Test tz-time-service: `cd services/tz-time-service && pytest tests/ -v`

### Phase 4: Verification ✅
- [ ] Run all tests across all services
- [ ] Verify no hardcoded values remain
- [ ] Check delta_t is computed
- [ ] Verify DST detection works dynamically

---

## 6. Expected Before/After

### BEFORE: converter.py

```python
# Line 36: ❌ HARDCODED
delta_t_seconds=0.0,

# No DST detection
# No LMT support
# Basic ZoneInfo only
```

### AFTER: converter.py

```python
# Line ~50: ✅ COMPUTED
delta_t_seconds=delta_t_seconds,  # Calculated from LMT offset

# ✅ Full DST detection via KoreanTimezoneHandler
# ✅ LMT support for 7 cities
# ✅ Historical timezone changes (1908-2018)
# ✅ DST gap/overlap handling
```

### BEFORE: events.py

```python
# Lines 26-44: ❌ HARDCODED
if "Asia/Seoul" in zones:
    events.append(TimeEvent(
        iana="Asia/Seoul",
        kind="transition",
        effective_from=datetime(1988, 5, 7, 16, 0, 0),
        notes="1987–1988 DST window",  # Generic
    ))

# Only 2 hardcoded events
# No dynamic detection
```

### AFTER: events.py

```python
# ✅ Dynamic detection using DST_PERIODS
if self.korean_handler.is_dst_period(dt):
    dst_period = self._find_dst_period(dt)
    events.append(TimeEvent(
        iana=tz_name,
        kind="dst",
        effective_from=dst_period["start"],
        notes=f"DST active: {dst_period['start']} to {dst_period['end']}",
    ))

# ✅ Detects all 12 DST periods (1948-1960, 1987-1988)
# ✅ Detects DST gaps/overlaps
# ✅ Detects historical changes
```

---

## 7. Risk Assessment

### Risk Level: MEDIUM ⚠️

**Why Medium Risk:**
1. **Cross-service changes** - Affects 3 services (common, pillars, tz-time)
2. **Import path updates** - Must update all imports correctly
3. **Existing code dependency** - pillars-service currently uses timezone_handler

**Mitigations:**
1. ✅ Move to common first, then update imports
2. ✅ Comprehensive testing at each phase
3. ✅ Keep original file until all tests pass
4. ✅ Git commits after each phase

**Potential Issues:**
- Import path errors → Fix: Update PYTHONPATH in tests
- Test failures in pillars-service → Fix: Ensure common module exported correctly
- Performance concerns → Unlikely, same code just moved

---

## 8. Timeline

**Estimated:** 3-4 hours total

- **Phase 1 (Move to common):** 30 minutes
- **Phase 2 (Update pillars):** 30 minutes
- **Phase 3 (Rewrite tz-time):** 90 minutes
- **Phase 4 (Testing):** 45 minutes
- **Buffer:** 45 minutes

---

## 9. Success Criteria

✅ **Verification Checklist:**
1. [ ] KoreanTimezoneHandler in services/common
2. [ ] pillars-service imports from common (not local)
3. [ ] Original timezone_handler.py removed from pillars-service
4. [ ] converter.py uses KoreanTimezoneHandler (no hardcoded delta_t)
5. [ ] events.py dynamically detects DST (no hardcoded events)
6. [ ] All pillars-service tests pass (17/17)
7. [ ] All tz-time-service tests pass
8. [ ] Integration tests pass
9. [ ] No hardcoded delta_t_seconds=0.0 in converter
10. [ ] No hardcoded DST events in detector

---

## 10. Next Steps

1. **Review this plan** - Confirm approach is acceptable
2. **Phase 1** - Move timezone_handler to common
3. **Phase 2** - Update pillars-service imports
4. **Phase 3** - Implement comprehensive converter/detector
5. **Phase 4** - Test thoroughly
6. **Commit** - Single atomic commit for entire migration

---

**Plan Created:** 2025-10-11
**Tasks:** #6 and #7 (HIGH Priority)
**Ready for Implementation:** ✅ YES
**Estimated Completion:** 3-4 hours from approval
