#!/usr/bin/env python3
"""
Migrate relation_policy.json to match relation.schema.json structure.

This script transforms the legacy flat policy structure into the modern
grouped schema structure, handling:
- attenuation.rules → attenuation_rules (with field renaming)
- confidence_rules.params → confidence_rules.weights
- flat rules[] → grouped relationships{}
- Adding aggregation and evidence_template fields

Usage:
    python tools/migrate_relation_policy_to_schema_v1.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List

# Label mappings for relationship types
LABELS_KO = {
    "六合": "육합",
    "三合": "삼합",
    "半合": "반합",
    "方合": "방합",
    "拱合": "공합",
    "沖": "충",
    "破": "파",
    "害": "해",
    "刑_三刑": "삼형",
    "刑_自刑": "자형",
    "刑_偏刑": "편형",
}

LABELS_EN = {
    "六合": "liu-he",
    "三合": "san-he",
    "半合": "ban-he",
    "方合": "fang-he",
    "拱合": "gong-he",
    "沖": "chong",
    "破": "po",
    "害": "hai",
    "刑_三刑": "xing-tri",
    "刑_自刑": "xing-self",
    "刑_偏刑": "xing-bias",
}

# Nature classification (auspicious/neutral/inauspicious)
NATURE_MAP = {
    "六合": "auspicious",
    "三合": "auspicious",
    "半合": "auspicious",
    "方合": "neutral",
    "拱合": "neutral",
    "沖": "inauspicious",
    "破": "inauspicious",
    "害": "inauspicious",
    "刑_三刑": "inauspicious",
    "刑_自刑": "inauspicious",
    "刑_偏刑": "inauspicious",
}

# Score ranges for each relationship type
SCORE_RANGES = {
    "六合": {"min": 0, "max": 10},
    "三合": {"min": 0, "max": 20},
    "半合": {"min": 0, "max": 10},
    "方合": {"min": 0, "max": 8},
    "拱合": {"min": 0, "max": 6},
    "沖": {"min": -15, "max": 0},
    "破": {"min": -10, "max": 0},
    "害": {"min": -8, "max": 0},
    "刑_三刑": {"min": -12, "max": 0},
    "刑_自刑": {"min": -6, "max": 0},
    "刑_偏刑": {"min": -10, "max": 0},
}


def transform_attenuation(old_policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform attenuation.rules → attenuation_rules.

    Changes:
    - if_together[0] → when (with " present" suffix)
    - apply_to → attenuate[] (convert to array)
    - Remove notes_ko (not in schema)

    Example:
        IN:  {"if_together": ["沖", "三合"], "apply_to": "三合", "factor": 0.7}
        OUT: {"when": "沖 present", "attenuate": ["三合"], "factor": 0.7}
    """
    old_rules = old_policy.get("attenuation", {}).get("rules", [])
    new_rules = []

    for rule in old_rules:
        # Extract primary condition from if_together
        condition = rule.get("if_together", ["unknown"])[0]

        # Extract target(s) to attenuate
        apply_to = rule.get("apply_to", "")
        attenuate = [apply_to] if isinstance(apply_to, str) else apply_to

        new_rule = {
            "when": f"{condition} present",
            "attenuate": attenuate,
            "factor": rule["factor"],
        }
        new_rules.append(new_rule)

    return new_rules


def transform_confidence_rules(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform confidence_rules structure.

    Changes:
    - params → weights
    - Add normalization (moved from top-level)
    - Keep formula

    Example:
        IN:  {"method": "...", "params": {...}, "formula": "..."}
        OUT: {"formula": "...", "weights": {...}, "normalization": {...}}
    """
    old_cr = policy.get("confidence_rules", {})

    # Extract score bounds for normalization
    score_bounds = policy.get("score_bounds", {"min": -20, "max": 20})

    return {
        "formula": old_cr.get("formula", ""),
        "weights": old_cr.get("params", {}),  # Rename params → weights
        "normalization": {
            "score_range": {
                "min": score_bounds.get("min", -20),
                "max": score_bounds.get("max", 20),
            },
            "priority_range": {"min": 0, "max": 100},
        },
    }


def transform_rules_to_relationships(flat_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transform flat rules[] array → grouped relationships{} object.

    Groups rules by 'kind' and creates relationship metadata.

    Changes per rule:
    - pattern → branches
    - score_delta → score_hint
    - notes_ko → note_ko
    - Add element if element_bias present
    - Add xing_type for 刑 relationships

    Example:
        IN:  [{"kind": "六合", "pattern": ["子", "丑"], "score_delta": 8.0, ...}]
        OUT: {"六合": {"label_ko": "육합", ..., "rules": [{"branches": ["子", "丑"], "score_hint": 8.0, ...}]}}
    """
    relationships = {}

    for rule in flat_rules:
        kind = rule["kind"]

        # Initialize relationship type if not exists
        if kind not in relationships:
            relationships[kind] = {
                "label_ko": LABELS_KO.get(kind, kind),
                "label_zh": kind,
                "label_en": LABELS_EN.get(kind, kind.lower()),
                "nature": NATURE_MAP.get(kind, "neutral"),
                "score_range": SCORE_RANGES.get(kind, {"min": -10, "max": 10}),
                "rules": [],
            }

        # Transform rule fields
        transformed_rule = {
            "branches": rule["pattern"],  # Rename: pattern → branches
            "priority": rule["priority"],
            "score_hint": rule["score_delta"],  # Rename: score_delta → score_hint
            "note_ko": rule.get("notes_ko", ""),  # Rename: notes_ko → note_ko
        }

        # Add optional fields if present
        if rule.get("element_bias"):
            transformed_rule["element"] = rule["element_bias"]

        # Handle 刑 (xing) relationships special fields
        if "刑" in kind:
            if "directionality" in rule:
                # Map directionality to xing_type
                dir_map = {"self": "self", "cyclic": "punishment_of_power", "mutual": "ungrateful"}
                transformed_rule["xing_type"] = dir_map.get(
                    rule["directionality"], rule["directionality"]
                )

            # Add stacking behavior for self-punishment
            if rule["directionality"] == "self":
                transformed_rule["xing_stack"] = "per_set"
                transformed_rule["stack_cap"] = 1

        relationships[kind]["rules"].append(transformed_rule)

    return relationships


def migrate_policy(input_path: Path, output_path: Path, backup_path: Path = None):
    """
    Main migration function.

    Reads old policy, transforms to new schema structure, writes output.

    Args:
        input_path: Path to old relation_policy.json
        output_path: Path to write new migrated policy
        backup_path: Optional path to save backup of original
    """
    print(f"🔄 Starting migration: {input_path}")

    # Load old policy
    with open(input_path, "r", encoding="utf-8") as f:
        old_policy = json.load(f)

    print(f"   Loaded old policy (version {old_policy.get('version', 'unknown')})")

    # Create backup if requested
    if backup_path:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(old_policy, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Backup saved: {backup_path}")

    # Build new structure
    print("   Transforming structure...")

    new_policy = {
        "version": old_policy.get("version", "1.1"),
        "policy_name": "relation_policy",  # Schema constant
        "description": old_policy.get("description", ""),
        # Keep existing conservation structure (already correct)
        "conservation": old_policy.get("conservation", {}),
        # Transformed fields
        "confidence_rules": transform_confidence_rules(old_policy),
        "mutual_exclusion_groups": old_policy.get("mutual_exclusion_groups", []),
        "attenuation_rules": transform_attenuation(old_policy),
        "relationships": transform_rules_to_relationships(old_policy.get("rules", [])),
        # New required fields
        "aggregation": {
            "score_formula": old_policy.get("aggregation_contract", {}).get(
                "method", "weighted_sum"
            ),
            "score_note_ko": "가중합 계산: Σ(score_delta × weight × attenuation_factor)",
        },
        "evidence_template": {
            "relation_type": "",
            "branches_involved": [],
            "element_produced": None,
            "conservation_detail": {},
            "attenuation_applied": None,
            "confidence": 0.0,
        },
        # Keep CI checks (already correct)
        "ci_checks": old_policy.get("ci_checks", []),
    }

    # Write migrated policy
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_policy, f, ensure_ascii=False, indent=2)

    # Report statistics
    old_rules_count = len(old_policy.get("rules", []))
    new_rel_count = len(new_policy["relationships"])
    old_atten_count = len(old_policy.get("attenuation", {}).get("rules", []))
    new_atten_count = len(new_policy["attenuation_rules"])

    print("   ✅ Migration complete!")
    print("")
    print("   Statistics:")
    print(f"   - Transformed {old_rules_count} flat rules")
    print(f"   - Created {new_rel_count} relationship groups")
    print(f"   - Migrated {old_atten_count} attenuation rules → {new_atten_count}")
    print("   - Added 2 new required fields (aggregation, evidence_template)")
    print("")
    print(f"   Output: {output_path}")

    return new_policy


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    input_path = (
        repo_root / "saju_codex_batch_all_v2_6_signed" / "policies" / "relation_policy.json"
    )
    backup_path = (
        repo_root
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "relation_policy_v1.1_backup.json"
    )
    output_path = (
        repo_root
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "relation_policy_migrated.json"
    )

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        exit(1)

    try:
        migrate_policy(input_path, output_path, backup_path)
        print("")
        print("✅ SUCCESS: Migration complete!")
        print("")
        print("Next steps:")
        print(f"1. Review migrated file: {output_path}")
        print(f"2. Replace original: mv {output_path} {input_path}")
        print("3. Update tests: python tools/update_relation_tests.py")
        print("4. Run tests: pytest services/analysis-service/tests/test_relation_policy.py")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
