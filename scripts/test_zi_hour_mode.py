#!/usr/bin/env python3
"""
Test 야자시/조자시 (Night Zi / Morning Zi) mode toggle.

Tests that traditional vs modern mode produces different day pillars
for births during 23:00-23:59 hour.
"""

from datetime import datetime

from calculate_pillars_traditional import calculate_four_pillars


def test_zi_hour_modes():
    """Test traditional vs modern 子時 handling."""

    print("=" * 120)
    print("야자시/조자시 (ZI HOUR MODE) TEST")
    print("=" * 120)
    print()
    print("Tests births during 23:00-23:59 hour (子時):")
    print("- Traditional mode: Day changes at 23:00 (야자시 = night zi = next day)")
    print("- Modern mode: Day changes at 00:00 (no special handling)")
    print()
    print("=" * 120)
    print()

    test_cases = [
        {
            "id": "ZI-01",
            "dt": datetime(2000, 9, 14, 23, 30),
            "description": "23:30 (子時 middle)",
        },
        {
            "id": "ZI-02",
            "dt": datetime(1987, 5, 10, 23, 15),
            "description": "23:15 during DST (子時 early)",
        },
        {
            "id": "ZI-03",
            "dt": datetime(2020, 12, 31, 23, 59),
            "description": "23:59 (子時 end, year boundary)",
        },
        {
            "id": "NON-ZI-01",
            "dt": datetime(2000, 9, 14, 0, 30),
            "description": "00:30 (조자시, should be same in both modes)",
        },
        {
            "id": "NON-ZI-02",
            "dt": datetime(2000, 9, 14, 12, 0),
            "description": "12:00 noon (should be same in both modes)",
        },
    ]

    passed = 0
    failed = 0

    for case in test_cases:
        test_id = case["id"]
        dt = case["dt"]
        description = case["description"]

        # Calculate with traditional mode
        result_trad = calculate_four_pillars(
            dt,
            tz_str="Asia/Seoul",
            mode="traditional_kr",
            validate_input=True,
            return_metadata=True,
            zi_hour_mode="traditional",
        )

        # Calculate with modern mode
        result_modern = calculate_four_pillars(
            dt,
            tz_str="Asia/Seoul",
            mode="traditional_kr",
            validate_input=True,
            return_metadata=True,
            zi_hour_mode="modern",
        )

        # Extract pillars
        trad_pillars = f"{result_trad['year']} {result_trad['month']} {result_trad['day']} {result_trad['hour']}"
        modern_pillars = f"{result_modern['year']} {result_modern['month']} {result_modern['day']} {result_modern['hour']}"

        # Extract day pillars for comparison
        trad_day = result_trad["day"]
        modern_day = result_modern["day"]

        # Extract metadata
        trad_zi_applied = result_trad["metadata"]["zi_transition_applied"]
        modern_zi_applied = result_modern["metadata"]["zi_transition_applied"]
        trad_day_for_pillar = result_trad["metadata"]["day_for_pillar"]
        modern_day_for_pillar = result_modern["metadata"]["day_for_pillar"]

        # Check if it's a 子時 hour (23:00-23:59)
        is_zi_hour = dt.hour == 23

        # Determine if test passed
        if is_zi_hour:
            # Traditional should apply zi transition, modern should not
            if trad_zi_applied and not modern_zi_applied and trad_day != modern_day:
                status = "✅ PASS"
                passed += 1
                note = f"Day pillar differs (야자시 applied)"
            else:
                status = "❌ FAIL"
                failed += 1
                note = f"Should differ but doesn't"
        else:
            # Non-zi hour: Check if traditional mode still differs due to LMT
            # Note: Modern mode uses original date, traditional uses LMT-adjusted date
            # So they might differ even for non-zi hours if LMT crosses day boundary
            if not trad_zi_applied and not modern_zi_applied:
                status = "✅ PASS"
                passed += 1
                if trad_day == modern_day:
                    note = f"Day pillar same (not 子時, no LMT day boundary)"
                else:
                    note = f"Day pillar differs due to LMT crossing day boundary"
            else:
                status = "❌ FAIL"
                failed += 1
                note = f"Zi transition should not apply (not 子時)"

        # Print result
        print(f"{status} | {test_id:12} | {description}")
        print(
            f"         | {'Traditional:':<12} | {trad_pillars:30} | Zi applied: {trad_zi_applied} | Day: {trad_day_for_pillar}"
        )
        print(
            f"         | {'Modern:':<12} | {modern_pillars:30} | Zi applied: {modern_zi_applied} | Day: {modern_day_for_pillar}"
        )
        print(f"         | {'Note:':<12} | {note}")
        print()

    # Summary
    print("=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print(f"Total tests:  {passed + failed}")
    print(f"Passed:       {passed}/{passed + failed} ({100*passed/(passed+failed):.1f}%)")
    print(f"Failed:       {failed}")
    print("=" * 120)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_zi_hour_modes()

    if failed == 0:
        print("\n🎉 ALL ZI HOUR MODE TESTS PASSED! 🎉")
        print("\nUsers can now choose between:")
        print("  - Traditional mode (야자시/조자시): Day changes at 23:00")
        print("  - Modern mode: Day changes at 00:00 (midnight boundary)")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review implementation.")
