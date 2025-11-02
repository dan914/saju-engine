#!/usr/bin/env python3
"""
Test suite for DST and timezone edge cases.

Based on ChatGPT deep research report on Korean timezone history.
Tests 20+ edge cases including:
- DST periods (1948-1960, 1987-1988)
- DST gaps (non-existent times)
- DST overlaps (ambiguous times)
- Historical timezone changes
- North Korean timezone changes
"""

import sys
from datetime import datetime
from pathlib import Path

# Add timezone handler path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "services" / "pillars-service" / "app" / "core")
)

# Direct import without package
import timezone_handler

KoreanTimezoneHandler = timezone_handler.KoreanTimezoneHandler
TimezoneWarning = timezone_handler.TimezoneWarning


def test_edge_cases():
    """Run all edge case tests."""
    handler = KoreanTimezoneHandler()

    print("=" * 130)
    print("DST AND TIMEZONE EDGE CASE TEST SUITE")
    print("=" * 130)
    print()

    # Test cases from research report
    test_cases = [
        # 1. Pre-1908 LMT differences
        {
            "id": "LMT-01",
            "dt": datetime(1907, 7, 15, 12, 0),
            "location": "Pyongyang",
            "description": "Pre-1908 Pyongyang LMT",
            "expected_warnings": [TimezoneWarning.HISTORICAL_LMT],
        },
        # 2. 1911-1912 timezone boundary
        {
            "id": "TZ-1911",
            "dt": datetime(1911, 12, 31, 23, 50),
            "location": "Seoul",
            "description": "1911 end, before UTC+9 change",
            "expected_warnings": [],
        },
        # 3. 1948 First DST start
        {
            "id": "DST-1948-START",
            "dt": datetime(1948, 6, 1, 0, 1),
            "location": "Seoul",
            "description": "1948 first DST implementation",
            "expected_dst": True,
        },
        # 4. 1948 DST end
        {
            "id": "DST-1948-END",
            "dt": datetime(1948, 9, 12, 23, 30),
            "location": "Seoul",
            "description": "1948 DST end approaching",
            "expected_dst": True,
        },
        # 5. 1954 timezone change (UTC+9 → UTC+8:30)
        {
            "id": "TZ-1954",
            "dt": datetime(1954, 3, 21, 0, 5),
            "location": "Busan",
            "description": "1954 South Korea timezone change to UTC+8:30",
            "expected_offset": 8.5,
        },
        # 6. 1954-1961 North-South time difference
        {
            "id": "TZ-1960-SPLIT",
            "dt": datetime(1960, 5, 1, 12, 0),
            "location": "Seoul",
            "description": "1960 during North-South timezone split",
            "expected_offset": 8.5,  # South was UTC+8:30
        },
        # 7. 1961 timezone restoration (UTC+8:30 → UTC+9)
        {
            "id": "TZ-1961",
            "dt": datetime(1961, 8, 10, 0, 5),
            "location": "Seoul",
            "description": "1961 South Korea timezone restore to UTC+9",
            "expected_offset": 9.0,
        },
        # 8. 1987 DST gap (non-existent time)
        {
            "id": "DST-1987-GAP",
            "dt": datetime(1987, 5, 10, 2, 10),
            "location": "Seoul",
            "description": "1987 DST gap - time doesn't exist",
            "expected_warnings": [TimezoneWarning.DST_GAP],
        },
        # 9. 1987 DST overlap (ambiguous time)
        {
            "id": "DST-1987-OVERLAP",
            "dt": datetime(1987, 10, 11, 2, 30),
            "location": "Seoul",
            "description": "1987 DST overlap - time occurs twice",
            "expected_warnings": [TimezoneWarning.DST_OVERLAP],
        },
        # 10. 1988 DST gap
        {
            "id": "DST-1988-GAP",
            "dt": datetime(1988, 5, 8, 2, 30),
            "location": "Seoul",
            "description": "1988 DST gap - time doesn't exist",
            "expected_warnings": [TimezoneWarning.DST_GAP],
        },
        # 11. 1988 DST overlap
        {
            "id": "DST-1988-OVERLAP",
            "dt": datetime(1988, 10, 9, 2, 15),
            "location": "Seoul",
            "description": "1988 DST overlap - time occurs twice",
            "expected_warnings": [TimezoneWarning.DST_OVERLAP],
        },
        # 12. 2015 North Korea Pyongyang Time (UTC+8:30)
        {
            "id": "NK-2015",
            "dt": datetime(2015, 8, 15, 0, 5),
            "location": "Pyongyang",
            "description": "2015 North Korea Pyongyang Time introduction",
            "expected_offset": 8.5,
        },
        # 13. 2018 North Korea timezone restore (UTC+8:30 → UTC+9)
        {
            "id": "NK-2018",
            "dt": datetime(2018, 5, 5, 0, 5),
            "location": "Pyongyang",
            "description": "2018 North Korea timezone restore to UTC+9",
            "expected_offset": 9.0,
        },
        # 14-20: Additional validation cases
        {
            "id": "NORMAL-2023",
            "dt": datetime(2023, 6, 15, 14, 30),
            "location": "Seoul",
            "description": "Normal modern time (no DST)",
            "expected_dst": False,
        },
        {
            "id": "CITY-BUSAN",
            "dt": datetime(2023, 3, 15, 10, 0),
            "location": "Busan",
            "description": "Busan city-specific LMT",
            "expected_lmt": -24,
        },
        {
            "id": "CITY-DAEGU",
            "dt": datetime(2023, 3, 15, 10, 0),
            "location": "Daegu",
            "description": "Daegu city-specific LMT",
            "expected_lmt": -27,
        },
    ]

    passed = 0
    failed = 0
    warnings_found = []

    for case in test_cases:
        test_id = case["id"]
        dt = case["dt"]
        location = case["location"]
        description = case["description"]

        try:
            # Run conversion
            result = handler.convert_to_saju_time(
                dt, location=location, apply_dst=True, apply_lmt=True
            )

            # Check expectations
            status = "✅ PASS"
            details = []

            # Check DST
            if "expected_dst" in case:
                if result["dst_applied"] == case["expected_dst"]:
                    details.append(f"DST:✅")
                else:
                    status = "❌ FAIL"
                    details.append(
                        f"DST:❌ expected {case['expected_dst']}, got {result['dst_applied']}"
                    )

            # Check warnings
            if "expected_warnings" in case:
                warning_types = [w["type"] for w in result["warnings"]]
                for expected_warning in case["expected_warnings"]:
                    if expected_warning in warning_types:
                        details.append(f"Warning:✅ {expected_warning}")
                        warnings_found.append(test_id)
                    else:
                        status = "❌ FAIL"
                        details.append(f"Warning:❌ missing {expected_warning}")

            # Check timezone offset
            if "expected_offset" in case:
                actual_offset = handler.get_standard_time_offset(dt, location)
                if abs(actual_offset - case["expected_offset"]) < 0.1:
                    details.append(f"Offset:✅ {actual_offset}")
                else:
                    status = "❌ FAIL"
                    details.append(
                        f"Offset:❌ expected {case['expected_offset']}, got {actual_offset}"
                    )

            # Check LMT
            if "expected_lmt" in case:
                if result["lmt_offset"] == case["expected_lmt"]:
                    details.append(f"LMT:✅ {result['lmt_offset']}min")
                else:
                    status = "❌ FAIL"
                    details.append(
                        f"LMT:❌ expected {case['expected_lmt']}, got {result['lmt_offset']}"
                    )

            print(f"{status:11} | {test_id:20} | {description:50} | {' '.join(details)}")

            if status == "✅ PASS":
                passed += 1
            else:
                failed += 1

            # Show warnings if any
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"{'':11} | {'':20} | ⚠️  {warning['message']}")

        except Exception as e:
            print(f"❌ ERROR   | {test_id:20} | {description:50} | Exception: {e}")
            failed += 1

        print()

    # Summary
    print("=" * 130)
    print("TEST SUMMARY")
    print("=" * 130)
    print(f"Total tests:        {passed + failed}")
    print(
        f"Passed:             {passed}/{passed + failed} ({100*passed/(passed+failed) if passed+failed > 0 else 0:.1f}%)"
    )
    print(f"Failed:             {failed}")
    print(f"Warnings detected:  {len(warnings_found)}")
    print("=" * 130)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_edge_cases()

    if failed == 0:
        print("\n🎉 ALL EDGE CASE TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review implementation.")
