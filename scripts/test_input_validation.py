#!/usr/bin/env python3
"""
Test suite for input validation.

Tests all the edge cases mentioned:
- Invalid times (24:00, 12:60)
- Invalid dates (Feb 30, 2023-02-29)
- Out of range values
- Type errors
"""

from scripts._script_loader import get_pillars_module

validate_birth_input = get_pillars_module("input_validator", "validate_birth_input")


def test_input_validation():
    """Run all input validation tests."""

    print("=" * 120)
    print("INPUT VALIDATION TEST SUITE")
    print("=" * 120)
    print()

    test_cases = [
        # Valid cases
        {
            "id": "VALID-01",
            "input": (2000, 9, 14, 10, 30),
            "description": "Normal valid datetime",
            "expect_valid": True,
        },
        {
            "id": "VALID-02",
            "input": (2020, 2, 29, 12, 0),
            "description": "Leap year Feb 29",
            "expect_valid": True,
        },
        {
            "id": "VALID-03",
            "input": (1900, 1, 1, 0, 0),
            "description": "Min year boundary",
            "expect_valid": True,
        },
        {
            "id": "VALID-04",
            "input": (2050, 12, 31, 23, 59),
            "description": "Max year boundary",
            "expect_valid": True,
        },
        # Invalid hour cases
        {
            "id": "INVALID-HOUR-01",
            "input": (2020, 10, 10, 24, 0),
            "description": "Hour 24:00 (strict mode)",
            "expect_valid": False,
            "expect_error": "Hour must be 0-23",
        },
        {
            "id": "INVALID-HOUR-02",
            "input": (2020, 10, 10, 25, 0),
            "description": "Hour 25 (impossible)",
            "expect_valid": False,
            "expect_error": "Hour must be 0-23",
        },
        {
            "id": "INVALID-HOUR-03",
            "input": (2020, 10, 10, -1, 0),
            "description": "Negative hour",
            "expect_valid": False,
            "expect_error": "Hour must be 0-23",
        },
        # Invalid minute cases
        {
            "id": "INVALID-MIN-01",
            "input": (2020, 10, 10, 12, 60),
            "description": "Minute 60 (impossible)",
            "expect_valid": False,
            "expect_error": "Minute must be 0-59",
        },
        {
            "id": "INVALID-MIN-02",
            "input": (2020, 10, 10, 12, 75),
            "description": "Minute 75 (impossible)",
            "expect_valid": False,
            "expect_error": "Minute must be 0-59",
        },
        {
            "id": "INVALID-MIN-03",
            "input": (2020, 10, 10, 12, -5),
            "description": "Negative minute",
            "expect_valid": False,
            "expect_error": "Minute must be 0-59",
        },
        # Invalid day cases
        {
            "id": "INVALID-DAY-01",
            "input": (2023, 2, 29, 12, 0),
            "description": "Feb 29 in non-leap year",
            "expect_valid": False,
            "expect_error": "not a leap year",
        },
        {
            "id": "INVALID-DAY-02",
            "input": (2020, 2, 30, 12, 0),
            "description": "Feb 30 (impossible)",
            "expect_valid": False,
            "expect_error": "February",
        },
        {
            "id": "INVALID-DAY-03",
            "input": (2020, 4, 31, 12, 0),
            "description": "April 31 (only has 30 days)",
            "expect_valid": False,
            "expect_error": "April",
        },
        {
            "id": "INVALID-DAY-04",
            "input": (2020, 11, 31, 12, 0),
            "description": "November 31 (only has 30 days)",
            "expect_valid": False,
            "expect_error": "November",
        },
        {
            "id": "INVALID-DAY-05",
            "input": (2020, 1, 0, 12, 0),
            "description": "Day 0 (impossible)",
            "expect_valid": False,
            "expect_error": "Day must be >= 1",
        },
        {
            "id": "INVALID-DAY-06",
            "input": (2020, 1, 32, 12, 0),
            "description": "January 32 (only has 31 days)",
            "expect_valid": False,
            "expect_error": "January",
        },
        # Invalid month cases
        {
            "id": "INVALID-MONTH-01",
            "input": (2020, 0, 15, 12, 0),
            "description": "Month 0 (impossible)",
            "expect_valid": False,
            "expect_error": "Month must be 1-12",
        },
        {
            "id": "INVALID-MONTH-02",
            "input": (2020, 13, 15, 12, 0),
            "description": "Month 13 (impossible)",
            "expect_valid": False,
            "expect_error": "Month must be 1-12",
        },
        # Invalid year cases
        {
            "id": "INVALID-YEAR-01",
            "input": (1899, 12, 31, 12, 0),
            "description": "Year 1899 (before data coverage)",
            "expect_valid": False,
            "expect_error": "before data coverage",
        },
        {
            "id": "INVALID-YEAR-02",
            "input": (2051, 1, 1, 12, 0),
            "description": "Year 2051 (beyond data coverage)",
            "expect_valid": False,
            "expect_error": "beyond data coverage",
        },
        # Edge cases
        {
            "id": "EDGE-01",
            "input": (2020, 12, 31, 23, 59, 59),
            "description": "Last second of year",
            "expect_valid": True,
        },
        {
            "id": "EDGE-02",
            "input": (2000, 1, 1, 0, 0, 0),
            "description": "Y2K midnight",
            "expect_valid": True,
        },
    ]

    passed = 0
    failed = 0

    for case in test_cases:
        test_id = case["id"]
        year, month, day, hour, minute = case["input"][:5]
        second = case["input"][5] if len(case["input"]) > 5 else 0
        description = case["description"]
        expect_valid = case["expect_valid"]

        # Run validation
        result = validate_birth_input(year, month, day, hour, minute, second, strict=True)

        # Check result
        if result["valid"] == expect_valid:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        # Format details
        details = []
        if result["valid"]:
            details.append(f"Valid: {result['datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
            if result["corrected"]:
                details.append(f"(corrected: {result['correction_note']})")
        else:
            details.append(f"Error: {result['error']}")
            # Check if error matches expected
            if "expect_error" in case:
                if case["expect_error"].lower() in result["error"].lower():
                    details.append("(expected error ✅)")
                else:
                    status = "⚠️  WARN"
                    details.append(f"(expected '{case['expect_error']}' ⚠️)")

        print(f"{status:11} | {test_id:20} | {description:40} | {' '.join(details)}")

    # Test non-strict mode (24:00 conversion)
    print()
    print("=" * 120)
    print("NON-STRICT MODE TESTS (24:00 auto-correction)")
    print("=" * 120)

    result = validate_birth_input(2020, 10, 10, 24, 0, 0, strict=False)
    if result["valid"] and result["corrected"]:
        print(
            f"✅ PASS      | 24:00 auto-convert    | Converted to {result['datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"             |                       | Note: {result['correction_note']}")
        passed += 1
    else:
        print(f"❌ FAIL      | 24:00 auto-convert    | Should auto-correct but didn't")
        failed += 1

    # Summary
    print()
    print("=" * 120)
    print("TEST SUMMARY")
    print("=" * 120)
    print(f"Total tests:  {passed + failed}")
    print(f"Passed:       {passed}/{passed + failed} ({100*passed/(passed+failed):.1f}%)")
    print(f"Failed:       {failed}")
    print("=" * 120)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_input_validation()

    if failed == 0:
        print("\n🎉 ALL INPUT VALIDATION TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review implementation.")
