"""Detailed comparison of SKY_LIZARD vs KFA solar terms."""

import csv
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKY_LIZARD_DIR = REPO_ROOT / "data" / "canonical" / "terms"
KFA_DIR = REPO_ROOT / "data" / "canonical" / "terms_kfa"


def parse_utc_time(utc_str: str) -> datetime:
    """Parse UTC timestamp from CSV."""
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    return dt.replace(tzinfo=None)


def compare_year(year: int) -> dict:
    """Compare SKY_LIZARD vs KFA for a given year."""
    sl_path = SKY_LIZARD_DIR / f"terms_{year}.csv"
    kfa_path = KFA_DIR / f"terms_{year}.csv"

    if not sl_path.exists() or not kfa_path.exists():
        return None

    sl_terms = {}
    kfa_terms = {}

    with sl_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sl_terms[row['term']] = parse_utc_time(row['utc_time'])

    with kfa_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kfa_terms[row['term']] = parse_utc_time(row['utc_time'])

    discrepancies = []
    for term in sorted(set(sl_terms.keys()) & set(kfa_terms.keys())):
        sl_time = sl_terms[term]
        kfa_time = kfa_terms[term]
        diff_seconds = abs((sl_time - kfa_time).total_seconds())
        diff_minutes = diff_seconds / 60

        if diff_minutes > 1:  # More than 1 minute difference
            discrepancies.append({
                'year': year,
                'term': term,
                'diff_minutes': diff_minutes,
                'sky_lizard': sl_time,
                'kfa': kfa_time
            })

    return {
        'year': year,
        'sl_count': len(sl_terms),
        'kfa_count': len(kfa_terms),
        'discrepancies': discrepancies
    }


def main():
    """Compare SKY_LIZARD vs KFA for overlapping years (1930-2020)."""
    print("=" * 100)
    print("DETAILED COMPARISON: SKY_LIZARD vs KFA/Wonkwang (1930-2020)")
    print("=" * 100)

    all_discrepancies = []
    total_comparisons = 0
    years_with_discrepancies = 0

    for year in range(1930, 2021):
        result = compare_year(year)
        if not result:
            continue

        total_comparisons += result['sl_count']

        if result['discrepancies']:
            years_with_discrepancies += 1
            all_discrepancies.extend(result['discrepancies'])

            print(f"\n{year}: {len(result['discrepancies'])} discrepancies")
            for disc in result['discrepancies']:
                print(f"  {disc['term']:4s}: {disc['diff_minutes']:6.1f} min"
                      f"  | SL: {disc['sky_lizard']}"
                      f"  | KFA: {disc['kfa']}")

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Years compared: 1930-2020 (91 years)")
    print(f"Total term comparisons: {total_comparisons}")
    print(f"Years with discrepancies (>1 min): {years_with_discrepancies}")
    print(f"Total discrepancies: {len(all_discrepancies)}")

    if all_discrepancies:
        avg_diff = sum(d['diff_minutes'] for d in all_discrepancies) / len(all_discrepancies)
        max_diff = max(all_discrepancies, key=lambda x: x['diff_minutes'])

        print(f"\nAverage difference: {avg_diff:.2f} minutes")
        print(f"Maximum difference: {max_diff['diff_minutes']:.1f} minutes")
        print(f"  {max_diff['year']} {max_diff['term']}: SL={max_diff['sky_lizard']}, KFA={max_diff['kfa']}")

        # Categorize by difference magnitude
        small = sum(1 for d in all_discrepancies if d['diff_minutes'] < 5)
        medium = sum(1 for d in all_discrepancies if 5 <= d['diff_minutes'] < 15)
        large = sum(1 for d in all_discrepancies if d['diff_minutes'] >= 15)

        print(f"\nDiscrepancy breakdown:")
        print(f"  < 5 minutes: {small}")
        print(f"  5-15 minutes: {medium}")
        print(f"  >= 15 minutes: {large}")

    print("\n" + "=" * 100)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 100)
    print("""
1. **Data Quality Assessment:**
   - Both sources appear to use similar algorithms
   - Small differences (1-15 min) likely due to:
     * Different ΔT (delta-T) values
     * Rounding differences in astronomical calculations
     * Different precision in ephemeris data

2. **Recommended Source Priority:**
   - **1930-2020**: Use SKY_LIZARD as PRIMARY
     Reason: Extracted from production app with real user base

   - **Pre-1930, 2021-2050**: Use KFA/Wonkwang
     Reason: Only source available, academic quality from Wonkwang University

3. **Validation Strategy:**
   - For critical dates near solar term boundaries:
     * Check both sources
     * Consider ±1 hour buffer zone for month pillar calculations
     * Document which source was used in trace log

4. **Next Steps:**
   - Merge SKY_LIZARD (1930-2020) + KFA (other years) into runtime data/
   - Add source attribution to each terms_*.csv file
   - Run regression tests with canonical pillar data
""")


if __name__ == "__main__":
    main()
