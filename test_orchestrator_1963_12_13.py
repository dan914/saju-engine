#!/usr/bin/env python3
"""
Orchestrator test for 1963-12-13 8:30 PM Seoul, Male
Shows core results only
"""
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "services" / "analysis-service"))
sys.path.insert(0, str(Path(__file__).parent / "services" / "common"))

print("=" * 80)
print("SAJU ANALYSIS: 1963-12-13 8:30 PM Seoul (Male)")
print("=" * 80)
print()

# Step 1: Calculate pillars
from scripts.calculate_pillars_traditional import calculate_four_pillars

birth_dt = datetime(1963, 12, 13, 20, 30, 0, tzinfo=ZoneInfo("Asia/Seoul"))
pillars_result = calculate_four_pillars(
    birth_dt=birth_dt,
    tz_str="Asia/Seoul",
    mode="traditional_kr",
    zi_hour_mode="default",
    use_refined=True,
    return_metadata=True
)

print("四柱 (Four Pillars):")
print(f"  年柱: {pillars_result['year']}")
print(f"  月柱: {pillars_result['month']}")
print(f"  日柱: {pillars_result['day']}")
print(f"  時柱: {pillars_result['hour']}")
print()

# Step 2: Run orchestrator
from app.core.saju_orchestrator import SajuOrchestrator

orchestrator = SajuOrchestrator()

pillars_input = {
    "year": pillars_result["year"],
    "month": pillars_result["month"],
    "day": pillars_result["day"],
    "hour": pillars_result["hour"]
}

birth_context = {
    "birth_dt": "1963-12-13T20:30:00+09:00",
    "gender": "male",
    "timezone": "Asia/Seoul"
}

result = orchestrator.analyze(pillars_input, birth_context)

# Step 3: Display core results
print("=" * 80)
print("CORE ANALYSIS RESULTS")
print("=" * 80)
print()

# Strength
strength = result.get('strength', {})
print("強弱 (Strength):")
print(f"  等級: {strength.get('grade_code', 'N/A')}")
print(f"  分數: {strength.get('score', 'N/A')}")
print(f"  階段: {strength.get('phase', 'N/A')}")
print()

# Ten Gods
ten_gods = result.get('ten_gods', {})
print("十神 (Ten Gods):")
print(f"  Summary: {ten_gods.get('summary', {})}")
print(f"  Dominant: {ten_gods.get('dominant', 'N/A')}")
print(f"  Missing: {ten_gods.get('missing', 'N/A')}")
print()

# Twelve Stages
twelve_stages = result.get('twelve_stages', {})
by_pillar = twelve_stages.get('by_pillar', {})
print("十二運星 (Twelve Stages):")
for pos in ['year', 'month', 'day', 'hour']:
    stage = by_pillar.get(pos, {})
    stage_zh = stage.get('stage_zh', 'N/A')
    stage_ko = stage.get('stage_ko', 'N/A')
    print(f"  {pos}: {stage_zh} ({stage_ko})")
print()

# Yongshin
yongshin = result.get('yongshin', {})
integrated = yongshin.get('integrated', {})
primary = integrated.get('primary', {})
secondary = integrated.get('secondary', {})
print("用神 (Yongshin):")
print(f"  Primary: {primary.get('elem_ko', 'N/A')} ({primary.get('role', 'N/A')})")
if secondary.get('elem_ko'):
    print(f"  Secondary: {secondary.get('elem_ko', 'N/A')} ({secondary.get('role', 'N/A')})")
print()

# Luck Pillars
luck = result.get('luck', {})
print("大運 (Luck Pillars):")
print(f"  Direction: {luck.get('direction', 'N/A')}")
print(f"  Start Age: {luck.get('start_age', 'N/A')} years")
pillars = luck.get('pillars', [])
if pillars:
    print("  First 5 Decades:")
    for p in pillars[:5]:
        print(f"    Decade {p['decade']}: {p['pillar']} (age {p['start_age']}-{p['end_age']})")
current = luck.get('current_luck')
if current:
    print(f"  Current: Decade {current['decade']} ({current['pillar']}), {current['years_into_decade']:.1f} years in")
print()

# Relations
relations = result.get('relations', {})
print("關係 (Relations):")
print(f"  Priority: {relations.get('priority_hit', 'None')}")
notes = relations.get('notes', [])
if notes:
    print(f"  Notes: {', '.join(notes[:5])}")
print()

# Stage-3
stage3 = result.get('stage3', {})
print("Stage-3 Engines:")

gyeokguk = stage3.get('gyeokguk', {})
if gyeokguk:
    print(f"  格局 (Gyeokguk): {gyeokguk.get('classification', 'N/A')}")

luck_flow = stage3.get('luck_flow', {})
if luck_flow:
    print(f"  運勢流向 (Luck Flow): {luck_flow.get('trend', 'N/A')}")

climate_advice = stage3.get('climate_advice', {})
if climate_advice:
    print(f"  調候建議 (Climate): {climate_advice.get('primary_advice', 'N/A')}")

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
