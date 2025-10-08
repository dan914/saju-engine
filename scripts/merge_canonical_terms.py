"""Merge SKY_LIZARD and KFA solar terms into runtime data/terms_*.csv files."""

import csv
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKY_LIZARD_DIR = REPO_ROOT / "data" / "canonical" / "terms"
KFA_DIR = REPO_ROOT / "data" / "canonical" / "terms_kfa"
RUNTIME_DATA_DIR = REPO_ROOT / "data"

# Year ranges for each source
SKY_LIZARD_RANGE = (1930, 2020)
KFA_RANGE_PRE = (1900, 1929)
KFA_RANGE_POST = (2021, 2050)


def merge_terms():
    """Merge canonical terms into runtime data directory."""

    print("=" * 80)
    print("MERGING CANONICAL SOLAR TERMS INTO RUNTIME DATA")
    print("=" * 80)

    # Strategy:
    # - 1930-2020: Use SKY_LIZARD (primary source, production app data)
    # - Pre-1930, 2021-2050: Use KFA (only source available, academic quality)

    stats = {
        'sky_lizard': 0,
        'kfa': 0,
        'skipped': 0,
        'errors': []
    }

    # Copy SKY_LIZARD data (1930-2020)
    print(f"\n1. Copying SKY_LIZARD terms ({SKY_LIZARD_RANGE[0]}-{SKY_LIZARD_RANGE[1]})...")
    for year in range(SKY_LIZARD_RANGE[0], SKY_LIZARD_RANGE[1] + 1):
        src = SKY_LIZARD_DIR / f"terms_{year}.csv"
        dst = RUNTIME_DATA_DIR / f"terms_{year}.csv"

        if src.exists():
            try:
                shutil.copy2(src, dst)
                stats['sky_lizard'] += 1
                if year % 10 == 0:
                    print(f"   Copied {year}")
            except Exception as e:
                stats['errors'].append(f"Error copying {year}: {e}")
        else:
            stats['skipped'] += 1
            stats['errors'].append(f"SKY_LIZARD missing year {year}")

    print(f"   ✓ Copied {stats['sky_lizard']} years from SKY_LIZARD")

    # Copy KFA data (pre-1930)
    print(f"\n2. Copying KFA terms (pre-{SKY_LIZARD_RANGE[0]})...")
    for year in range(KFA_RANGE_PRE[0], KFA_RANGE_PRE[1] + 1):
        src = KFA_DIR / f"terms_{year}.csv"
        dst = RUNTIME_DATA_DIR / f"terms_{year}.csv"

        if src.exists():
            try:
                shutil.copy2(src, dst)
                stats['kfa'] += 1
                if year % 10 == 0:
                    print(f"   Copied {year}")
            except Exception as e:
                stats['errors'].append(f"Error copying {year}: {e}")
        else:
            stats['skipped'] += 1

    print(f"   ✓ Copied {stats['kfa']} years from KFA (pre-1930)")

    # Copy KFA data (post-2020)
    print(f"\n3. Copying KFA terms (post-{SKY_LIZARD_RANGE[1]})...")
    kfa_post_count = 0
    for year in range(KFA_RANGE_POST[0], KFA_RANGE_POST[1] + 1):
        src = KFA_DIR / f"terms_{year}.csv"
        dst = RUNTIME_DATA_DIR / f"terms_{year}.csv"

        if src.exists():
            try:
                shutil.copy2(src, dst)
                kfa_post_count += 1
                if year % 10 == 0:
                    print(f"   Copied {year}")
            except Exception as e:
                stats['errors'].append(f"Error copying {year}: {e}")
        else:
            stats['skipped'] += 1

    stats['kfa'] += kfa_post_count
    print(f"   ✓ Copied {kfa_post_count} years from KFA (post-2020)")

    # Summary
    print("\n" + "=" * 80)
    print("MERGE COMPLETE")
    print("=" * 80)
    print(f"Total files copied: {stats['sky_lizard'] + stats['kfa']}")
    print(f"  - SKY_LIZARD (1930-2020): {stats['sky_lizard']}")
    print(f"  - KFA (1900-1929, 2021-2050): {stats['kfa']}")
    print(f"Skipped/Missing: {stats['skipped']}")

    if stats['errors']:
        print(f"\n⚠️  Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

    # Verify coverage
    print("\n" + "=" * 80)
    print("COVERAGE VERIFICATION")
    print("=" * 80)

    runtime_years = sorted([
        int(f.stem.split('_')[1])
        for f in RUNTIME_DATA_DIR.glob("terms_*.csv")
        if f.stem.startswith('terms_')
    ])

    if runtime_years:
        print(f"Runtime data coverage: {min(runtime_years)}-{max(runtime_years)}")
        print(f"Total years: {len(runtime_years)}")

        # Check for gaps
        gaps = []
        for i in range(len(runtime_years) - 1):
            if runtime_years[i+1] - runtime_years[i] > 1:
                gaps.append((runtime_years[i], runtime_years[i+1]))

        if gaps:
            print(f"\n⚠️  Found {len(gaps)} gaps in coverage:")
            for start, end in gaps:
                print(f"  - Gap between {start} and {end}")
        else:
            print("\n✅ No gaps in coverage!")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Verify the merged data loads correctly in the pillars service
2. Run canonical comparison tests (compare_canonical.py)
3. Check for any month pillar calculation discrepancies
4. Update documentation with data source information
5. Consider adding a metadata field to track which source was used per year
    """)


if __name__ == "__main__":
    merge_terms()
