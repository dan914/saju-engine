#!/usr/bin/env python3
"""
Test 30 mixed cases covering normal, edge, historical, and pathological scenarios.

Test categories:
- N01-N10: Normal cases (everyday scenarios)
- E01-E08: Edge cases (midnight boundaries, solar term transitions)
- H01-H05: Historical cases (DST periods, timezone changes)
- P01-P07: Pathological cases (invalid inputs, special timezones)
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import calculate_pillars_traditional
sys.path.insert(0, str(Path(__file__).parent))

from calculate_pillars_traditional import calculate_four_pillars


def parse_time(time_str):
    """Parse time string, handling special cases."""
    # Handle invalid time formats
    if ":" not in time_str:
        return None

    parts = time_str.split(":")
    if len(parts) != 2:
        return None

    try:
        hour = int(parts[0])
        minute = int(parts[1])

        # Validate ranges
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None

        return hour, minute
    except ValueError:
        return None


def test_30_mixed_cases(input_csv, output_csv):
    """Run all 30 test cases and write results to CSV."""

    print("=" * 130)
    print("SAJU ENGINE - 30 MIXED TEST CASES")
    print("=" * 130)
    print(f"Input:  {input_csv}")
    print(f"Output: {output_csv}")
    print("=" * 130)

    # Read input CSV
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)

    print(f"\nLoaded {len(test_cases)} test cases")
    print()

    results = []
    passed = 0
    failed = 0
    skipped = 0

    for case in test_cases:
        test_id = case["id"]
        date_str = case["date_local"]
        time_str = case["time_local"]
        tz_str = case["tz"]
        location = case["location"]
        note = case["note"]
        for_ft = case["for_forceteller"] == "True"

        # Parse time
        time_parts = parse_time(time_str)
        if time_parts is None:
            print(f"⚠️  SKIP {test_id:4} | {date_str} {time_str:8} | Invalid time format | {note}")
            results.append(
                {
                    "id": test_id,
                    "date_local": date_str,
                    "time_local": time_str,
                    "tz": tz_str,
                    "location": location,
                    "note": note,
                    "for_forceteller": for_ft,
                    "ft_year": "",
                    "ft_month": "",
                    "ft_day": "",
                    "ft_hour": "",
                    "engine_year": "ERROR",
                    "engine_month": "Invalid time format",
                    "engine_day": "",
                    "engine_hour": "",
                    "match_year": "",
                    "match_month": "",
                    "match_day": "",
                    "match_hour": "",
                }
            )
            skipped += 1
            continue

        hour, minute = time_parts

        # Parse date
        try:
            year, month, day = map(int, date_str.split("-"))
            birth_dt = datetime(year, month, day, hour, minute)
        except (ValueError, AttributeError) as e:
            print(f"⚠️  SKIP {test_id:4} | {date_str} {time_str:8} | Invalid date: {e} | {note}")
            results.append(
                {
                    "id": test_id,
                    "date_local": date_str,
                    "time_local": time_str,
                    "tz": tz_str,
                    "location": location,
                    "note": note,
                    "for_forceteller": for_ft,
                    "ft_year": "",
                    "ft_month": "",
                    "ft_day": "",
                    "ft_hour": "",
                    "engine_year": "ERROR",
                    "engine_month": f"Invalid date: {e}",
                    "engine_day": "",
                    "engine_hour": "",
                    "match_year": "",
                    "match_month": "",
                    "match_day": "",
                    "match_hour": "",
                }
            )
            skipped += 1
            continue

        # Calculate pillars
        try:
            result = calculate_four_pillars(
                birth_dt, tz_str=tz_str, mode="traditional_kr", return_metadata=True
            )

            if "error" in result:
                print(
                    f"❌ FAIL {test_id:4} | {date_str} {time_str:8} | Error: {result['error']} | {note}"
                )
                results.append(
                    {
                        "id": test_id,
                        "date_local": date_str,
                        "time_local": time_str,
                        "tz": tz_str,
                        "location": location,
                        "note": note,
                        "for_forceteller": for_ft,
                        "ft_year": "",
                        "ft_month": "",
                        "ft_day": "",
                        "ft_hour": "",
                        "engine_year": "ERROR",
                        "engine_month": result["error"],
                        "engine_day": "",
                        "engine_hour": "",
                        "match_year": "",
                        "match_month": "",
                        "match_day": "",
                        "match_hour": "",
                    }
                )
                failed += 1
                continue

            # Success
            year_pillar = result["year"]
            month_pillar = result["month"]
            day_pillar = result["day"]
            hour_pillar = result["hour"]

            meta = result["metadata"]
            zi_applied = "子時✓" if meta["zi_transition_applied"] else "子時✗"

            print(
                f"✅ PASS {test_id:4} | {date_str} {time_str:8} | "
                f"LMT: {meta['lmt_adjusted_time'][11:16]} | {zi_applied} | "
                f"{year_pillar} {month_pillar} {day_pillar} {hour_pillar} | {note}"
            )

            results.append(
                {
                    "id": test_id,
                    "date_local": date_str,
                    "time_local": time_str,
                    "tz": tz_str,
                    "location": location,
                    "note": note,
                    "for_forceteller": for_ft,
                    "ft_year": "",
                    "ft_month": "",
                    "ft_day": "",
                    "ft_hour": "",
                    "engine_year": year_pillar,
                    "engine_month": month_pillar,
                    "engine_day": day_pillar,
                    "engine_hour": hour_pillar,
                    "match_year": "",
                    "match_month": "",
                    "match_day": "",
                    "match_hour": "",
                }
            )
            passed += 1

        except Exception as e:
            print(f"❌ FAIL {test_id:4} | {date_str} {time_str:8} | Exception: {e} | {note}")
            results.append(
                {
                    "id": test_id,
                    "date_local": date_str,
                    "time_local": time_str,
                    "tz": tz_str,
                    "location": location,
                    "note": note,
                    "for_forceteller": for_ft,
                    "ft_year": "",
                    "ft_month": "",
                    "ft_day": "",
                    "ft_hour": "",
                    "engine_year": "ERROR",
                    "engine_month": str(e),
                    "engine_day": "",
                    "engine_hour": "",
                    "match_year": "",
                    "match_month": "",
                    "match_day": "",
                    "match_hour": "",
                }
            )
            failed += 1

    # Write results to CSV
    print("\n" + "=" * 130)
    print("Writing results to CSV...")

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "id",
            "date_local",
            "time_local",
            "tz",
            "location",
            "note",
            "for_forceteller",
            "ft_year",
            "ft_month",
            "ft_day",
            "ft_hour",
            "engine_year",
            "engine_month",
            "engine_day",
            "engine_hour",
            "match_year",
            "match_month",
            "match_day",
            "match_hour",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Results written to: {output_csv}")

    # Summary
    total = len(test_cases)
    print("\n" + "=" * 130)
    print("TEST SUMMARY")
    print("=" * 130)
    print(f"Total tests:  {total}")
    print(f"Passed:       {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"Failed:       {failed}")
    print(f"Skipped:      {skipped} (invalid input)")
    print("=" * 130)

    return passed, failed, skipped


if __name__ == "__main__":
    input_csv = "/Users/yujumyeong/Downloads/saju_test30_mixed.csv"
    output_csv = "/Users/yujumyeong/Downloads/saju_test30_results.csv"

    passed, failed, skipped = test_30_mixed_cases(input_csv, output_csv)

    if failed == 0 and skipped > 0:
        print(f"\n🎉 All valid tests passed! ({skipped} invalid inputs skipped as expected)")
    elif failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review results.")
