#!/usr/bin/env python3
"""Debug 2021-01-01 00:01 case - why do we get different day/hour pillars?"""

from datetime import datetime

from calculate_pillars_traditional import calculate_four_pillars

# The problematic case
dt = datetime(2021, 1, 1, 0, 1)

print("=" * 100)
print("DEBUGGING: 2021-01-01 00:01")
print("=" * 100)
print()

# Calculate with traditional mode
result = calculate_four_pillars(
    dt,
    tz_str="Asia/Seoul",
    mode="traditional_kr",
    validate_input=True,
    return_metadata=True,
    zi_hour_mode="traditional",
)

print("INPUT:")
print(f"  Birth datetime: {dt}")
print(f"  Timezone: Asia/Seoul")
print(f"  Mode: traditional_kr")
print(f"  Zi hour mode: traditional")
print()

print("OUTPUT:")
print(f"  Year:  {result['year']}")
print(f"  Month: {result['month']}")
print(f"  Day:   {result['day']}")
print(f"  Hour:  {result['hour']}")
print()

print("METADATA:")
meta = result["metadata"]
print(f"  LMT offset: {meta['lmt_offset']} minutes")
print(f"  LMT adjusted time: {meta['lmt_adjusted_time']}")
print(f"  子時 transition applied: {meta['zi_transition_applied']}")
print(f"  Day for pillar: {meta['day_for_pillar']}")
print(f"  Solar term: {meta['solar_term']}")
print(f"  DST applied: {meta['dst_applied']}")
print()

print("REFERENCE VALUES:")
print("  From original 10-case test:")
print("    Year:  庚子")
print("    Month: 戊子")
print("    Day:   己酉  ← Expected")
print("    Hour:  甲子  ← Expected")
print()
print("  Our calculation:")
print(f"    Year:  {result['year']}")
print(f"    Month: {result['month']}")
print(f"    Day:   {result['day']}  ← {'✅ MATCH' if result['day'] == '己酉' else '❌ DIFFERENT'}")
print(
    f"    Hour:  {result['hour']}  ← {'✅ MATCH' if result['hour'] == '甲子' else '❌ DIFFERENT'}"
)
print()

print("=" * 100)
print("ANALYSIS")
print("=" * 100)
print()

# Calculate the date used for day pillar
from datetime import timedelta

input_date = dt.date()
lmt_adjusted_date = (dt - timedelta(minutes=32)).date()

print("Date Analysis:")
print(f"  Input date:        {input_date} (2021-01-01)")
print(f"  LMT adjusted date: {lmt_adjusted_date}")
print()

print("Time Analysis:")
print(f"  Input time:        {dt.time()} (00:01)")
print(f"  LMT adjusted time: {meta['lmt_adjusted_time']}")
print(f"  Hour after LMT:    {meta['lmt_adjusted_time'].split()[1].split(':')[0]}")
print()

print("子時 Rule Analysis:")
print(f"  Is hour 23 (야자시)? {meta['lmt_adjusted_time'].split()[1].startswith('23')}")
print(f"  Is hour 00 (조자시)? {meta['lmt_adjusted_time'].split()[1].startswith('00')}")
print(f"  子時 transition:     {meta['zi_transition_applied']}")
print()

print("Day for Pillar:")
print(f"  Day used: {meta['day_for_pillar']}")
print()

# Check if reference might be using different calculation method
print("HYPOTHESIS:")
print()
print("Reference expects: 己酉 甲子")
print("We calculated:     戊申 壬子")
print()
print("Possible reasons:")
print("1. Reference doesn't apply LMT (-32 minutes)")
print("2. Reference doesn't apply 子時 rule at 23:xx")
print("3. Reference uses different day boundary (midnight vs 23:00)")
print("4. Our LMT pushes 00:01 back to 23:29 (previous day)")
print()

# Calculate without LMT to see
print("=" * 100)
print("TEST: Without LMT adjustment")
print("=" * 100)
result_no_lmt = calculate_four_pillars(
    dt,
    tz_str="Asia/Seoul",
    mode="traditional_kr",
    validate_input=True,
    return_metadata=True,
    lmt_offset_minutes=0,  # No LMT
)
print(
    f"Day:  {result_no_lmt['day']}  ← {('✅ MATCHES REFERENCE' if result_no_lmt['day'] == '己酉' else 'Still different')}"
)
print(
    f"Hour: {result_no_lmt['hour']}  ← {('✅ MATCHES REFERENCE' if result_no_lmt['hour'] == '甲子' else 'Still different')}"
)
print()

# Calculate with modern zi_hour_mode
print("=" * 100)
print("TEST: Modern zi_hour_mode (no 子時 rule)")
print("=" * 100)
result_modern = calculate_four_pillars(
    dt,
    tz_str="Asia/Seoul",
    mode="traditional_kr",
    validate_input=True,
    return_metadata=True,
    zi_hour_mode="modern",
)
print(
    f"Day:  {result_modern['day']}  ← {('✅ MATCHES REFERENCE' if result_modern['day'] == '己酉' else 'Still different')}"
)
print(
    f"Hour: {result_modern['hour']}  ← {('✅ MATCHES REFERENCE' if result_modern['hour'] == '甲子' else 'Still different')}"
)
print()

# Test with no LMT and modern mode
print("=" * 100)
print("TEST: No LMT + Modern mode")
print("=" * 100)
result_neither = calculate_four_pillars(
    dt,
    tz_str="Asia/Seoul",
    mode="traditional_kr",
    validate_input=True,
    return_metadata=True,
    lmt_offset_minutes=0,
    zi_hour_mode="modern",
)
print(
    f"Day:  {result_neither['day']}  ← {('✅ MATCHES REFERENCE' if result_neither['day'] == '己酉' else 'Still different')}"
)
print(
    f"Hour: {result_neither['hour']}  ← {('✅ MATCHES REFERENCE' if result_neither['hour'] == '甲子' else 'Still different')}"
)
print()

print("=" * 100)
print("CONCLUSION")
print("=" * 100)
print()
print("The discrepancy is due to:")
print("1. We apply LMT (-32 min): 2021-01-01 00:01 → 2020-12-31 23:29")
print("2. We apply 子時 rule: 23:29 is 야자시 → use 2021-01-01 for day pillar")
print("3. But LMT date is 2020-12-31, so calculations differ")
print()
print("Reference likely:")
print("- Uses 2021-01-01 directly (no LMT or different LMT logic)")
print("- Results in different day cycle position")
