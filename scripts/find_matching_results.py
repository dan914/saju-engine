#!/usr/bin/env python3
"""
Find which engine results match which FortuneTeller reference data.
Cross-reference all combinations to find correct mappings.
"""

import csv


def find_matches():
    """Find matching results between engine and FortuneTeller data."""

    # Read engine results
    engine_results = {}
    engine_dates = {}
    with open("/Users/yujumyeong/Downloads/saju_test30_results.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_id = row["id"]
            engine_results[test_id] = {
                "year": row["engine_year"],
                "month": row["engine_month"],
                "day": row["engine_day"],
                "hour": row["engine_hour"],
            }
            engine_dates[test_id] = f"{row['date_local']} {row['time_local']}"

    # Read FortuneTeller reference data
    ft_data = {}
    with open(
        "/Users/yujumyeong/Downloads/saju_test30_results_template_v2_filled.csv",
        "r",
        encoding="utf-8",
    ) as f:
        lines = f.readlines()
        if lines and lines[0].strip() == "":
            lines = lines[1:]

        reader = csv.DictReader(lines)
        for row in reader:
            if row.get("id") and row.get("ft_year"):
                ft_data[row["id"]] = {
                    "year": row["ft_year"],
                    "month": row["ft_month"],
                    "day": row["ft_day"],
                    "hour": row["ft_hour"],
                }

    print("=" * 130)
    print("CROSS-REFERENCE: Finding matching results")
    print("=" * 130)
    print()

    # Cross-reference all combinations
    matches_found = []

    for engine_id, engine_pillars in engine_results.items():
        if engine_pillars["year"] == "ERROR" or not engine_pillars["year"]:
            continue

        for ft_id, ft_pillars in ft_data.items():
            # Check if all 4 pillars match
            if (
                engine_pillars["year"] == ft_pillars["year"]
                and engine_pillars["month"] == ft_pillars["month"]
                and engine_pillars["day"] == ft_pillars["day"]
                and engine_pillars["hour"] == ft_pillars["hour"]
            ):

                matches_found.append(
                    {
                        "engine_id": engine_id,
                        "ft_id": ft_id,
                        "pillars": f"{engine_pillars['year']} {engine_pillars['month']} {engine_pillars['day']} {engine_pillars['hour']}",
                        "date": engine_dates[engine_id],
                    }
                )

    # Print matches
    if matches_found:
        print("PERFECT MATCHES FOUND:")
        print()
        for match in matches_found:
            same_id = "✅ SAME ID" if match["engine_id"] == match["ft_id"] else "⚠️  DIFFERENT ID"
            print(
                f"{same_id:15} | Engine: {match['engine_id']:4} | FT: {match['ft_id']:4} | "
                f"{match['pillars']} | {match['date']}"
            )
    else:
        print("No perfect matches found.")

    print()
    print("=" * 130)
    print(f"Total perfect matches: {len(matches_found)}")
    print("=" * 130)

    return matches_found


if __name__ == "__main__":
    matches = find_matches()
