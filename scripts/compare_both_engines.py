#!/usr/bin/env python3
"""
Compare both pillar calculation engines for 2000-09-14 10:00 AM Seoul

Engine 1: calculate_four_pillars() - Active engine with LMT/DST/子時 support
Engine 2: PillarsCalculator + CanonicalCalendar - Orphaned engine with CSV lookup
"""

import sys
from datetime import datetime
from pathlib import Path

# Setup paths
repo_root = Path(__file__).resolve().parents[1]
scripts_path = str(repo_root / "scripts")
pillars_service_path = str(repo_root / "services" / "pillars-service")

# Add to path
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
if pillars_service_path not in sys.path:
    sys.path.insert(0, pillars_service_path)

print("=" * 80)
print("🔍 COMPARING TWO PILLAR ENGINES")
print("Birth: 2000-09-14 10:00 AM Seoul")
print("=" * 80)
print()

# ============================================================================
# ENGINE 1: calculate_four_pillars() - ACTIVE ENGINE
# ============================================================================
print("ENGINE 1: calculate_four_pillars() - ACTIVE ENGINE")
print("-" * 80)
print("Features:")
print("  ✓ LMT (Local Mean Time) adjustment by city")
print("  ✓ DST handling (1948-1960, 1987-1988)")
print("  ✓ 子時 (Zi Hour) day transition rule")
print("  ✓ Multiple city support (Seoul, Busan, Tokyo, Shanghai)")
print("  ✓ Refined Saju Lite solar terms with ΔT corrections")
print()

from calculate_pillars_traditional import calculate_four_pillars

birth_dt = datetime(2000, 9, 14, 10, 0, 0)
timezone = "Asia/Seoul"

result1 = calculate_four_pillars(
    birth_dt=birth_dt,
    tz_str=timezone,
    mode="traditional_kr",
    zi_hour_mode="traditional",
    use_refined=True,
    return_metadata=True,
)

print("Results:")
print(f"  년주 (Year):  {result1['year']}")
print(f"  월주 (Month): {result1['month']}")
print(f"  일주 (Day):   {result1['day']}")
print(f"  시주 (Hour):  {result1['hour']}")
print()

if "metadata" in result1:
    meta = result1["metadata"]
    print("Metadata:")
    print(f"  LMT offset: {meta.get('lmt_offset', 0)} minutes")
    print(f"  DST applied: {meta.get('dst_applied', False)}")
    print(f"  子時 transition: {meta.get('zi_transition', False)}")
    print(f"  子時 mode: {meta.get('zi_hour_mode', 'N/A')}")
    print(f"  Day for pillar: {meta.get('day_for_pillar', 'N/A')}")
    print()

# ============================================================================
# ENGINE 2: PillarsCalculator + CanonicalCalendar - ORPHANED ENGINE
# ============================================================================
print("=" * 80)
print("ENGINE 2: PillarsCalculator + CanonicalCalendar - ORPHANED ENGINE")
print("-" * 80)
print("Features:")
print("  ✓ CSV lookup from precomputed canonical data")
print("  ✓ Falls back to calculation if not in CSV")
print("  ✗ NO LMT adjustment by city (uses basic calculation)")
print("  ✗ NO DST handling")
print("  ✗ Basic 子時 rule (not city-specific)")
print()

try:
    from app.core.pillars import default_calculator

    calculator = default_calculator()

    result2 = calculator.compute(local_dt=birth_dt, timezone=timezone)

    print("Results:")
    print(f"  년주 (Year):  {result2['year']}")
    print(f"  월주 (Month): {result2['month']}")
    print(f"  일주 (Day):   {result2['day']}")
    print(f"  시주 (Hour):  {result2['hour']}")
    print()

    if result2.get("month_term"):
        print("Metadata:")
        print(f"  Month term: {result2['month_term']}")
        print(f"  Day start: {result2.get('day_start', 'N/A')}")
        print(f"  Hour branch: {result2.get('hour_branch', 'N/A')}")
        print(f"  Hour range: {result2.get('hour_range', 'N/A')}")
        print()

except Exception as e:
    print(f"❌ ERROR running Engine 2: {e}")
    print(f"   This engine is orphaned and may have dependency issues.")
    print()
    result2 = None

# ============================================================================
# COMPARISON
# ============================================================================
print("=" * 80)
print("📊 COMPARISON")
print("-" * 80)

if result2:
    print(f"{'Pillar':<12} {'Engine 1 (Active)':<20} {'Engine 2 (Orphaned)':<20} {'Match?':<10}")
    print("-" * 80)

    year_match = "✓" if result1["year"] == result2["year"] else "✗"
    month_match = "✓" if result1["month"] == result2["month"] else "✗"
    day_match = "✓" if result1["day"] == result2["day"] else "✗"
    hour_match = "✓" if result1["hour"] == result2["hour"] else "✗"

    print(f"{'년주 (Year)':<12} {result1['year']:<20} {result2['year']:<20} {year_match:<10}")
    print(f"{'월주 (Month)':<12} {result1['month']:<20} {result2['month']:<20} {month_match:<10}")
    print(f"{'일주 (Day)':<12} {result1['day']:<20} {result2['day']:<20} {day_match:<10}")
    print(f"{'시주 (Hour)':<12} {result1['hour']:<20} {result2['hour']:<20} {hour_match:<10}")
    print()

    all_match = year_match == "✓" and month_match == "✓" and day_match == "✓" and hour_match == "✓"

    if all_match:
        print("✅ Both engines produce IDENTICAL results!")
    else:
        print("⚠️  Engines produce DIFFERENT results!")
        print()
        print("Likely reasons for difference:")
        print("  - Engine 1 applies LMT adjustment (-32 min for Seoul)")
        print("  - Engine 1 applies DST corrections (if applicable)")
        print("  - Engine 1 uses refined solar terms with ΔT corrections")
        print("  - Engine 2 uses basic calculation or CSV lookup")
else:
    print("Engine 2 failed to run (orphaned code with missing dependencies)")

print()
print("=" * 80)
print("🏆 RECOMMENDED ENGINE: Engine 1 (calculate_four_pillars)")
print("-" * 80)
print("Reasons:")
print("  ✓ Actively maintained and tested")
print("  ✓ Supports multiple cities with proper LMT adjustment")
print("  ✓ Handles DST correctly for Korean historical periods")
print("  ✓ Implements traditional 子時 day transition rule")
print("  ✓ Uses refined astronomical data from Saju Lite")
print("  ✓ Used by current API endpoints")
print()
print("Engine 2 is ORPHANED - complete but never integrated into production.")
print("=" * 80)
