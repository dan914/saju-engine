#!/usr/bin/env python3
"""
Calculate Four Pillars with Traditional Korean Rules (子時 + LMT).

This implementation uses:
1. Local Mean Time (LMT) adjustment for Seoul (-32 minutes)
2. Traditional 子時 (Zi Hour) day transition rule (23:00 = next day)
3. Refined Saju Lite astronomical solar terms (with ΔT corrections)
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

# Constants
SEXAGENARY_CYCLE = [
    "甲子",
    "乙丑",
    "丙寅",
    "丁卯",
    "戊辰",
    "己巳",
    "庚午",
    "辛未",
    "壬申",
    "癸酉",
    "甲戌",
    "乙亥",
    "丙子",
    "丁丑",
    "戊寅",
    "己卯",
    "庚辰",
    "辛巳",
    "壬午",
    "癸未",
    "甲申",
    "乙酉",
    "丙戌",
    "丁亥",
    "戊子",
    "己丑",
    "庚寅",
    "辛卯",
    "壬辰",
    "癸巳",
    "甲午",
    "乙未",
    "丙申",
    "丁酉",
    "戊戌",
    "己亥",
    "庚子",
    "辛丑",
    "壬寅",
    "癸卯",
    "甲辰",
    "乙巳",
    "丙午",
    "丁未",
    "戊申",
    "己酉",
    "庚戌",
    "辛亥",
    "壬子",
    "癸丑",
    "甲寅",
    "乙卯",
    "丙辰",
    "丁巳",
    "戊午",
    "己未",
    "庚申",
    "辛酉",
    "壬戌",
    "癸亥",
]

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
HOUR_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

YEAR_STEM_TO_MONTH_START = {
    "甲": "丙",
    "己": "丙",
    "乙": "戊",
    "庚": "戊",
    "丙": "庚",
    "辛": "庚",
    "丁": "壬",
    "壬": "壬",
    "戊": "甲",
    "癸": "甲",
}

DAY_STEM_TO_HOUR_START = {
    "甲": "甲",
    "己": "甲",
    "乙": "丙",
    "庚": "丙",
    "丙": "戊",
    "辛": "戊",
    "丁": "庚",
    "壬": "庚",
    "戊": "壬",
    "癸": "壬",
}

TERM_TO_BRANCH = {
    "小寒": "丑",
    "立春": "寅",
    "驚蟄": "卯",
    "清明": "辰",
    "立夏": "巳",
    "芒種": "午",
    "小暑": "未",
    "立秋": "申",
    "白露": "酉",
    "寒露": "戌",
    "立冬": "亥",
    "大雪": "子",
}

MAJOR_TERMS = [
    "小寒",
    "立春",
    "驚蟄",
    "清明",
    "立夏",
    "芒種",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
]

KOREAN_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
KOREAN_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# LMT offsets for major cities (minutes)
LMT_OFFSETS = {
    "Asia/Seoul": -32,  # 126.978°E vs 135°E
    "Asia/Busan": -24,  # 129.075°E vs 135°E
    "Asia/Tokyo": -31,  # 139.692°E vs 135°E
    "Asia/Shanghai": +21,  # 121.472°E vs 120°E
}


def hanja_to_korean(pillar: str) -> str:
    """Convert hanja pillar to Korean pronunciation."""
    stem = pillar[0]
    branch = pillar[1]
    stem_kr = KOREAN_STEMS[HEAVENLY_STEMS.index(stem)]
    branch_kr = KOREAN_BRANCHES[EARTHLY_BRANCHES.index(branch)]
    return f"{stem_kr}{branch_kr}"


def load_terms_for_year(year: int, use_refined: bool = True) -> list:
    """Load solar terms for a given year."""
    if use_refined:
        data_dir = Path(__file__).resolve().parents[1] / "data" / "canonical" / "canonical_v1"
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    terms_file = data_dir / f"terms_{year}.csv"

    if not terms_file.exists():
        return []

    terms = []
    with terms_file.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            utc_time_str = row["utc_time"]
            utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
            terms.append({"term": row["term"], "utc_time": utc_time})
    return terms


def apply_traditional_adjustments(
    birth_dt: datetime,
    tz_str: str,
    lmt_offset_minutes: Optional[int] = None,
    apply_dst: bool = True,
    zi_hour_mode: str = "traditional",
) -> dict:
    """
    Apply DST, LMT and 子時 (Zi Hour) day transition rule.

    子時 (Zi Hour) modes:
    - 'traditional' (default): Day changes at 23:00
      - 23:00-23:59 = NEXT day (early 子時 / 야자시)
      - 00:00-00:59 = SAME day (late 子時 / 조자시)
    - 'modern': Day changes at 00:00 (midnight)
      - 23:00-23:59 = SAME day
      - 00:00-00:59 = SAME day
      - No special 子時 handling

    Calculation order:
    1. Apply DST adjustment (if applicable)
    2. Apply LMT adjustment
    3. Apply 子時 transition rule (based on zi_hour_mode)
    4. Calculate pillars

    Args:
        birth_dt: Birth datetime in local timezone
        tz_str: IANA timezone string
        lmt_offset_minutes: LMT offset (None = auto-detect from timezone)
        apply_dst: Whether to apply DST correction (default: True)
        zi_hour_mode: 子時 handling mode ('traditional' or 'modern')

    Returns:
        {
            'lmt_adjusted': datetime,     # For solar term lookup and hour pillar
            'day_for_pillar': date,       # For day pillar (may be next day if 子時)
            'lmt_offset': int,            # Minutes applied
            'zi_transition': bool,        # Whether 子時 rule was applied
            'zi_hour_mode': str,          # Mode used
            'dst_applied': bool,          # Whether DST was applied
            'warnings': list              # Any timezone warnings
        }
    """
    warnings = []
    dst_applied = False

    # Step 0: Apply DST if applicable (1948-1960, 1987-1988)
    if apply_dst:
        # Extract naive datetime for comparison
        birth_naive = birth_dt.replace(tzinfo=None) if birth_dt.tzinfo else birth_dt

        # Check if in DST period
        DST_PERIODS = [
            # 1948-1960 periods
            (datetime(1948, 6, 1), datetime(1948, 9, 13)),
            (datetime(1949, 4, 3), datetime(1949, 9, 11)),
            (datetime(1950, 4, 1), datetime(1950, 9, 10)),
            (datetime(1951, 5, 6), datetime(1951, 9, 9)),
            (datetime(1955, 5, 5), datetime(1955, 9, 9)),
            (datetime(1956, 5, 20), datetime(1956, 9, 30)),
            (datetime(1957, 5, 5), datetime(1957, 9, 22)),
            (datetime(1958, 5, 4), datetime(1958, 9, 21)),
            (datetime(1959, 5, 3), datetime(1959, 9, 20)),
            (datetime(1960, 5, 1), datetime(1960, 9, 18)),
            # 1987-1988 Olympic periods
            (datetime(1987, 5, 10, 2), datetime(1987, 10, 11, 3)),
            (datetime(1988, 5, 8, 2), datetime(1988, 10, 9, 3)),
        ]

        for start, end in DST_PERIODS:
            if start <= birth_naive < end:
                # During DST: subtract 1 hour to get standard time
                birth_dt = birth_dt - timedelta(hours=1)
                dst_applied = True
                warnings.append("DST applied: -1 hour to standard time")
                break

    # Auto-detect LMT offset if not provided
    if lmt_offset_minutes is None:
        lmt_offset_minutes = LMT_OFFSETS.get(tz_str, 0)

    # Step 1: Apply LMT adjustment
    lmt_adjusted = birth_dt - timedelta(minutes=abs(lmt_offset_minutes))

    # Step 2: Apply 子時 transition rule (based on mode)
    zi_transition_applied = False

    if zi_hour_mode == "traditional":
        # Traditional: Day changes at 23:00 (based on ASTRONOMICAL/LMT time)
        # Check zi hour AFTER LMT adjustment - uses solar time, not clock time
        if lmt_adjusted.hour == 23:
            # Early 子時 (23:00-23:59) belongs to NEXT day (야자시)
            # Use LMT-adjusted date + 1 day
            day_for_pillar = lmt_adjusted.date() + timedelta(days=1)
            zi_transition_applied = True
        else:
            # Late 子時 (00:00-00:59) and all other hours use same day (조자시)
            day_for_pillar = lmt_adjusted.date()

    elif zi_hour_mode == "modern":
        # Modern: Day changes at 00:00 (midnight boundary)
        # Use the ORIGINAL input date (not LMT-adjusted date)
        # This respects the user's calendar date regardless of astronomical time
        day_for_pillar = birth_dt.date()
        zi_transition_applied = False

    else:
        # Invalid mode, default to traditional
        warnings.append(f"Invalid zi_hour_mode '{zi_hour_mode}', using 'traditional'")
        if lmt_adjusted.hour == 23:
            day_for_pillar = lmt_adjusted.date() + timedelta(days=1)
            zi_transition_applied = True
        else:
            day_for_pillar = lmt_adjusted.date()

    return {
        "lmt_adjusted": lmt_adjusted,
        "time_after_dst": birth_dt,  # Time after DST but before LMT (for hour pillar)
        "day_for_pillar": day_for_pillar,
        "lmt_offset": lmt_offset_minutes,
        "zi_transition": zi_transition_applied,
        "zi_hour_mode": zi_hour_mode,
        "dst_applied": dst_applied,
        "warnings": warnings,
    }


def calculate_year_pillar(
    birth_dt: datetime, tz: ZoneInfo, terms_current: list, terms_prev: list
) -> tuple:
    """
    Calculate year pillar based on 立春 (Lichun) solar term.

    Returns:
        (year_pillar, year_for_calculation)
    """
    aware_dt = birth_dt.replace(tzinfo=tz) if birth_dt.tzinfo is None else birth_dt

    # Find 立春 for current year
    all_terms = terms_prev + terms_current
    lichun = None
    for term in all_terms:
        if term["term"] == "立春":
            local_time = term["utc_time"].astimezone(tz)
            if local_time.year == aware_dt.year:
                lichun = local_time
                break

    # If birth is before 立春, use previous year
    if lichun and aware_dt < lichun:
        year_for_calculation = aware_dt.year - 1
    else:
        year_for_calculation = aware_dt.year

    # Calculate year pillar
    anchor_year = 1984  # 1984 = 甲子 (index 0)
    year_offset = year_for_calculation - anchor_year
    year_index = year_offset % 60
    year_pillar = SEXAGENARY_CYCLE[year_index]

    return year_pillar, year_for_calculation


def calculate_month_pillar(
    lmt_adjusted: datetime, tz: ZoneInfo, year_pillar: str, terms_current: list, terms_prev: list
) -> tuple:
    """
    Calculate month pillar based on major solar terms.

    Returns:
        (month_pillar, solar_term_name)
    """
    aware_dt = lmt_adjusted.replace(tzinfo=tz) if lmt_adjusted.tzinfo is None else lmt_adjusted

    # Combine terms from current and previous year
    all_terms = terms_prev + terms_current

    # Find current major term
    current_term = None
    for term in all_terms:
        if term["term"] not in MAJOR_TERMS:
            continue
        local_time = term["utc_time"].astimezone(tz)
        if local_time <= aware_dt:
            current_term = term
        else:
            break

    if not current_term:
        return None, None

    month_branch = TERM_TO_BRANCH[current_term["term"]]

    # Calculate month stem from year stem
    year_stem = year_pillar[0]
    month_start_stem = YEAR_STEM_TO_MONTH_START[year_stem]
    start_stem_index = HEAVENLY_STEMS.index(month_start_stem)
    anchor_branch_index = EARTHLY_BRANCHES.index("寅")
    month_branch_index = EARTHLY_BRANCHES.index(month_branch)
    offset = (month_branch_index - anchor_branch_index) % 12
    month_stem_index = (start_stem_index + offset) % 10
    month_stem = HEAVENLY_STEMS[month_stem_index]
    month_pillar = month_stem + month_branch

    return month_pillar, current_term["term"]


def calculate_day_pillar(day_for_pillar: datetime.date) -> str:
    """
    Calculate day pillar using the adjusted date from 子時 rule.

    Args:
        day_for_pillar: Date after LMT and 子時 adjustments
    """
    anchor_date = datetime(1900, 1, 1).date()  # 1900-01-01 = 甲戌
    anchor_index = SEXAGENARY_CYCLE.index("甲戌")  # 10

    delta_days = (day_for_pillar - anchor_date).days
    day_index = (anchor_index + delta_days) % 60

    return SEXAGENARY_CYCLE[day_index]


def calculate_hour_pillar(lmt_adjusted: datetime, day_stem: str) -> str:
    """
    Calculate hour pillar using LMT-adjusted time (solar time).

    Hour boundaries are fixed 2-hour blocks based on solar time:
    子時 = 23:00-00:59, 丑時 = 01:00-02:59, etc.

    Args:
        lmt_adjusted: Time after LMT adjustment (solar time)
        day_stem: Stem from day pillar (already adjusted by 子時 rule)
    """
    hour = lmt_adjusted.hour

    # Standard 2-hour boundaries
    hour_branch_index = ((hour + 1) // 2) % 12
    hour_branch = HOUR_BRANCHES[hour_branch_index]

    # Calculate stem from day stem
    hour_start_stem = DAY_STEM_TO_HOUR_START[day_stem]
    hour_stem_index = (HEAVENLY_STEMS.index(hour_start_stem) + hour_branch_index) % 10
    hour_stem = HEAVENLY_STEMS[hour_stem_index]

    return hour_stem + hour_branch


def calculate_four_pillars(
    birth_dt: datetime,
    tz_str: str = "Asia/Seoul",
    mode: str = "traditional_kr",
    validate_input: bool = True,
    lmt_offset_minutes: Optional[int] = None,
    use_refined: bool = True,
    return_metadata: bool = False,
    zi_hour_mode: str = "traditional",
) -> dict:
    """
    Calculate Four Pillars with configurable calculation mode.

    Args:
        birth_dt: Birth datetime in local timezone
        tz_str: IANA timezone (e.g., 'Asia/Seoul')
        mode: Calculation mode ('traditional_kr', 'modern')
        validate_input: Validate input datetime (default: True)
        lmt_offset_minutes: Manual LMT override (None = auto-calculate)
        use_refined: Use refined astronomical data (default: True)
        return_metadata: Include calculation details in result
        zi_hour_mode: 子時 (Zi hour) handling mode
            - 'traditional': Day changes at 23:00 (야자시/조자시 rule)
            - 'modern': Day changes at 00:00 (midnight boundary)

    Returns:
        {
            'year': '庚子',
            'month': '戊子',
            'day': '己酉',
            'hour': '甲子',
            'metadata': {...}  # if return_metadata=True
        }
    """
    # Input validation
    if validate_input:
        # Import validator
        import sys
        from pathlib import Path

        sys.path.insert(
            0, str(Path(__file__).parent.parent / "services" / "pillars-service" / "app" / "core")
        )
        try:
            import input_validator as iv

            valid, error = iv.BirthDateTimeValidator.validate_datetime_object(birth_dt)
            if not valid:
                return {"error": f"Invalid input: {error}"}
        except ImportError:
            # Validator not available, skip validation
            pass

    tz = ZoneInfo(tz_str)
    aware_dt = birth_dt.replace(tzinfo=tz) if birth_dt.tzinfo is None else birth_dt

    # Load solar terms
    terms_current = load_terms_for_year(aware_dt.year, use_refined)
    terms_prev = load_terms_for_year(aware_dt.year - 1, use_refined)

    if not terms_current and not terms_prev:
        return {"error": f"No terms data for {aware_dt.year}"}

    # Apply adjustments based on mode
    if mode == "traditional_kr":
        adjustments = apply_traditional_adjustments(
            aware_dt, tz_str, lmt_offset_minutes, zi_hour_mode=zi_hour_mode
        )
        lmt_adjusted = adjustments["lmt_adjusted"]
        day_for_pillar = adjustments["day_for_pillar"]
    else:  # modern mode
        lmt_adjusted = aware_dt
        day_for_pillar = aware_dt.date()
        adjustments = {"lmt_offset": 0, "zi_transition": False}

    # Calculate year pillar
    year_pillar, year_used = calculate_year_pillar(lmt_adjusted, tz, terms_current, terms_prev)

    # Calculate month pillar
    month_pillar, solar_term = calculate_month_pillar(
        lmt_adjusted, tz, year_pillar, terms_current, terms_prev
    )

    if not month_pillar:
        return {"error": "No applicable solar term"}

    # Calculate day pillar (using adjusted date from 子時 rule)
    day_pillar = calculate_day_pillar(day_for_pillar)

    # Calculate hour pillar (using LMT-adjusted time and day stem from adjusted day)
    day_stem = day_pillar[0]
    hour_pillar = calculate_hour_pillar(lmt_adjusted, day_stem)

    result = {"year": year_pillar, "month": month_pillar, "day": day_pillar, "hour": hour_pillar}

    if return_metadata:
        result["metadata"] = {
            "mode": mode,
            "lmt_offset": adjustments["lmt_offset"],
            "lmt_adjusted_time": lmt_adjusted.strftime("%Y-%m-%d %H:%M:%S"),
            "zi_transition_applied": adjustments["zi_transition"],
            "zi_hour_mode": adjustments.get("zi_hour_mode", "traditional"),
            "dst_applied": adjustments.get("dst_applied", False),
            "day_for_pillar": day_for_pillar.strftime("%Y-%m-%d"),
            "solar_term": solar_term,
            "year_used": year_used,
            "data_source": "CANONICAL_V1",
            "algo_version": "v1.6.1+dst+zi_toggle",
            "warnings": adjustments.get("warnings", []),
        }

    return result


if __name__ == "__main__":
    # Test with the 10 reference cases
    test_cases = [
        (1, "1974-11-07", "21:14", "Asia/Seoul", "甲寅", "甲戌", "壬子", "庚戌"),
        (2, "1988-03-26", "05:22", "Asia/Seoul", "戊辰", "乙卯", "庚辰", "戊寅"),
        (3, "1995-05-15", "14:20", "Asia/Seoul", "乙亥", "辛巳", "丙午", "乙未"),
        (4, "2001-09-03", "03:07", "Asia/Seoul", "辛巳", "丙申", "己巳", "乙丑"),
        (5, "2007-12-29", "17:53", "Asia/Seoul", "丁亥", "壬子", "丁酉", "己酉"),
        (6, "2013-04-18", "10:41", "Asia/Seoul", "癸巳", "丙辰", "甲寅", "己巳"),
        (7, "2016-02-29", "00:37", "Asia/Seoul", "丙申", "庚寅", "辛巳", "戊子"),
        (8, "2019-08-07", "23:58", "Asia/Seoul", "己亥", "辛未", "丁丑", "庚子"),
        (9, "2021-01-01", "00:01", "Asia/Seoul", "庚子", "戊子", "己酉", "甲子"),
        (10, "2024-11-07", "06:05", "Asia/Seoul", "甲辰", "甲戌", "乙亥", "己卯"),
    ]

    print("=" * 120)
    print("TRADITIONAL KOREAN SAJU CALCULATION (子時 Rule + LMT)")
    print("=" * 120)

    passed = 0
    failed = 0

    for test_id, date_str, time_str, tz_str, ref_yr, ref_mo, ref_dy, ref_hr in test_cases:
        date_parts = date_str.split("-")
        time_parts = time_str.split(":")

        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        hour = int(time_parts[0])
        minute = int(time_parts[1])

        birth_dt = datetime(year, month, day, hour, minute)
        result = calculate_four_pillars(
            birth_dt, tz_str, mode="traditional_kr", return_metadata=True
        )

        print(f"\n[{test_id}] {date_str} {time_str} {tz_str}")
        print("-" * 120)

        if "error" in result:
            print(f"ERROR: {result['error']}")
            failed += 4
        else:
            # Check each pillar
            pillars = [
                ("Year", result["year"], ref_yr),
                ("Month", result["month"], ref_mo),
                ("Day", result["day"], ref_dy),
                ("Hour", result["hour"], ref_hr),
            ]

            test_passed = 0
            for name, mine, ref in pillars:
                match = "✅" if mine == ref else "❌"
                print(f"{name:6} - Mine: {mine} | Ref: {ref} {match}")
                if mine == ref:
                    passed += 1
                    test_passed += 1
                else:
                    failed += 1

            # Show metadata
            meta = result["metadata"]
            print(f"\nMetadata:")
            print(f"  LMT offset: {meta['lmt_offset']} minutes")
            print(f"  LMT adjusted: {meta['lmt_adjusted_time']}")
            print(f"  子時 transition: {meta['zi_transition_applied']}")
            print(f"  Day for pillar: {meta['day_for_pillar']}")
            print(f"  Solar term: {meta['solar_term']}")
            print(f"  Test result: {test_passed}/4 pillars correct")

    print("\n" + "=" * 120)
    print("FINAL RESULTS")
    print("=" * 120)
    print(f"Total pillars: {passed + failed}")
    print(f"Passed: {passed}/{passed + failed} ({100*passed/(passed+failed):.1f}%)")
    print(f"Failed: {failed}")
    print("=" * 120)
