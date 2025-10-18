#!/usr/bin/env python3
"""
Full orchestrator test for 2000-09-14 10:00 AM Seoul, Male
Tests ALL engines with real data - NO stubs or hardcoded values
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "services" / "analysis-service"))
sys.path.insert(0, str(Path(__file__).parent / "services" / "common"))

print("=" * 80)
print("FULL ORCHESTRATOR TEST - 2000-09-14 10:00 AM Seoul (Male)")
print("=" * 80)
print()

# Step 1: Calculate pillars using real calculation
print("STEP 1: Calculate Four Pillars")
print("-" * 80)

try:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from scripts.calculate_pillars_traditional import calculate_four_pillars

    birth_dt = datetime(2000, 9, 14, 10, 0, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    pillars_result = calculate_four_pillars(
        birth_dt=birth_dt,
        tz_str="Asia/Seoul",
        mode="traditional_kr",
        zi_hour_mode="default",
        use_refined=True,
        return_metadata=True
    )

    print(f"Year:  {pillars_result['year']}")
    print(f"Month: {pillars_result['month']}")
    print(f"Day:   {pillars_result['day']}")
    print(f"Hour:  {pillars_result['hour']}")
    print(f"Metadata: {pillars_result.get('metadata', {})}")
    print("✅ Pillars calculated successfully")
    print()

except Exception as e:
    print(f"❌ ERROR in pillar calculation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Run orchestrator
print("STEP 2: Run Full Orchestrator")
print("-" * 80)

try:
    from app.core.saju_orchestrator import SajuOrchestrator

    orchestrator = SajuOrchestrator()
    print("✅ Orchestrator initialized")
    print()

    # Prepare input
    pillars_input = {
        "year": pillars_result["year"],
        "month": pillars_result["month"],
        "day": pillars_result["day"],
        "hour": pillars_result["hour"]
    }

    birth_context = {
        "birth_dt": "2000-09-14T10:00:00+09:00",
        "gender": "male",
        "timezone": "Asia/Seoul"
    }

    print("Input:")
    print(f"  Pillars: {pillars_input}")
    print(f"  Context: {birth_context}")
    print()

    # Run analysis
    print("Running analysis...")
    result = orchestrator.analyze(pillars_input, birth_context)
    print("✅ Analysis completed")
    print()

except Exception as e:
    print(f"❌ ERROR in orchestrator: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Display all engine results
print("=" * 80)
print("ALL ENGINE RESULTS")
print("=" * 80)
print()

engines = [
    "season",
    "strength",
    "relations",
    "relations_weighted",
    "relations_extras",
    "climate",
    "elements_distribution_raw",
    "elements_distribution_transformed",
    "combination_trace",
    "yongshin",
    "luck",
    "shensha",
    "void",
    "yuanjin",
    "ten_gods",
    "twelve_stages",
    "stage3"
]

for engine_name in engines:
    if engine_name in result:
        print(f"[{engine_name.upper()}]")
        print("-" * 80)

        engine_result = result[engine_name]

        # Pretty print based on type
        if isinstance(engine_result, dict):
            # Show key structure
            print(f"Type: dict with {len(engine_result)} keys")
            print(f"Keys: {list(engine_result.keys())}")

            # Show sample values for important keys
            if engine_name == "strength":
                print(f"  score: {engine_result.get('score', 'N/A')}")
                print(f"  grade_code: {engine_result.get('grade_code', 'N/A')}")
                print(f"  bin: {engine_result.get('bin', 'N/A')}")

            elif engine_name == "luck":
                print(f"  policy_version: {engine_result.get('policy_version', 'N/A')}")
                print(f"  direction: {engine_result.get('direction', 'N/A')}")
                print(f"  start_age: {engine_result.get('start_age', 'N/A')}")
                print(f"  pillars_count: {len(engine_result.get('pillars', []))}")
                if engine_result.get('pillars'):
                    print(f"  first_pillar: {engine_result['pillars'][0]}")
                print(f"  current_luck: {engine_result.get('current_luck', 'N/A')}")

            elif engine_name == "ten_gods":
                by_pillar = engine_result.get('by_pillar', {})
                summary = engine_result.get('summary', {})
                print(f"  by_pillar keys: {list(by_pillar.keys())}")
                print(f"  summary: {summary}")
                print(f"  dominant: {engine_result.get('dominant', 'N/A')}")
                print(f"  missing: {engine_result.get('missing', 'N/A')}")

            elif engine_name == "twelve_stages":
                by_pillar = engine_result.get('by_pillar', {})
                print(f"  by_pillar keys: {list(by_pillar.keys())}")
                print(f"  dominant: {engine_result.get('dominant', 'N/A')}")
                print(f"  weakest: {engine_result.get('weakest', 'N/A')}")

            elif engine_name == "stage3":
                for stage3_engine in ['luck_flow', 'gyeokguk', 'climate_advice', 'pattern']:
                    if stage3_engine in engine_result:
                        stage3_data = engine_result[stage3_engine]
                        print(f"  {stage3_engine}: {type(stage3_data).__name__} with {len(stage3_data) if isinstance(stage3_data, (dict, list)) else 'N/A'} items")

            else:
                # Just show structure
                for key, value in list(engine_result.items())[:3]:
                    if isinstance(value, (str, int, float, bool)):
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {type(value).__name__}")

        elif isinstance(engine_result, (list, str, int, float)):
            print(f"Value: {engine_result}")

        print()
    else:
        print(f"[{engine_name.upper()}]")
        print("-" * 80)
        print("❌ MISSING from result")
        print()

# Step 4: Check for any errors or placeholders
print("=" * 80)
print("VALIDATION")
print("=" * 80)
print()

def check_for_stubs(obj, path="root"):
    """Recursively check for stub/placeholder values"""
    issues = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"

            # Check for common stub patterns
            if isinstance(value, str):
                if value in ["STUB", "TODO", "PLACEHOLDER", "NOT_IMPLEMENTED"]:
                    issues.append(f"{current_path} = '{value}'")

            # Check for empty critical fields
            if key in ["policy_signature", "direction", "grade_code"] and not value:
                issues.append(f"{current_path} is empty")

            # Recurse
            issues.extend(check_for_stubs(value, current_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            issues.extend(check_for_stubs(item, f"{path}[{i}]"))

    return issues

print("Checking for stubs/placeholders...")
issues = check_for_stubs(result)

if issues:
    print(f"❌ Found {len(issues)} issues:")
    for issue in issues[:10]:  # Show first 10
        print(f"  - {issue}")
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")
else:
    print("✅ No stubs or placeholders found")

print()

# Step 5: Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print(f"Total engines: {len(engines)}")
print(f"Engines present: {sum(1 for e in engines if e in result)}")
print(f"Engines missing: {sum(1 for e in engines if e not in result)}")
print()

print("Critical outputs:")
print(f"  ✅ Pillars: {pillars_input}")
print(f"  ✅ Strength: {result.get('strength', {}).get('grade_code', 'MISSING')}")
print(f"  ✅ Luck direction: {result.get('luck', {}).get('direction', 'MISSING')}")
print(f"  ✅ Luck pillars count: {len(result.get('luck', {}).get('pillars', []))}")
print(f"  ✅ Ten Gods dominant: {result.get('ten_gods', {}).get('dominant', 'MISSING')}")
print(f"  ✅ Stage-3 engines: {list(result.get('stage3', {}).keys())}")
print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Save full result to file
output_file = Path(__file__).parent / "test_result_2000_09_14_full.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Full result saved to: {output_file}")
