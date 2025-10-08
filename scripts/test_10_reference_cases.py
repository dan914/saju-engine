#!/usr/bin/env python3
"""
Test the 10 reference cases with the fixed zi hour logic.
"""

from datetime import datetime
from calculate_pillars_traditional import calculate_four_pillars

# Reference cases with expected results
REFERENCE_CASES = [
    {
        'id': 'REF-01',
        'date': datetime(1974, 11, 7, 21, 14),
        'expected': {'year': '甲寅', 'month': '甲戌', 'day': '壬子', 'hour': '庚戌'}
    },
    {
        'id': 'REF-02',
        'date': datetime(1988, 3, 26, 5, 22),
        'expected': {'year': '戊辰', 'month': '乙卯', 'day': '庚辰', 'hour': '戊寅'}
    },
    {
        'id': 'REF-03',
        'date': datetime(1995, 5, 15, 14, 20),
        'expected': {'year': '乙亥', 'month': '辛巳', 'day': '丙午', 'hour': '乙未'}
    },
    {
        'id': 'REF-04',
        'date': datetime(2001, 9, 3, 3, 7),
        'expected': {'year': '辛巳', 'month': '丙申', 'day': '己巳', 'hour': '乙丑'}
    },
    {
        'id': 'REF-05',
        'date': datetime(2007, 12, 29, 17, 53),
        'expected': {'year': '丁亥', 'month': '壬子', 'day': '丁酉', 'hour': '己酉'}
    },
    {
        'id': 'REF-06',
        'date': datetime(2013, 4, 18, 10, 41),
        'expected': {'year': '癸巳', 'month': '丙辰', 'day': '甲寅', 'hour': '己巳'}
    },
    {
        'id': 'REF-07',
        'date': datetime(2016, 2, 29, 0, 37),
        'expected': {'year': '丙申', 'month': '庚寅', 'day': '辛巳', 'hour': '戊子'}
    },
    {
        'id': 'REF-08',
        'date': datetime(2019, 8, 7, 23, 58),
        'expected': {'year': '己亥', 'month': '辛未', 'day': '丁丑', 'hour': '庚子'}
    },
    {
        'id': 'REF-09',
        'date': datetime(2021, 1, 1, 0, 1),
        'expected': {'year': '庚子', 'month': '戊子', 'day': '己酉', 'hour': '甲子'}
    },
    {
        'id': 'REF-10',
        'date': datetime(2024, 11, 7, 6, 5),
        'expected': {'year': '甲辰', 'month': '甲戌', 'day': '乙亥', 'hour': '己卯'}
    },
]

def format_pillar(stem, branch):
    """Format a pillar as a single string."""
    return f"{stem}{branch}"

def main():
    print("=" * 120)
    print("TESTING 10 REFERENCE CASES (WITH FIXED ZI HOUR LOGIC)")
    print("=" * 120)
    print()

    total_cases = 0
    perfect_matches = 0
    total_pillars = 0
    matched_pillars = 0

    for case in REFERENCE_CASES:
        test_id = case['id']
        date = case['date']
        expected = case['expected']

        # Calculate using the fixed engine
        result = calculate_four_pillars(
            birth_dt=date,
            tz_str='Asia/Seoul',
            mode='traditional_kr',
            validate_input=True,
            return_metadata=True,
            zi_hour_mode='traditional'
        )

        if 'error' in result:
            print(f"❌ ERROR {test_id} | {date} | {result['error']}")
            continue

        total_cases += 1
        total_pillars += 4

        # Format results
        result_year = format_pillar(*result['year'])
        result_month = format_pillar(*result['month'])
        result_day = format_pillar(*result['day'])
        result_hour = format_pillar(*result['hour'])

        # Compare
        year_match = result_year == expected['year']
        month_match = result_month == expected['month']
        day_match = result_day == expected['day']
        hour_match = result_hour == expected['hour']

        matches = sum([year_match, month_match, day_match, hour_match])
        matched_pillars += matches

        if matches == 4:
            status = "✅ PASS"
            perfect_matches += 1
        else:
            status = f"❌ FAIL {matches}/4"

        # Output
        print(f"{status:12} | {test_id:7} | {date} | ", end='')

        if matches == 4:
            print(f"{result_year} {result_month} {result_day} {result_hour}")
        else:
            # Show differences
            parts = []
            if not year_match:
                parts.append(f"Y:{result_year}≠{expected['year']}")
            if not month_match:
                parts.append(f"M:{result_month}≠{expected['month']}")
            if not day_match:
                parts.append(f"D:{result_day}≠{expected['day']}")
            if not hour_match:
                parts.append(f"H:{result_hour}≠{expected['hour']}")
            print(" | ".join(parts))

    # Summary
    print()
    print("=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print(f"Total cases:        {total_cases}")
    print(f"Perfect matches:    {perfect_matches}/{total_cases} ({100*perfect_matches/total_cases:.1f}%)")
    print(f"Total pillars:      {total_pillars}")
    print(f"Matched pillars:    {matched_pillars}/{total_pillars} ({100*matched_pillars/total_pillars:.1f}%)")
    print("=" * 120)

    if perfect_matches == total_cases:
        print(f"\n🎉 PERFECT! All {total_cases} reference cases pass! 🎉")
        print("✅ 100% accuracy achieved!")
    else:
        print(f"\n⚠️  {total_cases - perfect_matches} case(s) still failing")

if __name__ == "__main__":
    main()
