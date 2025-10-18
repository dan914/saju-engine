#!/usr/bin/env python3
"""
Analyze impact of fix: Check zi hour AFTER LMT instead of BEFORE.

Shows which test cases will have different results.
"""

from datetime import datetime, timedelta

from calculate_pillars_traditional import calculate_four_pillars


def analyze_case(dt, label):
    """Analyze a single case under both old and new logic."""

    # Current (old) logic: Check zi using original hour
    result_current = calculate_four_pillars(
        dt,
        tz_str="Asia/Seoul",
        mode="traditional_kr",
        validate_input=True,
        return_metadata=True,
        zi_hour_mode="traditional",
    )

    # Simulate new logic manually
    # Step 1: Apply LMT
    lmt_adjusted = dt - timedelta(minutes=32)
    lmt_hour = lmt_adjusted.hour

    # Step 2: Check zi using LMT hour (new logic)
    if lmt_hour == 23:
        # 야자시: Use next day from LMT
        new_day_for_pillar = lmt_adjusted.date() + timedelta(days=1)
        new_zi_applied = True
    else:
        # Not 야자시
        new_day_for_pillar = lmt_adjusted.date()
        new_zi_applied = False

    # Calculate what new result would be
    result_new = calculate_four_pillars(
        dt,
        tz_str="Asia/Seoul",
        mode="traditional_kr",
        validate_input=True,
        return_metadata=True,
        zi_hour_mode="modern",  # Use modern to get LMT date without zi rule
    )

    # Then manually check if new zi rule would apply
    if lmt_hour == 23:
        # Need to recalculate with next day
        # This is complex, so we'll just note it changes
        will_change = True
    else:
        will_change = False

    # Compare
    current_day = result_current["metadata"]["day_for_pillar"]
    current_zi = result_current["metadata"]["zi_transition_applied"]
    current_pillars = f"{result_current['year']} {result_current['month']} {result_current['day']} {result_current['hour']}"

    original_hour = dt.hour

    print(f"\n{'='*100}")
    print(f"{label}")
    print(f"{'='*100}")
    print(f"Input:          {dt}")
    print(f"Original hour:  {original_hour}")
    print(f"LMT adjusted:   {lmt_adjusted}")
    print(f"LMT hour:       {lmt_hour}")
    print()
    print(f"CURRENT LOGIC (check original hour {original_hour}):")
    print(f"  Zi applied:   {current_zi}")
    print(f"  Day for pillar: {current_day}")
    print(f"  Pillars:      {current_pillars}")
    print()
    print(f"NEW LOGIC (check LMT hour {lmt_hour}):")
    print(f"  Zi applied:   {new_zi_applied}")
    print(f"  Day for pillar: {new_day_for_pillar}")

    # Determine if it changes
    if (original_hour == 23 and lmt_hour != 23) or (original_hour != 23 and lmt_hour == 23):
        print(f"  RESULT:       ⚠️  WILL CHANGE (zi logic differs)")
        return True
    else:
        print(f"  RESULT:       ✅ STAYS SAME (zi logic identical)")
        return False


def main():
    print("=" * 100)
    print("IMPACT ANALYSIS: Old Logic (check original hour) vs New Logic (check LMT hour)")
    print("=" * 100)

    # Test cases from our suites
    test_cases = [
        # Original 10 reference cases
        (datetime(1974, 11, 7, 21, 14), "REF-01: 1974-11-07 21:14"),
        (datetime(1988, 3, 26, 5, 22), "REF-02: 1988-03-26 05:22"),
        (datetime(1995, 5, 15, 14, 20), "REF-03: 1995-05-15 14:20"),
        (datetime(2001, 9, 3, 3, 7), "REF-04: 2001-09-03 03:07"),
        (datetime(2007, 12, 29, 17, 53), "REF-05: 2007-12-29 17:53"),
        (datetime(2013, 4, 18, 10, 41), "REF-06: 2013-04-18 10:41"),
        (datetime(2016, 2, 29, 0, 37), "REF-07: 2016-02-29 00:37"),
        (datetime(2019, 8, 7, 23, 58), "REF-08: 2019-08-07 23:58"),
        (datetime(2021, 1, 1, 0, 1), "REF-09: 2021-01-01 00:01 ← THE FAILING CASE"),
        (datetime(2024, 11, 7, 6, 5), "REF-10: 2024-11-07 06:05"),
        # 30-case edge cases
        (datetime(2000, 9, 14, 10, 0), "N01: 2000-09-14 10:00"),
        (datetime(1999, 12, 31, 23, 30), "N06: 1999-12-31 23:30 (NYE)"),
        (datetime(2020, 2, 3, 23, 59), "E08: 2020-02-03 23:59 (before lichun)"),
        (datetime(2020, 2, 4, 0, 1), "E07: 2020-02-04 00:01 (after lichun)"),
        # Critical boundary cases
        (datetime(2000, 9, 14, 23, 30), "ZI-01: 23:30 (original zi test)"),
        (datetime(2000, 9, 14, 0, 30), "ZI-MORNING: 00:30 (조자시)"),
        # Edge cases around LMT boundary
        (datetime(2000, 1, 1, 23, 0), "EDGE: 23:00 exact"),
        (datetime(2000, 1, 1, 23, 15), "EDGE: 23:15 (→ LMT 22:43)"),
        (datetime(2000, 1, 1, 23, 32), "EDGE: 23:32 (→ LMT 23:00)"),
        (datetime(2000, 1, 1, 23, 59), "EDGE: 23:59 (→ LMT 23:27)"),
        (datetime(2000, 1, 1, 0, 0), "EDGE: 00:00 (→ LMT prev 23:28)"),
        (datetime(2000, 1, 1, 0, 32), "EDGE: 00:32 (→ LMT 00:00)"),
        (datetime(2000, 1, 1, 0, 59), "EDGE: 00:59 (→ LMT 00:27)"),
    ]

    changes = []
    no_changes = []

    for dt, label in test_cases:
        will_change = analyze_case(dt, label)
        if will_change:
            changes.append(label)
        else:
            no_changes.append(label)

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"\nTotal cases analyzed: {len(test_cases)}")
    print(f"Will CHANGE: {len(changes)}")
    print(f"Stay SAME:   {len(no_changes)}")

    if changes:
        print(f"\n⚠️  Cases that will CHANGE:")
        for case in changes:
            print(f"    - {case}")

    if no_changes:
        print(f"\n✅ Cases that stay SAME:")
        for case in no_changes:
            print(f"    - {case}")

    print("\n" + "=" * 100)
    print("KEY INSIGHT")
    print("=" * 100)
    print(
        """
Cases that CHANGE are those where:
  - Original hour is 23 BUT LMT hour is NOT 23
    (e.g., 23:15 → LMT 22:43, loses zi status)
  - Original hour is NOT 23 BUT LMT hour IS 23
    (e.g., 00:01 → LMT 23:29, gains zi status)

This happens in a ~32-minute window around midnight:
  - Input 23:00-23:31 → LMT 22:28-22:59 (loses zi)
  - Input 00:00-00:27 → LMT prev day 23:28-23:59 (gains zi)
    """
    )


if __name__ == "__main__":
    main()
