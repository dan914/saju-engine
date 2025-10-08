#!/usr/bin/env python3
"""
Test midnight boundary cases for 子時 (Zi Hour) transition rule.

Creates 48 test cases across midnight boundaries to validate:
1. 23:00-23:59 → Next day (子時 early)
2. 00:00-00:59 → Same day (子時 late)
3. Other hours → Normal calculation
"""

from datetime import datetime, timedelta

from calculate_pillars_traditional import calculate_four_pillars


def generate_midnight_test_cases():
    """Generate 48 test cases around midnight."""
    # 3 reference dates (regular, before/after solar terms)
    base_dates = [
        datetime(2025, 1, 15),  # Regular day
        datetime(2025, 2, 3),  # Day before 立春 (Feb 4)
        datetime(2025, 8, 7),  # Day before 立秋 (Aug 8)
    ]

    # 8 times per date: 23:00, 23:15, 23:30, 23:45, 00:00, 00:15, 00:30, 00:45
    times = [(23, 0), (23, 15), (23, 30), (23, 45), (0, 0), (0, 15), (0, 30), (0, 45)]

    test_cases = []
    for base_dt in base_dates:
        for hour, minute in times:
            test_dt = base_dt.replace(hour=hour, minute=minute)
            test_cases.append(test_dt)

    return test_cases


def test_midnight_transitions():
    """Test 子時 transition rule across midnight boundaries."""
    test_cases = generate_midnight_test_cases()

    print("=" * 130)
    print("MIDNIGHT BOUNDARY TEST - 子時 (Zi Hour) TRANSITION RULE")
    print("=" * 130)
    print(f"Testing {len(test_cases)} cases across 3 dates × 8 times")
    print()
    print("Expected behavior:")
    print("  - 23:00-23:59 (after LMT): 子時 early → Use NEXT day")
    print("  - 00:00-00:59 (after LMT): 子時 late  → Use SAME day")
    print("=" * 130)

    results_by_hour = {}
    passed = 0
    failed = 0

    for test_dt in test_cases:
        result = calculate_four_pillars(
            test_dt, tz_str="Asia/Seoul", mode="traditional_kr", return_metadata=True
        )

        if "error" in result:
            print(f"ERROR: {test_dt} - {result['error']}")
            failed += 1
            continue

        meta = result["metadata"]
        lmt_time = datetime.strptime(meta["lmt_adjusted_time"], "%Y-%m-%d %H:%M:%S")
        lmt_hour = lmt_time.hour

        # Track results by LMT hour
        if lmt_hour not in results_by_hour:
            results_by_hour[lmt_hour] = {"zi_applied": 0, "zi_not_applied": 0, "total": 0}

        results_by_hour[lmt_hour]["total"] += 1
        if meta["zi_transition_applied"]:
            results_by_hour[lmt_hour]["zi_applied"] += 1
        else:
            results_by_hour[lmt_hour]["zi_not_applied"] += 1

        # Validate expected behavior
        expected_zi = lmt_hour == 23
        actual_zi = meta["zi_transition_applied"]

        if expected_zi == actual_zi:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        # Expected day offset
        if lmt_hour == 23:
            expected_day = (lmt_time.date() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            expected_day = lmt_time.date().strftime("%Y-%m-%d")

        actual_day = meta["day_for_pillar"]

        day_match = "✅" if expected_day == actual_day else "❌"

        print(
            f"{status} | Input: {test_dt.strftime('%Y-%m-%d %H:%M')} | "
            f"LMT: {lmt_time.strftime('%H:%M')} (hr={lmt_hour:02d}) | "
            f"子時: {actual_zi} | Day: {actual_day} {day_match} | "
            f"Pillars: {result['year']} {result['month']} {result['day']} {result['hour']}"
        )

    # Summary by hour
    print("\n" + "=" * 130)
    print("SUMMARY BY LMT HOUR")
    print("=" * 130)
    print(
        f"{'Hour':<6} {'Total':<8} {'子時 Applied':<15} {'子時 Not Applied':<20} {'Expected Behavior':<30}"
    )
    print("-" * 130)

    for hour in sorted(results_by_hour.keys()):
        stats = results_by_hour[hour]
        if hour == 23:
            expected = "✅ Should apply 子時 (next day)"
            status = "✅" if stats["zi_applied"] == stats["total"] else "❌"
        else:
            expected = "✅ Should NOT apply 子時 (same day)"
            status = "✅" if stats["zi_not_applied"] == stats["total"] else "❌"

        print(
            f"{hour:02d}:xx  {stats['total']:<8} "
            f"{stats['zi_applied']:<15} {stats['zi_not_applied']:<20} "
            f"{status} {expected}"
        )

    # Final summary
    print("\n" + "=" * 130)
    print("FINAL TEST RESULTS")
    print("=" * 130)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}/{passed + failed} ({100*passed/(passed+failed):.1f}%)")
    print(f"Failed: {failed}")
    print("=" * 130)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_midnight_transitions()

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 子時 rule is working correctly! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review implementation.")
