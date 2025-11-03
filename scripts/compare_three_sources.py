"""Compare solar terms from three sources: SKY_LIZARD, KFA, and Manseoryeok."""

import csv
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKY_LIZARD_DIR = REPO_ROOT / "data" / "canonical" / "terms"
KFA_DIR = REPO_ROOT / "data" / "canonical" / "terms_kfa"
MANSEORYEOK_DB = Path(
    "/Users/yujumyeong/Downloads/korean_fortune_apps_complete/manseoryeok_database/perpetualcalendarlite.sqlite"
)

# Mapping Korean term names to Chinese characters
KOREAN_TO_CHINESE = {
    "소한": "小寒",
    "대한": "大寒",
    "입춘": "立春",
    "우수": "雨水",
    "경칩": "驚蟄",
    "춘분": "春分",
    "청명": "清明",
    "곡우": "穀雨",
    "입하": "立夏",
    "소만": "小滿",
    "망종": "芒種",
    "하지": "夏至",
    "소서": "小暑",
    "대서": "大暑",
    "입추": "立秋",
    "처서": "處暑",
    "백로": "白露",
    "추분": "秋分",
    "한로": "寒露",
    "상강": "霜降",
    "입동": "立冬",
    "소설": "小雪",
    "대설": "大雪",
    "동지": "冬至",
}


def parse_utc_time(utc_str: str) -> datetime:
    """Parse UTC timestamp from CSV."""
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    # Return as naive UTC datetime for comparison
    return dt.replace(tzinfo=None)


def load_sky_lizard_terms(year: int) -> dict[str, datetime]:
    """Load SKY_LIZARD terms for a given year."""
    terms = {}
    csv_path = SKY_LIZARD_DIR / f"terms_{year}.csv"
    if not csv_path.exists():
        return terms

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row["term"]
            utc_time = parse_utc_time(row["utc_time"])
            terms[term] = utc_time
    return terms


def load_kfa_terms(year: int) -> dict[str, datetime]:
    """Load KFA/Wonkwang terms for a given year."""
    terms = {}
    csv_path = KFA_DIR / f"terms_{year}.csv"
    if not csv_path.exists():
        return terms

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row["term"]
            utc_time = parse_utc_time(row["utc_time"])
            terms[term] = utc_time
    return terms


def load_manseoryeok_terms(year: int) -> dict[str, datetime]:
    """Load Manseoryeok database terms for a given year."""
    terms = {}
    if not MANSEORYEOK_DB.exists():
        return terms

    conn = sqlite3.connect(MANSEORYEOK_DB)
    cursor = conn.cursor()

    # Query for year's solar terms
    cursor.execute(
        """
        SELECT umdate, jeol, jeoliptime
        FROM mansedata
        WHERE umdate LIKE ? AND jeoliptime <> ''
        ORDER BY umdate
    """,
        (f"{year}%",),
    )

    for umdate, jeol_korean, jeoliptime in cursor.fetchall():
        # umdate format: YYYYMMDD (lunar date)
        # jeoliptime format: HH:MM (KST local time)
        term_chinese = KOREAN_TO_CHINESE.get(jeol_korean)
        if not term_chinese:
            continue

        # Parse the date and time
        try:
            year_val = int(umdate[:4])
            month_val = int(umdate[4:6])
            day_val = int(umdate[6:8])
            hour_val = int(jeoliptime.split(":")[0])
            minute_val = int(jeoliptime.split(":")[1])

            # Create KST datetime and convert to UTC
            kst_time = datetime(year_val, month_val, day_val, hour_val, minute_val)
            utc_time = kst_time - timedelta(hours=9)

            terms[term_chinese] = utc_time
        except (ValueError, IndexError):
            continue

    conn.close()
    return terms


def compare_year(year: int) -> dict:
    """Compare all three sources for a given year."""
    sl_terms = load_sky_lizard_terms(year)
    kfa_terms = load_kfa_terms(year)
    manse_terms = load_manseoryeok_terms(year)

    # Get all unique term names
    all_terms = set(sl_terms.keys()) | set(kfa_terms.keys()) | set(manse_terms.keys())

    results = {"year": year, "terms": {}, "discrepancies": []}

    for term in sorted(all_terms):
        sl_time = sl_terms.get(term)
        kfa_time = kfa_terms.get(term)
        manse_time = manse_terms.get(term)

        results["terms"][term] = {
            "sky_lizard": sl_time.isoformat() if sl_time else None,
            "kfa": kfa_time.isoformat() if kfa_time else None,
            "manseoryeok": manse_time.isoformat() if manse_time else None,
        }

        # Check for discrepancies
        times = [t for t in [sl_time, kfa_time, manse_time] if t is not None]
        if len(times) < 2:
            continue

        # Calculate max difference in minutes
        max_diff = max((t1 - t2).total_seconds() / 60 for t1 in times for t2 in times)

        if max_diff > 5:  # More than 5 minutes difference
            results["discrepancies"].append(
                {
                    "term": term,
                    "max_diff_minutes": max_diff,
                    "sky_lizard": sl_time.isoformat() if sl_time else "N/A",
                    "kfa": kfa_time.isoformat() if kfa_time else "N/A",
                    "manseoryeok": manse_time.isoformat() if manse_time else "N/A",
                }
            )

    return results


def main():
    """Compare solar terms across sources for sample years."""
    test_years = [1950, 1970, 1990, 2000, 2010, 2020]

    print("=" * 80)
    print("SOLAR TERMS COMPARISON: SKY_LIZARD vs KFA vs Manseoryeok")
    print("=" * 80)

    for year in test_years:
        print(f"\n{'=' * 80}")
        print(f"Year: {year}")
        print("=" * 80)

        results = compare_year(year)

        # Print summary
        sl_count = sum(1 for t in results["terms"].values() if t["sky_lizard"])
        kfa_count = sum(1 for t in results["terms"].values() if t["kfa"])
        manse_count = sum(1 for t in results["terms"].values() if t["manseoryeok"])

        print(f"\nTerm counts:")
        print(f"  SKY_LIZARD:  {sl_count} terms")
        print(f"  KFA:         {kfa_count} terms")
        print(f"  Manseoryeok: {manse_count} terms")

        if results["discrepancies"]:
            print(f"\n⚠️  Found {len(results['discrepancies'])} discrepancies (>5 min difference):")
            print()

            for disc in results["discrepancies"]:
                print(f"  {disc['term']}:")
                print(f"    Max difference: {disc['max_diff_minutes']:.1f} minutes")
                print(f"    SKY_LIZARD:  {disc['sky_lizard']}")
                print(f"    KFA:         {disc['kfa']}")
                print(f"    Manseoryeok: {disc['manseoryeok']}")
                print()
        else:
            print("\n✅ All sources agree within 5 minutes!")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print(
        """
Based on the comparison:

1. SKY_LIZARD (1930-2020):
   - Authentic production app data
   - 12 major terms per year
   - Should be PRIMARY source for 1930-2020

2. KFA/Wonkwang (1900-2050):
   - Academic quality (Wonkwang University)
   - 12 major terms per year
   - Use for years OUTSIDE SKY_LIZARD range (pre-1930, post-2020)

3. Manseoryeok (1930-2065+):
   - Good for validation/cross-checking
   - May have different precision/rounding
   - Use as TERTIARY reference only

SUGGESTED STRATEGY:
- 1930-2020: Use SKY_LIZARD as canonical
- Pre-1930, 2021-2050: Use KFA
- Always validate critical dates against multiple sources
"""
    )


if __name__ == "__main__":
    main()
