#!/usr/bin/env python3
"""
Compare FortuneTeller results (from user's message) with engine results.
"""

import csv

# FortuneTeller results from user's message
ft_results = {
    "E01": {"year": "庚子", "month": "戊子", "day": "己酉", "hour": "甲子"},
    "E02": {"year": "己亥", "month": "辛未", "day": "丁丑", "hour": "庚子"},
    "E03": {"year": "丙申", "month": "庚寅", "day": "辛巳", "hour": "戊子"},
    "E04": {"year": "甲辰", "month": "甲戌", "day": "乙亥", "hour": "己卯"},
    "E05": {"year": "癸卯", "month": "己未", "day": "丁酉", "hour": "庚子"},
    "E06": {"year": "壬寅", "month": "丙午", "day": "乙巳", "hour": "壬午"},
    "E07": {"year": "己亥", "month": "丁丑", "day": "丁丑", "hour": "庚子"},
    "E08": {"year": "己亥", "month": "丁丑", "day": "丁丑", "hour": "庚子"},
    "H01": {"year": "丁卯", "month": "乙巳", "day": "己未", "hour": "甲子"},
    "H02": {"year": "戊辰", "month": "丁巳", "day": "癸亥", "hour": "壬子"},
    "H03": {"year": "丁卯", "month": "庚戌", "day": "癸巳", "hour": "癸丑"},
    "H04": {"year": "戊辰", "month": "壬戌", "day": "丁酉", "hour": "辛丑"},
    "P01": {"year": "庚子", "month": "丙戌", "day": "丙戌", "hour": "戊子"},
}

# Read engine results
engine_results = {}
with open("/Users/yujumyeong/Downloads/saju_test30_results.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        test_id = row["id"]
        engine_results[test_id] = {
            "year": row["engine_year"],
            "month": row["engine_month"],
            "day": row["engine_day"],
            "hour": row["engine_hour"],
            "date": row["date_local"],
            "time": row["time_local"],
        }

print("=" * 140)
print("COMPARISON: ENGINE vs FORTUNETELLER")
print("=" * 140)
print()

total_tests = 0
perfect_matches = 0
total_pillars = 0
matched_pillars = 0

for test_id in sorted(ft_results.keys()):
    ft = ft_results[test_id]
    engine = engine_results.get(test_id)

    if not engine or engine["year"] == "ERROR":
        print(f"⚠️  SKIP {test_id} | Engine error or not found")
        continue

    total_tests += 1
    total_pillars += 4

    # Compare each pillar
    year_match = engine["year"] == ft["year"]
    month_match = engine["month"] == ft["month"]
    day_match = engine["day"] == ft["day"]
    hour_match = engine["hour"] == ft["hour"]

    matches = sum([year_match, month_match, day_match, hour_match])
    matched_pillars += matches

    if matches == 4:
        status = "✅ PERFECT"
        perfect_matches += 1
    else:
        status = f"❌ {matches}/4"

    # Format output
    print(f"{status:11} | {test_id:4} | {engine['date']} {engine['time']:8} |", end=" ")

    # Year
    if year_match:
        print(f"Y:✅", end=" ")
    else:
        print(f"Y:❌ {engine['year']}≠{ft['year']}", end=" ")

    # Month
    if month_match:
        print(f"M:✅", end=" ")
    else:
        print(f"M:❌ {engine['month']}≠{ft['month']}", end=" ")

    # Day
    if day_match:
        print(f"D:✅", end=" ")
    else:
        print(f"D:❌ {engine['day']}≠{ft['day']}", end=" ")

    # Hour
    if hour_match:
        print(f"H:✅")
    else:
        print(f"H:❌ {engine['hour']}≠{ft['hour']}")

# Summary
print()
print("=" * 140)
print("SUMMARY")
print("=" * 140)
print(f"Tests compared:     {total_tests}")
print(
    f"Perfect matches:    {perfect_matches}/{total_tests} ({100*perfect_matches/total_tests:.1f}%)"
)
print(f"Total pillars:      {total_pillars}")
print(
    f"Matched pillars:    {matched_pillars}/{total_pillars} ({100*matched_pillars/total_pillars:.1f}%)"
)
print("=" * 140)

if perfect_matches == total_tests:
    print(f"\n🎉 PERFECT! All {total_tests} tests match FortuneTeller! 🎉")
else:
    print(f"\n⚠️  {total_tests - perfect_matches} test(s) differ from FortuneTeller")
