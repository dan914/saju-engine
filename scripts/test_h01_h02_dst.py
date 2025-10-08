#!/usr/bin/env python3
"""
Test H01 and H02 cases with DST correction.

These previously failed because FortuneTeller accounts for DST
but our engine didn't.
"""

from datetime import datetime
from calculate_pillars_traditional import calculate_four_pillars


def test_dst_cases():
    """Test H01 and H02 with DST correction."""

    print("=" * 120)
    print("H01/H02 DST CORRECTION TEST")
    print("=" * 120)
    print()

    # Expected results from FortuneTeller
    expected = {
        'H01': {'year': '丁卯', 'month': '乙巳', 'day': '己未', 'hour': '甲子'},
        'H02': {'year': '戊辰', 'month': '丁巳', 'day': '癸亥', 'hour': '壬子'},
    }

    test_cases = [
        ('H01', datetime(1987, 5, 10, 2, 30)),
        ('H02', datetime(1988, 5, 8, 2, 30)),
    ]

    for test_id, birth_dt in test_cases:
        result = calculate_four_pillars(
            birth_dt,
            tz_str='Asia/Seoul',
            mode='traditional_kr',
            return_metadata=True
        )

        exp = expected[test_id]
        meta = result['metadata']

        # Check match
        year_match = result['year'] == exp['year']
        month_match = result['month'] == exp['month']
        day_match = result['day'] == exp['day']
        hour_match = result['hour'] == exp['hour']

        matches = sum([year_match, month_match, day_match, hour_match])

        if matches == 4:
            status = "✅ PERFECT"
        else:
            status = f"❌ {matches}/4"

        print(f"{status} | {test_id} | {birth_dt.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Expected: {exp['year']} {exp['month']} {exp['day']} {exp['hour']}")
        print(f"  Got:      {result['year']} {result['month']} {result['day']} {result['hour']}")
        print(f"  DST:      {meta['dst_applied']}")
        print(f"  LMT time: {meta['lmt_adjusted_time']}")

        if meta.get('warnings'):
            for warning in meta['warnings']:
                print(f"  ⚠️  {warning}")

        print()

    print("=" * 120)


if __name__ == "__main__":
    test_dst_cases()
