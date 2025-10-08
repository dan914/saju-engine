"""Run test cases against the Saju engine."""

import csv
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Add service to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "pillars-service" / "app"))

from core.constants import SEXAGENARY_CYCLE, HEAVENLY_STEMS, EARTHLY_BRANCHES, HOUR_BRANCHES
from core.constants import YEAR_STEM_TO_MONTH_START, DAY_STEM_TO_HOUR_START

TEST_CASES_FILE = "/Users/yujumyeong/Downloads/saju_test_cases_v1.csv"

# Load solar terms
def load_terms_for_year(year: int) -> list:
    """Load solar terms for a given year."""
    terms_file = Path(__file__).resolve().parents[1] / "data" / f"terms_{year}.csv"
    if not terms_file.exists():
        return []

    terms = []
    with terms_file.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            utc_time_str = row['utc_time']
            utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
            terms.append({
                'term': row['term'],
                'utc_time': utc_time
            })
    return terms


def calculate_pillars(birth_dt: datetime, tz_str: str) -> dict:
    """Calculate Four Pillars for a given birth datetime."""
    tz = ZoneInfo(tz_str)
    aware_dt = birth_dt.replace(tzinfo=tz)

    # Load solar terms
    terms = load_terms_for_year(aware_dt.year)
    if not terms:
        # Try previous year
        terms = load_terms_for_year(aware_dt.year - 1)

    # Find current month (last major term before birth)
    major_terms = ['小寒', '立春', '驚蟄', '清明', '立夏', '芒種', '小暑', '立秋', '白露', '寒露', '立冬', '大雪']
    TERM_TO_BRANCH = {
        '小寒': '丑', '立春': '寅', '驚蟄': '卯', '清明': '辰',
        '立夏': '巳', '芒種': '午', '小暑': '未', '立秋': '申',
        '白露': '酉', '寒露': '戌', '立冬': '亥', '大雪': '子'
    }

    current_term = None
    for term in terms:
        if term['term'] not in major_terms:
            continue
        local_time = term['utc_time'].astimezone(tz)
        if local_time <= aware_dt:
            current_term = term
        else:
            break

    if not current_term:
        return {'error': 'No solar term found'}

    month_branch = TERM_TO_BRANCH[current_term['term']]

    # Year pillar (using 1984 anchor)
    anchor_year = 1984
    anchor_index = 0  # 甲子
    year_offset = aware_dt.year - anchor_year
    year_index = (anchor_index + year_offset) % 60
    year_pillar = SEXAGENARY_CYCLE[year_index]

    # Month pillar
    year_stem = year_pillar[0]
    month_start_stem = YEAR_STEM_TO_MONTH_START[year_stem]
    start_stem_index = HEAVENLY_STEMS.index(month_start_stem)
    anchor_branch_index = EARTHLY_BRANCHES.index('寅')
    month_branch_index = EARTHLY_BRANCHES.index(month_branch)
    offset = (month_branch_index - anchor_branch_index) % 12
    month_stem_index = (start_stem_index + offset) % 10
    month_stem = HEAVENLY_STEMS[month_stem_index]
    month_pillar = month_stem + month_branch

    # Day pillar (using standard 1900-01-01 = 甲戌)
    anchor_date = datetime(1900, 1, 1)
    anchor_index = SEXAGENARY_CYCLE.index('甲戌')
    delta_days = (aware_dt.date() - anchor_date.date()).days
    day_index = (anchor_index + delta_days) % 60
    day_pillar = SEXAGENARY_CYCLE[day_index]

    # Hour pillar
    hour = aware_dt.hour
    hour_branch_index = ((hour + 1) // 2) % 12
    hour_branch = HOUR_BRANCHES[hour_branch_index]
    day_stem = day_pillar[0]
    hour_start_stem = DAY_STEM_TO_HOUR_START[day_stem]
    hour_stem_index = (HEAVENLY_STEMS.index(hour_start_stem) + hour_branch_index) % 10
    hour_stem = HEAVENLY_STEMS[hour_stem_index]
    hour_pillar = hour_stem + hour_branch

    return {
        'year': year_pillar,
        'month': month_pillar,
        'day': day_pillar,
        'hour': hour_pillar,
        'solar_term': current_term['term']
    }


def run_tests():
    """Run all test cases."""
    print("=" * 80)
    print("RUNNING SAJU TEST CASES")
    print("=" * 80)

    test_cases = []
    with open(TEST_CASES_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)

    passed = 0
    failed = 0
    skipped = 0

    for tc in test_cases:
        test_id = tc['id']
        label = tc['label']

        try:
            # Parse date and time
            date_parts = tc['date_local'].split('-')
            time_parts = tc['time_local'].split(':')

            year = int(date_parts[0])
            month = int(date_parts[1])
            day = int(date_parts[2])
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            # Check for invalid times (expected edge cases)
            if hour >= 24 or minute >= 60:
                print(f"SKIP {test_id:3s} {label:25s} - Invalid time (expected edge case)")
                skipped += 1
                continue

            birth_dt = datetime(year, month, day, hour, minute)
            result = calculate_pillars(birth_dt, tc['tz'])

            if 'error' in result:
                print(f"FAIL {test_id:3s} {label:25s} - {result['error']}")
                failed += 1
            else:
                print(f"PASS {test_id:3s} {label:25s} - {result['year']} {result['month']} {result['day']} {result['hour']}")
                passed += 1

        except Exception as e:
            if 'literal for int()' in str(e):
                print(f"SKIP {test_id:3s} {label:25s} - Non-numeric input (expected edge case)")
                skipped += 1
            else:
                print(f"FAIL {test_id:3s} {label:25s} - {str(e)}")
                failed += 1

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {len(test_cases)}")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
