#!/usr/bin/env python3
"""Debug script to check relation policy loading."""

import json
from pathlib import Path

# Manually check policy files
POLICY_BASE = Path(__file__).resolve().parent.parent

RELATION_POLICY_V25 = (
    POLICY_BASE / "saju_codex_v2_5_bundle" / "policies" / "relation_structure_adjust_v2_5.json"
)
RELATION_POLICY_V21 = (
    POLICY_BASE / "saju_codex_addendum_v2_1" / "policies" / "relation_transform_rules_v1_1.json"
)
RELATION_POLICY_V2 = (
    POLICY_BASE / "saju_codex_addendum_v2" / "policies" / "relation_transform_rules.json"
)

print(f"V25 exists: {RELATION_POLICY_V25.exists()} at {RELATION_POLICY_V25}")
print(f"V21 exists: {RELATION_POLICY_V21.exists()} at {RELATION_POLICY_V21}")
print(f"V2 exists: {RELATION_POLICY_V2.exists()} at {RELATION_POLICY_V2}")
print()

# Determine which one to load
policy_path = (
    RELATION_POLICY_V25
    if RELATION_POLICY_V25.exists()
    else (RELATION_POLICY_V21 if RELATION_POLICY_V21.exists() else RELATION_POLICY_V2)
)

print(f"Loading from: {policy_path}")
print()

with policy_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("Policy keys:", list(data.keys()))
print("Priority:", data.get("priority", []))
print("Definitions keys:", list(data.get("definitions", {}).keys()))

if "definitions" in data:
    defs = data["definitions"]
    if "sanhe_groups" in defs:
        print("Sanhe groups:", list(defs["sanhe_groups"].keys()))
