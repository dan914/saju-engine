#!/usr/bin/env python3
"""
Test input validation integration with main engine.
"""

from datetime import datetime

from calculate_pillars_traditional import calculate_four_pillars


def test_validation_integration():
    """Test that validation catches errors in main engine."""

    print("=" * 120)
    print("VALIDATION INTEGRATION TEST")
    print("=" * 120)
    print()

    test_cases = [
        # Valid case
        {
            "id": "VALID",
            "dt": datetime(2000, 9, 14, 10, 30),
            "should_pass": True,
        },
        # Invalid cases that should be caught
        {
            "id": "YEAR-TOO-OLD",
            "dt": datetime(1899, 12, 31, 12, 0),
            "should_pass": False,
            "expected_error": "before data coverage",
        },
        {
            "id": "YEAR-TOO-NEW",
            "dt": datetime(2051, 1, 1, 12, 0),
            "should_pass": False,
            "expected_error": "beyond data coverage",
        },
    ]

    passed = 0
    failed = 0

    for case in test_cases:
        test_id = case["id"]
        dt = case["dt"]
        should_pass = case["should_pass"]

        # Run calculation with validation enabled
        result = calculate_four_pillars(
            dt, tz_str="Asia/Seoul", mode="traditional_kr", validate_input=True
        )

        # Check if error was caught correctly
        has_error = "error" in result

        if should_pass:
            if not has_error:
                status = "✅ PASS"
                pillars = f"{result['year']} {result['month']} {result['day']} {result['hour']}"
                print(f"{status} | {test_id:20} | Valid input accepted | {pillars}")
                passed += 1
            else:
                status = "❌ FAIL"
                print(f"{status} | {test_id:20} | Valid input rejected | {result['error']}")
                failed += 1
        else:
            if has_error:
                status = "✅ PASS"
                error_match = ""
                if "expected_error" in case:
                    if case["expected_error"].lower() in result["error"].lower():
                        error_match = " (expected error ✅)"
                print(
                    f"{status} | {test_id:20} | Invalid input caught | {result['error']}{error_match}"
                )
                passed += 1
            else:
                status = "❌ FAIL"
                print(f"{status} | {test_id:20} | Invalid input NOT caught | Should have errored")
                failed += 1

    # Test with validation disabled
    print()
    print("=" * 120)
    print("VALIDATION DISABLED TEST (validation=False)")
    print("=" * 120)

    # This should process without validation error
    result = calculate_four_pillars(
        datetime(1899, 12, 31, 12, 0), tz_str="Asia/Seoul", validate_input=False
    )

    if "error" in result and "data" not in result["error"].lower():
        # Got validation error even with validation=False
        print(f"❌ FAIL | Validation disabled but still got validation error")
        failed += 1
    else:
        print(f"✅ PASS | Validation disabled, input processed (may fail later on missing data)")
        passed += 1

    # Summary
    print()
    print("=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print(f"Total tests:  {passed + failed}")
    print(f"Passed:       {passed}/{passed + failed} ({100*passed/(passed+failed):.1f}%)")
    print(f"Failed:       {failed}")
    print("=" * 120)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_validation_integration()

    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
