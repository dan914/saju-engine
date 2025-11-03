#!/usr/bin/env python3
"""
Compare engine results with FortuneTeller reference data for 30 test cases.
"""

import csv


def compare_results():
    """Compare engine results with FortuneTeller reference data."""

    # Read engine results
    engine_results = {}
    with open("/Users/yujumyeong/Downloads/saju_test30_results.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            engine_results[row["id"]] = {
                "year": row["engine_year"],
                "month": row["engine_month"],
                "day": row["engine_day"],
                "hour": row["engine_hour"],
            }

    # Read FortuneTeller reference data
    ft_data = {}
    with open(
        "/Users/yujumyeong/Downloads/saju_test30_results_template_v2_filled.csv",
        "r",
        encoding="utf-8",
    ) as f:
        lines = f.readlines()
        # Skip first line if it's empty
        if lines and lines[0].strip() == "":
            lines = lines[1:]

        reader = csv.DictReader(lines)
        for row in reader:
            if row.get("id"):  # Skip empty rows
                ft_data[row["id"]] = {
                    "year": row["ft_year"],
                    "month": row["ft_month"],
                    "day": row["ft_day"],
                    "hour": row["ft_hour"],
                }

    print("=" * 150)
    print("COMPARISON: SAJU ENGINE vs FORTUNETELLER REFERENCE DATA")
    print("=" * 150)
    print()

    total_tests = 0
    total_pillars = 0
    matched_pillars = 0
    perfect_matches = 0

    for test_id in sorted(engine_results.keys()):
        engine = engine_results[test_id]
        ft = ft_data.get(test_id, {"year": "", "month": "", "day": "", "hour": ""})

        # Skip if no FortuneTeller data
        if not ft["year"]:
            continue

        # Skip if engine error
        if engine["year"] == "ERROR" or not engine["year"]:
            continue

        total_tests += 1

        # Compare each pillar
        year_match = engine["year"] == ft["year"]
        month_match = engine["month"] == ft["month"]
        day_match = engine["day"] == ft["day"]
        hour_match = engine["hour"] == ft["hour"]

        matches = sum([year_match, month_match, day_match, hour_match])
        total_pillars += 4
        matched_pillars += matches

        if matches == 4:
            perfect_matches += 1
            status = "✅ PERFECT"
        else:
            status = f"❌ {matches}/4"

        # Format output
        print(f"{status} | {test_id:4} | ", end="")

        # Year
        if year_match:
            print(f"Y:✅ {engine['year']} ", end="")
        else:
            print(f"Y:❌ {engine['year']}≠{ft['year']} ", end="")

        # Month
        if month_match:
            print(f"M:✅ {engine['month']} ", end="")
        else:
            print(f"M:❌ {engine['month']}≠{ft['month']} ", end="")

        # Day
        if day_match:
            print(f"D:✅ {engine['day']} ", end="")
        else:
            print(f"D:❌ {engine['day']}≠{ft['day']} ", end="")

        # Hour
        if hour_match:
            print(f"H:✅ {engine['hour']}")
        else:
            print(f"H:❌ {engine['hour']}≠{ft['hour']}")

    # Summary
    print()
    print("=" * 150)
    print("COMPARISON SUMMARY")
    print("=" * 150)
    print(f"Tests compared:     {total_tests}")
    print(
        f"Perfect matches:    {perfect_matches}/{total_tests} ({100*perfect_matches/total_tests if total_tests > 0 else 0:.1f}%)"
    )
    print(f"Total pillars:      {total_pillars}")
    print(
        f"Matched pillars:    {matched_pillars}/{total_pillars} ({100*matched_pillars/total_pillars if total_pillars > 0 else 0:.1f}%)"
    )
    print("=" * 150)

    return perfect_matches, total_tests


if __name__ == "__main__":
    perfect, total = compare_results()

    if perfect == total:
        print(f"\n🎉 PERFECT! All {total} tests match FortuneTeller! 🎉")
    else:
        print(f"\n⚠️  {total - perfect} test(s) don't match FortuneTeller reference data")
