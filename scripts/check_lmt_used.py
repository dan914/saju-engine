#!/usr/bin/env python3
"""Check what LMT offset was actually used in the test results."""

from datetime import datetime

from calculate_pillars_traditional import calculate_four_pillars

# Test cases with different cities
test_cases = [
    ("N02", datetime(1993, 3, 21, 18, 45), "Asia/Seoul", "Busan"),
    ("N03", datetime(2012, 12, 12, 12, 12), "Asia/Seoul", "Incheon"),
    ("N04", datetime(1984, 6, 1, 9, 30), "Asia/Seoul", "Daegu"),
    ("N05", datetime(2023, 5, 5, 5, 5), "Asia/Seoul", "Daejeon"),
]

print("=" * 100)
print("LMT OFFSET CHECK - What was actually used?")
print("=" * 100)

for test_id, birth_dt, tz, city in test_cases:
    result = calculate_four_pillars(
        birth_dt, tz_str=tz, mode="traditional_kr", return_metadata=True
    )

    meta = result["metadata"]
    lmt_offset = meta["lmt_offset"]
    lmt_time = meta["lmt_adjusted_time"]

    print(
        f"{test_id} | {city:10} | TZ: {tz:12} | LMT offset: {lmt_offset:3} min | "
        f"Input: {birth_dt.strftime('%H:%M')} → LMT: {lmt_time[11:16]}"
    )

print("=" * 100)
print("\nNote: All used Asia/Seoul timezone in input CSV, not city-specific timezones")
print("Expected LMT offsets if city-specific:")
print("  Seoul:   -32 min (126.978°E)")
print("  Busan:   -24 min (129.075°E)")
print("  Incheon: -32 min (126.711°E)")
print("  Daegu:   -27 min (128.601°E)")
print("  Daejeon: -31 min (127.385°E)")
