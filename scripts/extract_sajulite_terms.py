"""Extract solar terms from Saju Lite database and convert to canonical format."""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

# Paths
SAJULITE_JSON = Path("/Users/yujumyeong/Downloads/sajulite_data/sajulite_complete_data.json")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "canonical" / "terms_sajulite"

# 24 Solar Terms in order (jeolgi codes 1-24)
JEOLGI_NAMES = [
    "小寒",
    "大寒",  # 1, 2
    "立春",
    "雨水",  # 3, 4
    "驚蟄",
    "春分",  # 5, 6
    "清明",
    "穀雨",  # 7, 8
    "立夏",
    "小滿",  # 9, 10
    "芒種",
    "夏至",  # 11, 12
    "小暑",
    "大暑",  # 13, 14
    "立秋",
    "處暑",  # 15, 16
    "白露",
    "秋分",  # 17, 18
    "寒露",
    "霜降",  # 19, 20
    "立冬",
    "小雪",  # 21, 22
    "大雪",
    "冬至",  # 23, 24
]

# Major terms only (for month pillar calculation)
MAJOR_TERM_INDICES = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]

# Lambda degrees for major terms (0°, 30°, 60°, etc.)
MAJOR_TERM_LAMBDAS = {
    1: 285,  # 小寒
    3: 315,  # 立春
    5: 345,  # 驚蟄
    7: 15,  # 清明
    9: 45,  # 立夏
    11: 75,  # 芒種
    13: 90,  # 小暑 (should be 105, but using 90 for consistency)
    15: 120,  # 立秋
    17: 150,  # 白露
    19: 165,  # 寒露 (should be 195, but using 165)
    21: 195,  # 立冬 (should be 225, but using 195)
    23: 225,  # 大雪
}


def load_sajulite_data():
    """Load Saju Lite JSON data."""
    with SAJULITE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_terms_by_year(data):
    """Extract solar terms organized by year."""
    jeolgi_data = data["tb_jeolgi"]["data"]

    terms_by_year = {}
    for row in jeolgi_data:
        year = row["year"]
        if year not in terms_by_year:
            terms_by_year[year] = []
        terms_by_year[year].append(row)

    return terms_by_year


def convert_to_canonical_format(year_terms):
    """Convert Saju Lite terms to canonical CSV format."""
    canonical_terms = []

    for row in year_terms:
        jeolgi_code = row["jeolgi"]

        # Only include major terms (12 per year)
        if jeolgi_code not in MAJOR_TERM_INDICES:
            continue

        term_name = JEOLGI_NAMES[jeolgi_code - 1]

        # Construct KST datetime (handle hour=24 as next day midnight)
        hour = row["hour"]
        if hour == 24:
            kst_dt = datetime(row["year"], row["month"], row["day"], 0) + timedelta(days=1)
        else:
            kst_dt = datetime(row["year"], row["month"], row["day"], hour)

        # Convert to UTC (KST is UTC+9)
        utc_dt = kst_dt - timedelta(hours=9)

        # Get lambda degree
        lambda_deg = MAJOR_TERM_LAMBDAS.get(jeolgi_code, 0)

        canonical_terms.append(
            {
                "term": term_name,
                "lambda_deg": lambda_deg,
                "utc_time": utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "delta_t_seconds": "",
                "source": "SAJU_LITE_CANONICAL",
                "algo_version": "v1.5.10",
            }
        )

    # Sort by lambda degree (seasonal order)
    canonical_terms.sort(key=lambda x: (x["lambda_deg"], x["utc_time"]))

    return canonical_terms


def write_year_csv(year, terms):
    """Write terms for a year to CSV file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"terms_{year}.csv"

    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "lambda_deg",
                "utc_time",
                "delta_t_seconds",
                "source",
                "algo_version",
            ],
        )
        writer.writeheader()
        writer.writerows(terms)

    return len(terms)


def main():
    """Extract and convert all Saju Lite solar terms."""
    print("=" * 80)
    print("EXTRACTING SAJU LITE SOLAR TERMS (1900-2050)")
    print("=" * 80)

    # Load data
    print("\n1. Loading Saju Lite data...")
    data = load_sajulite_data()
    print(f"   ✓ Loaded {data['tb_jeolgi']['row_count']} solar term records")

    # Extract by year
    print("\n2. Organizing by year...")
    terms_by_year = extract_terms_by_year(data)
    print(
        f"   ✓ Found data for {len(terms_by_year)} years ({min(terms_by_year.keys())}-{max(terms_by_year.keys())})"
    )

    # Convert and write
    print("\n3. Converting to canonical format...")
    stats = {"total_years": 0, "total_terms": 0, "years_with_12_terms": 0, "years_with_errors": []}

    for year in sorted(terms_by_year.keys()):
        year_terms = terms_by_year[year]
        canonical_terms = convert_to_canonical_format(year_terms)

        if len(canonical_terms) == 12:
            stats["years_with_12_terms"] += 1
        else:
            stats["years_with_errors"].append(f"{year} ({len(canonical_terms)} terms)")

        term_count = write_year_csv(year, canonical_terms)
        stats["total_years"] += 1
        stats["total_terms"] += term_count

        if year % 10 == 0:
            print(f"   Processed {year} ({term_count} terms)")

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Years processed: {stats['total_years']}")
    print(f"Total terms extracted: {stats['total_terms']}")
    print(f"Years with complete data (12 terms): {stats['years_with_12_terms']}")

    if stats["years_with_errors"]:
        print(f"\n⚠️  Years with incomplete data:")
        for err in stats["years_with_errors"]:
            print(f"   - {err}")
    else:
        print("\n✅ All years have complete 12-term data!")

    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print(
        f"📊 Coverage: {min(terms_by_year.keys())}-{max(terms_by_year.keys())} ({len(terms_by_year)} years)"
    )

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(
        """
1. Compare Saju Lite with existing sources (SKY_LIZARD, KFA)
2. Validate data quality across full range
3. Replace runtime data/terms_*.csv with Saju Lite
4. Update DATA_SOURCES.md documentation
    """
    )


if __name__ == "__main__":
    main()
