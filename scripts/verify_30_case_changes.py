#!/usr/bin/env python3
"""
Verify which 30-case results actually changed from the fix.
Compare current results with expected behavior.
"""

from datetime import datetime, timedelta

from calculate_pillars_traditional import calculate_four_pillars


def analyze_case(test_id, dt, description):
    """Analyze if a case's zi hour check differs between clock and LMT."""

    result = calculate_four_pillars(
        birth_dt=dt,
        tz_str="Asia/Seoul",
        mode="traditional_kr",
        validate_input=True,
        return_metadata=True,
        zi_hour_mode="traditional",
    )

    if "error" in result:
        return None

    metadata = result["metadata"]

    # Original clock hour
    clock_hour = dt.hour

    # LMT-adjusted hour
    lmt_adjusted_str = metadata.get("lmt_adjusted_time", "")
    if lmt_adjusted_str:
        lmt_dt = datetime.strptime(lmt_adjusted_str, "%Y-%m-%d %H:%M:%S")
        lmt_hour = lmt_dt.hour
    else:
        lmt_hour = None

    # Check if zi logic would differ
    clock_would_apply_zi = clock_hour == 23
    lmt_would_apply_zi = (lmt_hour == 23) if lmt_hour is not None else False

    changed = clock_would_apply_zi != lmt_would_apply_zi

    return {
        "id": test_id,
        "dt": dt,
        "description": description,
        "clock_hour": clock_hour,
        "lmt_hour": lmt_hour,
        "clock_zi": clock_would_apply_zi,
        "lmt_zi": lmt_would_apply_zi,
        "changed": changed,
        "zi_applied": metadata.get("zi_transition_applied", False),
        "result": f"{result['year']} {result['month']} {result['day']} {result['hour']}",
    }


# 30-case test suite
cases = [
    ("N01", datetime(2000, 9, 14, 10, 0), "normal_daytime"),
    ("N02", datetime(2001, 9, 3, 3, 7), "normal_early_morning"),
    ("N03", datetime(2016, 2, 29, 0, 37), "leap_day_midnight"),
    ("N04", datetime(2024, 11, 7, 6, 5), "recent_morning"),
    ("N05", datetime(2023, 8, 7, 0, 0), "midnight_exact"),
    ("N06", datetime(1999, 12, 31, 23, 30), "nye_late_night"),
    ("N07", datetime(2007, 12, 29, 17, 53), "reference_set_case"),
    ("N08", datetime(2013, 4, 18, 10, 41), "reference_set_case"),
    ("N09", datetime(1995, 5, 15, 14, 20), "reference_set_case"),
    ("N10", datetime(1974, 11, 7, 21, 14), "reference_set_case"),
    ("E01", datetime(2021, 1, 1, 0, 1), "midnight_plus_1min"),
    ("E02", datetime(2019, 8, 7, 23, 58), "near_liqiu_edge"),
    ("E03", datetime(2016, 2, 29, 0, 37), "leap_day_midnight_block"),
    ("E04", datetime(2024, 11, 7, 6, 5), "lidong_day_morning"),
    ("E05", datetime(2023, 8, 7, 0, 0), "liqiu_exact_midnight"),
    ("E06", datetime(2022, 6, 21, 12, 0), "xiazhi_noon"),
    ("E07", datetime(2020, 2, 4, 0, 1), "lichun_after_1min"),
    ("E08", datetime(2020, 2, 3, 23, 59), "lichun_before_1min"),
    ("H01", datetime(1987, 5, 10, 2, 30), "DST_start_gap_1987"),
    ("H02", datetime(1988, 5, 8, 2, 30), "DST_start_gap_1988"),
    ("H03", datetime(1987, 10, 11, 2, 30), "DST_end_overlap_1987"),
    ("H04", datetime(1988, 10, 9, 2, 30), "DST_end_overlap_1988"),
    ("H05", datetime(1961, 8, 10, 0, 10), "KR_offset_change_1961"),
    ("P04", datetime(1908, 1, 1, 0, 10), "historic_LMT_edge"),
    ("P05", datetime(1990, 5, 20, 3, 15), "coords_instead_of_city"),
    ("P06", datetime(2015, 8, 15, 0, 10), "py_time_shift_2015"),
    ("P07", datetime(2018, 5, 5, 0, 10), "py_time_revert_2018"),
]

print("=" * 140)
print("DETAILED ANALYSIS: Which 30-case results were affected by the zi hour fix?")
print("=" * 140)
print()

changed_cases = []
same_cases = []

for test_id, dt, desc in cases:
    result = analyze_case(test_id, dt, desc)

    if result is None:
        print(f"⚠️  SKIP {test_id:5} | Error in calculation")
        continue

    if result["changed"]:
        changed_cases.append(result)
    else:
        same_cases.append(result)

# Show changed cases
if changed_cases:
    print("🔄 CASES WHERE ZI LOGIC DIFFERS (Clock hour vs LMT hour):")
    print("=" * 140)
    print(
        f"{'ID':<7} {'Date':<20} {'Clock':<8} {'LMT':<8} {'Old Zi':<8} {'New Zi':<8} {'Result':<30}"
    )
    print("-" * 140)

    for case in changed_cases:
        print(
            f"{case['id']:<7} {str(case['dt']):<20} "
            f"h={case['clock_hour']:<6} h={case['lmt_hour']:<6} "
            f"{'YES' if case['clock_zi'] else 'NO':<8} "
            f"{'YES' if case['lmt_zi'] else 'NO':<8} "
            f"{case['result']:<30}"
        )

    print()

# Show cases that stayed the same
print()
print(f"✅ CASES THAT STAYED THE SAME ({len(same_cases)} cases):")
print("=" * 140)
print("These cases have identical zi logic whether checked on clock or LMT hour.")
print()

# Summary
print()
print("=" * 140)
print("SUMMARY")
print("=" * 140)
print(f"Total cases analyzed:     {len(cases)}")
print(f"Cases that CHANGED:       {len(changed_cases)} (zi logic differs)")
print(f"Cases that STAYED SAME:   {len(same_cases)} (zi logic identical)")
print()

if changed_cases:
    print("KEY INSIGHT:")
    print("-" * 140)
    print("Cases CHANGED are in the 32-minute window where:")
    print("  • Clock 23:00-23:31 → LMT 22:28-22:59 (hour 22, LOSES zi status)")
    print("  • Clock 00:00-00:31 → LMT prev day 23:28-23:59 (hour 23, GAINS zi status)")
    print()
    print("These changes are CORRECTIONS - the new results use astronomical time consistently.")
    print("=" * 140)
