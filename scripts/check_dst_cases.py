#!/usr/bin/env python3
"""
Check what's happening with DST cases H01 and H02.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from calculate_pillars_traditional import calculate_four_pillars

dst_cases = [
    ("H01", datetime(1987, 5, 10, 2, 30), "1987 DST start gap"),
    ("H02", datetime(1988, 5, 8, 2, 30), "1988 DST start gap"),
]

print("=" * 120)
print("DST CASE ANALYSIS - What's happening?")
print("=" * 120)
print()

for test_id, birth_dt, note in dst_cases:
    # Create timezone-aware datetime
    tz = ZoneInfo("Asia/Seoul")
    birth_dt_tz = birth_dt.replace(tzinfo=tz)

    print(f"{test_id} | {note}")
    print(f"  Input time:     {birth_dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"  UTC offset:     {birth_dt_tz.strftime('%z')} ({birth_dt_tz.tzname()})")

    # Calculate pillars
    result = calculate_four_pillars(
        birth_dt, tz_str="Asia/Seoul", mode="traditional_kr", return_metadata=True
    )

    meta = result["metadata"]
    lmt_time = meta["lmt_adjusted_time"]
    lmt_hour = int(lmt_time[11:13])

    print(f"  LMT adjusted:   {lmt_time}")
    print(f"  LMT hour:       {lmt_hour:02d}")
    print(f"  Hour branch:    {result['hour']}")

    # Check what hour branch should be
    hour_branches = {
        (23, 1): "子",
        (1, 3): "丑",
        (3, 5): "寅",
        (5, 7): "卯",
        (7, 9): "辰",
        (9, 11): "巳",
        (11, 13): "午",
        (13, 15): "未",
        (15, 17): "申",
        (17, 19): "酉",
        (19, 21): "戌",
        (21, 23): "亥",
    }

    expected_branch = None
    for (start, end), branch in hour_branches.items():
        if start <= lmt_hour < end:
            expected_branch = branch
            break

    print(f"  Expected branch: {expected_branch} (hour {lmt_hour} → {start}-{end})")
    print(f"  Engine result:   {result['year']} {result['month']} {result['day']} {result['hour']}")
    print()

print("=" * 120)
print("NOTES:")
print("- Korea had DST 1987-1988 (clocks forward 1 hour)")
print("- DST start: May 10/8, 00:00 → 01:00 (2:00-3:00 doesn't exist)")
print("- Our engine ignores DST, just uses standard time + LMT")
print("- FortuneTeller might be accounting for DST differently")
print("=" * 120)
