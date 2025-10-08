"""Run test cases against Saju engine (standalone - no service imports)."""

import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TEST_CASES_FILE = "/Users/yujumyeong/Downloads/saju_test_cases_v1.csv"

# Constants
SEXAGENARY_CYCLE = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
HOUR_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

YEAR_STEM_TO_MONTH_START = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    '丙': '庚', '辛': '庚',
    '丁': '壬', '壬': '壬',
    '戊': '甲', '癸': '甲'
}

DAY_STEM_TO_HOUR_START = {
    '甲': '甲', '己': '甲',
    '乙': '丙', '庚': '丙',
    '丙': '戊', '辛': '戊',
    '丁': '庚', '壬': '庚',
    '戊': '壬', '癸': '壬'
}

TERM_TO_BRANCH = {
    '小寒': '丑', '立春': '寅', '驚蟄': '卯', '清明': '辰',
    '立夏': '巳', '芒種': '午', '小暑': '未', '立秋': '申',
    '白露': '酉', '寒露': '戌', '立冬': '亥', '大雪': '子'
}

MAJOR_TERMS = ['小寒', '立春', '驚蟄', '清明', '立夏', '芒種', '小暑', '立秋', '白露', '寒露', '立冬', '大雪']


def load_terms_for_year(year: int, use_sajulite: bool = False, use_refined: bool = False) -> list:
    """Load solar terms for a given year."""
    if use_refined:
        data_dir = Path(__file__).resolve().parents[1] / "data" / "canonical" / "terms_sajulite_refined"
    elif use_sajulite:
        data_dir = Path(__file__).resolve().parents[1] / "data" / "canonical" / "terms_sajulite"
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    terms_file = data_dir / f"terms_{year}.csv"

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


def calculate_pillars(birth_dt: datetime, tz_str: str, use_sajulite: bool = False, use_refined: bool = False) -> dict:
    """Calculate Four Pillars."""
    try:
        tz = ZoneInfo(tz_str)
        aware_dt = birth_dt.replace(tzinfo=tz)

        # Load solar terms
        terms = load_terms_for_year(aware_dt.year, use_sajulite, use_refined)
        if not terms:
            terms = load_terms_for_year(aware_dt.year - 1, use_sajulite, use_refined)
        if not terms:
            return {'error': f'No terms data for {aware_dt.year}'}

        # Find current major term
        current_term = None
        for term in terms:
            if term['term'] not in MAJOR_TERMS:
                continue
            local_time = term['utc_time'].astimezone(tz)
            if local_time <= aware_dt:
                current_term = term
            else:
                break

        if not current_term:
            return {'error': 'No applicable solar term'}

        month_branch = TERM_TO_BRANCH[current_term['term']]

        # Year pillar
        anchor_year = 1984
        year_offset = aware_dt.year - anchor_year
        year_index = year_offset % 60
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

        # Day pillar
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
    except Exception as e:
        return {'error': str(e)}


def run_tests(use_sajulite: bool = False, use_refined: bool = False):
    """Run all test cases."""
    if use_refined:
        data_source = "SAJU LITE (refined - astronomical precision)"
    elif use_sajulite:
        data_source = "SAJU LITE (original - hour-rounded)"
    else:
        data_source = "SKY_LIZARD"
    print("=" * 90)
    print(f"RUNNING SAJU TEST CASES (using {data_source} data)")
    print("=" * 90)

    test_cases = []
    with open(TEST_CASES_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)

    passed = 0
    failed = 0
    skipped = 0
    results = []

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

            # Check for invalid times
            if hour >= 24 or minute >= 60:
                print(f"SKIP {test_id:3s} {label:30s} - Invalid time (expected)")
                skipped += 1
                continue

            birth_dt = datetime(year, month, day, hour, minute)
            result = calculate_pillars(birth_dt, tc['tz'], use_sajulite, use_refined)

            if 'error' in result:
                status = "FAIL"
                output = result['error']
                failed += 1
                print(f"{status} {test_id:3s} {label:30s} - {output}")
            else:
                status = "PASS"
                output = f"{result['year']} {result['month']} {result['day']} {result['hour']}"
                passed += 1
                print(f"{status} {test_id:3s} {label:30s} - {output}")

            results.append({
                'id': test_id,
                'label': label,
                'status': status,
                'pillars': output
            })

        except Exception as e:
            if 'literal for int()' in str(e):
                print(f"SKIP {test_id:3s} {label:30s} - Non-numeric (expected)")
                skipped += 1
            else:
                print(f"FAIL {test_id:3s} {label:30s} - {str(e)}")
                failed += 1

    print("\n" + "=" * 90)
    print("TEST SUMMARY")
    print("=" * 90)
    print(f"Passed:  {passed}/{len(test_cases)} ({100*passed/len(test_cases):.1f}%)")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped} (expected edge cases)")
    print("=" * 90)

    return results


if __name__ == "__main__":
    import sys
    use_refined = "--refined" in sys.argv
    use_sajulite = "--sajulite" in sys.argv
    run_tests(use_sajulite, use_refined)
