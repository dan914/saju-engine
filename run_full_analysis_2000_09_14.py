#!/usr/bin/env python3
"""
Comprehensive test for 2000-09-14, 10:00 AM Seoul, Male
Run all engines and report hardcoded values, stubs, and errors
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent

# Use Poetry-based imports via script loader
from scripts._script_loader import get_analysis_module

# Load required classes/functions from services
SajuOrchestrator = get_analysis_module("saju_orchestrator", "SajuOrchestrator")

from scripts.calculate_pillars_traditional import calculate_four_pillars


def check_for_issues(data, path="root"):
    """Recursively check for hardcoded values, stubs, errors"""
    issues = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}"

            # Check for stub/placeholder indicators
            if key in ["stub", "placeholder", "todo", "fixme", "hardcoded"]:
                issues.append(f"⚠️  STUB/PLACEHOLDER at {current_path}: {value}")

            # Check for error indicators
            if key == "error" and value:
                issues.append(f"❌ ERROR at {current_path}: {value}")

            # Check for common stub values
            if value in [0.8, 0.7, 0.75, 0.5] and "confidence" in key.lower():
                issues.append(f"🔍 POSSIBLE HARDCODED CONFIDENCE at {current_path}: {value}")

            if value in [0.0, 1.0] and ("delta_t" in key.lower() or "lmt" in key.lower()):
                issues.append(f"🔍 POSSIBLE HARDCODED TIME ADJUSTMENT at {current_path}: {value}")

            # Check for "unknown" or "null" indicators
            if value in ["unknown", "null", None, "", []]:
                issues.append(f"⚠️  EMPTY/UNKNOWN VALUE at {current_path}: {value}")

            # Recurse
            issues.extend(check_for_issues(value, current_path))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            issues.extend(check_for_issues(item, f"{path}[{i}]"))

    return issues


def main():
    print("=" * 80)
    print("COMPREHENSIVE TEST: 2000-09-14, 10:00 AM Seoul, Male")
    print("=" * 80)
    print()

    # Step 1: Calculate pillars
    print("STEP 1: Calculating Four Pillars...")
    print("-" * 80)

    birth_dt = datetime(2000, 9, 14, 10, 0, 0)
    tz_str = "Asia/Seoul"

    try:
        pillars_result = calculate_four_pillars(
            birth_dt=birth_dt,
            tz_str=tz_str,
            mode="traditional_kr",
            zi_hour_mode="default",
            use_refined=True,
            return_metadata=True,
        )

        print(f"✅ Year:  {pillars_result['year']}")
        print(f"✅ Month: {pillars_result['month']}")
        print(f"✅ Day:   {pillars_result['day']}")
        print(f"✅ Hour:  {pillars_result['hour']}")
        print()

        # Check metadata
        metadata = pillars_result.get("metadata", {})
        print("Metadata:")
        print(f"  LMT offset: {metadata.get('lmt_offset', 'MISSING')} minutes")
        print(f"  DST applied: {metadata.get('dst_applied', 'MISSING')}")
        print(f"  Zi transition: {metadata.get('zi_transition_applied', 'MISSING')}")
        print()

        # Check for issues in pillars
        pillar_issues = check_for_issues(pillars_result, "pillars")
        if pillar_issues:
            print("⚠️  ISSUES FOUND IN PILLARS:")
            for issue in pillar_issues:
                print(f"  {issue}")
            print()

    except Exception as e:
        print(f"❌ PILLAR CALCULATION ERROR: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 2: Run orchestrator
    print("\nSTEP 2: Running Orchestrator (All Engines)...")
    print("-" * 80)

    try:
        orchestrator = SajuOrchestrator()

        pillars_payload = {
            "year": pillars_result["year"],
            "month": pillars_result["month"],
            "day": pillars_result["day"],
            "hour": pillars_result["hour"],
        }
        birth_context = {
            "birth_dt": "2000-09-14T10:00:00+09:00",
            "timezone": "Asia/Seoul",
            "gender": "male",
        }

        request_data = {
            "pillars": {slot: {"pillar": value} for slot, value in pillars_payload.items()},
            "options": {
                **birth_context,
                "calendar": "solar",
            },
        }

        print(f"Request: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        print()

        result = orchestrator.analyze(pillars_payload, birth_context)

        print("✅ Orchestrator completed successfully")
        print()

        # Display key results
        print("KEY RESULTS:")
        print("-" * 80)

        # Strength
        strength = result.get("strength", {})
        print(
            f"Strength: {strength.get('grade_code', 'MISSING')} (score: {strength.get('score', 'MISSING')})"
        )

        # Yongshin
        yongshin = result.get("yongshin", {})
        print(f"Yongshin: {yongshin.get('yongshin', 'MISSING')}")
        print(f"Yongshin Confidence: {yongshin.get('confidence', 'MISSING')}")

        # Gyeokguk
        gyeokguk = result.get("stage3", {}).get("gyeokguk", {})
        print(f"Gyeokguk: {gyeokguk.get('classification', 'MISSING')}")

        # Engine summaries
        summaries = result.get("engine_summaries", {})
        if summaries:
            print("\nEngine Summaries:")
            strength_sum = summaries.get("strength", {})
            print(f"  Strength confidence: {strength_sum.get('confidence', 'MISSING')}")

            yongshin_sum = summaries.get("yongshin_result", {})
            print(f"  Yongshin confidence: {yongshin_sum.get('confidence', 'MISSING')}")

        print()

        # Check for issues
        print("\nCHECKING FOR ISSUES...")
        print("-" * 80)

        all_issues = check_for_issues(result, "result")

        if all_issues:
            print(f"⚠️  FOUND {len(all_issues)} ISSUES:")
            print()

            # Group by type
            errors = [i for i in all_issues if "ERROR" in i]
            stubs = [i for i in all_issues if "STUB" in i or "PLACEHOLDER" in i]
            hardcoded = [i for i in all_issues if "HARDCODED" in i]
            empty = [i for i in all_issues if "EMPTY" in i or "UNKNOWN" in i]

            if errors:
                print(f"\n❌ ERRORS ({len(errors)}):")
                for issue in errors:
                    print(f"  {issue}")

            if stubs:
                print(f"\n⚠️  STUBS/PLACEHOLDERS ({len(stubs)}):")
                for issue in stubs:
                    print(f"  {issue}")

            if hardcoded:
                print(f"\n🔍 POSSIBLE HARDCODED VALUES ({len(hardcoded)}):")
                for issue in hardcoded:
                    print(f"  {issue}")

            if empty:
                print(f"\n⚠️  EMPTY/UNKNOWN VALUES ({len(empty)}):")
                for issue in empty[:10]:  # Limit to first 10
                    print(f"  {issue}")
                if len(empty) > 10:
                    print(f"  ... and {len(empty) - 10} more")
        else:
            print("✅ NO ISSUES FOUND!")

        print()

        # Save full result for inspection
        output_file = Path(__file__).parent / "test_result_2000_09_14.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 Full result saved to: {output_file}")
        print()

    except Exception as e:
        print(f"❌ ORCHESTRATOR ERROR: {e}")
        import traceback

        traceback.print_exc()
        return

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
