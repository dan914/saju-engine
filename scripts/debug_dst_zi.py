#!/usr/bin/env python3
"""Debug DST + zi hour interaction."""

from datetime import datetime, timedelta

# Test case: 1987-05-10 23:15 (during DST)
birth_dt_original = datetime(1987, 5, 10, 23, 15)
print(f"Original input: {birth_dt_original}")
print(f"Original hour: {birth_dt_original.hour}")
print()

# Check DST
DST_PERIODS = [
    (datetime(1987, 5, 10, 2), datetime(1987, 10, 11, 3)),
]

birth_dt = birth_dt_original
for start, end in DST_PERIODS:
    if start <= birth_dt < end:
        print(f"In DST period: {start} to {end}")
        birth_dt = birth_dt - timedelta(hours=1)
        print(f"After DST -1hr: {birth_dt}")
        print(f"Post-DST hour: {birth_dt.hour}")
        break

print()
print("Question: Should we check zi hour BEFORE or AFTER DST adjustment?")
print(f"  - Check birth_dt_original.hour (23): Would trigger zi rule ✓")
print(f"  - Check birth_dt.hour (22): Would NOT trigger zi rule ✗")
