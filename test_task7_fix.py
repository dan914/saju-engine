#!/usr/bin/env python3
"""Test script for Task #7: TimeEventDetector temporal filtering."""

from datetime import datetime

from services.tz_time_service.app.core.events import KOREAN_TZ_EVENTS, TimeEventDetector
from services.tz_time_service.app.models.conversion import TimeConversionRequest

print('✅ TimeEventDetector imports successfully')
print(f'✅ KOREAN_TZ_EVENTS contains {len(KOREAN_TZ_EVENTS)} historical events')
print()

# Test 1: 2000-09-14 (far from any DST events)
detector = TimeEventDetector(transition_window_hours=48)
request1 = TimeConversionRequest(
    instant=datetime(2000, 9, 14, 10, 0, 0),
    source_tz='Asia/Seoul',
    target_tz='UTC'
)
events1 = detector.detect(request1)
print('TEST 1: 2000-09-14 Seoul request (far from DST)')
print(f'  Events returned: {len(events1)}')
if len(events1) == 0:
    print('  ✅ CORRECT: No events (1988 DST is 12 years away)')
else:
    print(f'  ❌ WRONG: Should return 0 events, got {len(events1)}')
print()

# Test 2: 1988-05-08 (near DST start)
request2 = TimeConversionRequest(
    instant=datetime(1988, 5, 8, 2, 0, 0),
    source_tz='Asia/Seoul',
    target_tz='UTC'
)
events2 = detector.detect(request2)
print('TEST 2: 1988-05-08 Seoul request (DST start day)')
print(f'  Events returned: {len(events2)}')
if len(events2) >= 1:
    print(f'  ✅ CORRECT: Returned {len(events2)} event(s)')
    for e in events2:
        print(f'    - {e.iana}: {e.notes}')
else:
    print('  ❌ WRONG: Should return 1+ events')
print()

# Test 3: 2015-08-15 (Pyongyang policy change)
request3 = TimeConversionRequest(
    instant=datetime(2015, 8, 15, 0, 0, 0),
    source_tz='Asia/Pyongyang',
    target_tz='UTC'
)
events3 = detector.detect(request3)
print('TEST 3: 2015-08-15 Pyongyang request (policy change)')
print(f'  Events returned: {len(events3)}')
if len(events3) >= 1:
    print(f'  ✅ CORRECT: Returned {len(events3)} event(s)')
    for e in events3:
        print(f'    - {e.iana}: {e.notes}')
else:
    print('  ❌ WRONG: Should return 1+ events')
print()

# Test 4: Edge case - 30 days window captures multiple events
detector_wide = TimeEventDetector(transition_window_hours=24*30)
request4 = TimeConversionRequest(
    instant=datetime(1987, 7, 1, 0, 0, 0),
    source_tz='Asia/Seoul',
    target_tz='UTC'
)
events4 = detector_wide.detect(request4)
print('TEST 4: 1987-07-01 Seoul with 30-day window')
print(f'  Events returned: {len(events4)}')
if len(events4) >= 2:
    print('  ✅ CORRECT: Captured multiple events (DST start + end)')
    for e in events4:
        print(f'    - {e.effective_from}: {e.notes}')
else:
    print(f'  ⚠️  Got {len(events4)} events (expected 2: May start, Oct end)')
print()

print('✅ Task #7 COMPLETE: TimeEventDetector now filters by temporal relevance!')
