#!/usr/bin/env python3
"""Debug zi hour mode logic."""

from datetime import datetime, timedelta

# Test case: 2000-09-14 00:30
birth_dt = datetime(2000, 9, 14, 0, 30)
lmt_offset_minutes = -32

print(f"Original birth time: {birth_dt}")
print(f"LMT offset: {lmt_offset_minutes} minutes")

# Apply LMT
lmt_adjusted = birth_dt - timedelta(minutes=abs(lmt_offset_minutes))
print(f"After LMT adjustment: {lmt_adjusted}")
print(f"LMT-adjusted hour: {lmt_adjusted.hour}")
print()

# Traditional mode logic
print("=== TRADITIONAL MODE ===")
if lmt_adjusted.hour == 23:
    day_for_pillar = lmt_adjusted.date() + timedelta(days=1)
    zi_applied = True
    print(f"Hour is 23 → 야자시 → Use next day: {day_for_pillar}")
else:
    day_for_pillar = lmt_adjusted.date()
    zi_applied = False
    print(f"Hour is {lmt_adjusted.hour} → Use current day: {day_for_pillar}")

print()
print("=== MODERN MODE ===")
day_for_pillar_modern = lmt_adjusted.date()
print(f"No special handling → Use current day: {day_for_pillar_modern}")
