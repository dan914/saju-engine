#!/usr/bin/env python3
"""Debug 23:30 case."""

from datetime import datetime, timedelta

# Test case 1: 2000-09-14 23:30
print("=== Case 1: 2000-09-14 23:30 ===")
birth_dt = datetime(2000, 9, 14, 23, 30)
lmt_offset_minutes = -32

print(f"Original birth time: {birth_dt}")
print(f"Original hour: {birth_dt.hour}")
print(f"LMT offset: {lmt_offset_minutes} minutes")

# Apply LMT
lmt_adjusted = birth_dt - timedelta(minutes=abs(lmt_offset_minutes))
print(f"After LMT adjustment: {lmt_adjusted}")
print(f"LMT-adjusted hour: {lmt_adjusted.hour}")
print(f"Is hour == 23? {lmt_adjusted.hour == 23}")
print()

# Test case 2: 1987-05-10 23:15 (DST period)
print("=== Case 2: 1987-05-10 23:15 (DST) ===")
birth_dt2 = datetime(1987, 5, 10, 23, 15)
print(f"Original birth time: {birth_dt2}")
print(f"Original hour: {birth_dt2.hour}")

# Check if in DST
DST_PERIODS = [
    (datetime(1987, 5, 10, 2), datetime(1987, 10, 11, 3)),
]
for start, end in DST_PERIODS:
    if start <= birth_dt2 < end:
        print(f"In DST period: {start} to {end}")
        birth_dt2_dst = birth_dt2 - timedelta(hours=1)
        print(f"After DST -1hr: {birth_dt2_dst}")
        break

# Apply LMT
lmt_adjusted2 = birth_dt2_dst - timedelta(minutes=abs(lmt_offset_minutes))
print(f"After LMT -32min: {lmt_adjusted2}")
print(f"LMT-adjusted hour: {lmt_adjusted2.hour}")
print(f"Is hour == 23? {lmt_adjusted2.hour == 23}")
