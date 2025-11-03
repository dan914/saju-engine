#!/usr/bin/env -S ../scripts/py
"""
Standalone integration test for Luck Pillars engine
Direct import to avoid package init issues

IMPORTANT: This script MUST be run via the venv Python:
  ./scripts/py test_luck_pillars_standalone.py
OR via Makefile target (preferred)
"""
import importlib.util
import json
import sys
from pathlib import Path

# Load luck_pillars module directly
luck_pillars_path = (
    Path(__file__).parent / "services" / "analysis-service" / "app" / "core" / "luck_pillars.py"
)
spec = importlib.util.spec_from_file_location(
    "analysis_service.luck_pillars", luck_pillars_path  # Use namespaced name
)
luck_pillars = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = luck_pillars  # ✅ Register BEFORE exec_module (critical for @dataclass)
spec.loader.exec_module(luck_pillars)

LuckCalculator = luck_pillars.LuckCalculator

# Load policy
policy_path = (
    Path(__file__).parent
    / "saju_codex_batch_all_v2_6_signed"
    / "policies"
    / "luck_pillars_policy.json"
)
with open(policy_path, encoding="utf-8") as f:
    policy = json.load(f)

# Create calculator
calc = LuckCalculator(policy)

# Build pillars (2000-09-14 case)
pillars = {
    "year": {"stem": "庚", "branch": "辰"},
    "month": {"stem": "乙", "branch": "酉"},
    "day": {"stem": "乙", "branch": "亥"},
    "hour": {"stem": "辛", "branch": "巳"},
}

# Build birth context with solar terms
# For this test, we'll use a simplified ctx with start_age override
birth_ctx = {
    "sex": "male",
    "birth_ts": "2000-09-14T10:00:00+09:00",
    "age_years_decimal": 25.1,
    "luck": {"method": "solar_term_interval", "start_age": 7.98},  # Simplified - using known value
}

print("Running Luck Pillars engine integration test...")
print("=" * 80)

# Call engine
result = calc.evaluate(birth_ctx, pillars)

# Display results
print(f"Policy Version: {result['policy_version']}")
print(f"Direction: {result['direction']}")
print(f"Start Age: {result['start_age']}")
print(f"Method: {result['method']}")
print(f"Pillars Count: {len(result['pillars'])}")
print()

print("First 3 Decade Pillars:")
for p in result["pillars"][:3]:
    print(f"  Decade {p['decade']}: {p['pillar']} (age {p['start_age']}-{p['end_age']})")

current = result.get("current_luck")
if current:
    print()
    print(
        f"Current Luck: Decade {current['decade']} ({current['pillar']}), {current['years_into_decade']:.2f} years into decade"
    )

print()
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

# Verify first pillar is 丙戌 (乙酉 + 1)
expected_first = "丙戌"
actual_first = result["pillars"][0]["pillar"]
print(f"Expected first pillar: {expected_first}")
print(f"Actual first pillar: {actual_first}")
print(f"Match: {'✅' if expected_first == actual_first else '❌'}")

# Verify direction is forward (male × 庚陽)
expected_dir = "forward"
actual_dir = result["direction"]
print(f"Expected direction: {expected_dir}")
print(f"Actual direction: {actual_dir}")
print(f"Match: {'✅' if expected_dir == actual_dir else '❌'}")

# Verify 10 pillars
expected_count = 10
actual_count = len(result["pillars"])
print(f"Expected pillar count: {expected_count}")
print(f"Actual pillar count: {actual_count}")
print(f"Match: {'✅' if expected_count == actual_count else '❌'}")

# Verify all pillars have correct decade numbers
all_decades_correct = all(p["decade"] == i + 1 for i, p in enumerate(result["pillars"]))
print(f"All decades numbered correctly: {'✅' if all_decades_correct else '❌'}")

# Verify all pillars have 10-year spans
all_spans_correct = all(p["end_age"] - p["start_age"] == 10 for p in result["pillars"])
print(f"All spans are 10 years: {'✅' if all_spans_correct else '❌'}")

# Verify signature exists and is hex
sig = result.get("policy_signature", "")
sig_valid = len(sig) == 64 and all(c in "0123456789abcdefABCDEF" for c in sig)
print(f"Policy signature valid: {'✅' if sig_valid else '❌'}")

print()
print("🎉 Luck Pillars Integration Test Complete!")
print()

# Show all 10 pillars
print("=" * 80)
print("ALL 10 DECADE PILLARS")
print("=" * 80)
for p in result["pillars"]:
    print(f"Decade {p['decade']:2d}: {p['pillar']} (age {p['start_age']:2.0f}-{p['end_age']:2.0f})")

print()
print("=" * 80)
