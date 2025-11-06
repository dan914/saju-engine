# Task #10 Implementation Plan: Re-enable Relation Schema Test

**Date:** 2025-10-12
**Status:** PLANNING (ULTRATHINK MODE)
**Priority:** 🟠 HIGH
**Estimated Time:** 2-3 hours
**Complexity:** HIGH (Schema/Policy structural misalignment)

---

## 1. Problem Analysis

### 1.1 Core Issue
The test `test_p0_schema_validation` is skipped because `relation_policy.json` and `relation.schema.json` are **structurally incompatible**. This isn't just missing fields - it's a fundamental architecture mismatch.

### 1.2 Current Skip Reason (from test file line 60)
```python
@pytest.mark.skip(reason="Policy missing required fields: attenuation_rules, aggregation, evidence_template. Schema needs alignment with actual policy structure.")
```

### 1.3 Discovered Mismatches

#### Mismatch #1: Schema Requires, Policy Has Different Name
| Schema Requires (line 14) | Policy Has (line 92) | Status |
|----------------------------|----------------------|--------|
| `attenuation_rules` (array) | `attenuation` (object with "rules" inside) | ❌ MISMATCH |
| `relationships` (object) | `rules` (array) | ❌ FUNDAMENTAL MISMATCH |
| `aggregation` (object) | `aggregation_contract` (object) | ❌ NAME MISMATCH |
| `evidence_template` (object) | *missing* | ❌ MISSING |

#### Mismatch #2: Nested Structure Issues
**Schema expects (lines 176-203):**
```json
"attenuation_rules": [
  {
    "when": "string",
    "attenuate": ["array"],
    "factor": 0.7
  }
]
```

**Policy has (lines 92-97):**
```json
"attenuation": {
  "rules": [
    {
      "if_together": ["沖", "三合"],
      "apply_to": "三合",
      "factor": 0.7
    }
  ]
}
```

#### Mismatch #3: confidence_rules Structure
**Schema expects (lines 96-140):**
```json
"confidence_rules": {
  "formula": "string",
  "weights": {
    "w_norm": 0.45,
    "w_conservation": 0.30,
    "w_priority": 0.15,
    "w_conflict": -0.20
  },
  "normalization": {
    "score_range": {"min": -20, "max": 20},
    "priority_range": {"min": 0, "max": 100}
  }
}
```

**Policy has (lines 105-114):**
```json
"confidence_rules": {
  "method": "deterministic_linear_v1",
  "params": {
    "w_norm": 0.45,
    "w_conservation": 0.30,
    "w_priority": 0.15,
    "w_conflict": -0.20
  },
  "formula": "conf = clamp01(...)"
}
```

**Issue:** Schema expects `weights`, policy has `params`. Schema expects `normalization`, policy has it at top level.

#### Mismatch #4: relationships vs rules
**Schema expects (lines 205-281):**
```json
"relationships": {
  "六合": {
    "label_ko": "육합",
    "label_zh": "六合",
    "label_en": "liu-he",
    "nature": "auspicious",
    "score_range": {"min": 0, "max": 10},
    "rules": [
      {
        "branches": ["子", "丑"],
        "priority": 70,
        "score_hint": 8.0,
        "note_ko": "자축합"
      }
    ]
  }
}
```

**Policy has (lines 202-260):**
```json
"rules": [
  {
    "id": "REL-LIUHE-01",
    "kind": "六合",
    "pattern": ["子", "丑"],
    "element_bias": "土",
    "score_delta": 8.0,
    "priority": 70,
    "notes_ko": "자축합(土)"
  }
]
```

**Issue:** Completely different structure - schema groups by relationship type, policy is flat array.

#### Mismatch #5: policy_name Value
**Schema expects (line 28):** `"policy_name": "relation_policy"` (const)
**Test expects (line 489):** `"policy_name": "Saju Relation Transformer Policy"` (string)
**Policy has (line 3):** `"policy_name": "relation_policy"` (matches schema now)

**Issue:** Test and schema are inconsistent!

---

## 2. Root Cause Analysis

### 2.1 Historical Context
This appears to be a **schema evolution mismatch**. The schema was likely designed for a newer/different architecture than the policy file implements:

1. **Schema Design:** Structured, grouped by relationship type, with metadata-heavy approach
2. **Policy Implementation:** Flat, rule-based, simpler structure
3. **Test Expectations:** Mixed - some tests expect old values, some new

### 2.2 Why This Happened
- Schema (`relation.schema.json`) was designed for **output validation** of analysis results
- Policy (`relation_policy.json`) was designed for **engine configuration**
- They evolved separately and diverged
- Tests were written against the policy structure, not schema structure

### 2.3 Evidence from Code Usage
Looking at `relations.py` (lines 33-36), the actual engine loads:
```python
RELATION_POLICY_PATH = _resolve_with_fallback(
    "relation_transform_rules_v1_1.json",  # ← DIFFERENT FILE!
    "relation_transform_rules.json"
)
```

**The engine doesn't even use `relation_policy.json`!** It uses `relation_transform_rules*.json`.

This means `relation_policy.json` might be:
1. Legacy/deprecated
2. For a different purpose (documentation/specification)
3. Never actually used in production

---

## 3. Solution Strategy

### 3.1 Three Possible Approaches

#### Approach A: Fix Policy to Match Schema (RECOMMENDED)
**Effort:** 2-3 hours
**Risk:** Medium (requires restructuring policy file)
**Benefit:** Schema becomes source of truth, proper validation

**Steps:**
1. Restructure policy to match schema requirements
2. Update all tests to match new structure
3. Verify all 14 test cases still pass
4. Re-sign policy with RFC-8785

**Pros:**
- Schema-driven design (best practice)
- Future-proof validation
- Clean separation of concerns

**Cons:**
- Breaking change to policy file
- Need to update any code that reads it (if any)

#### Approach B: Fix Schema to Match Policy
**Effort:** 1-2 hours
**Risk:** Low (schema is more flexible)
**Benefit:** Minimal code changes

**Steps:**
1. Rewrite schema to match actual policy structure
2. Change required fields to match what exists
3. Update schema field names

**Pros:**
- Minimal disruption
- Policy file stays the same
- Tests mostly unchanged

**Cons:**
- Schema becomes descriptive, not prescriptive
- Loses validation rigor
- Technical debt accumulates

#### Approach C: Create Adapter/Transformer
**Effort:** 3-4 hours
**Risk:** High (adds complexity layer)
**Benefit:** Both structures coexist

**Steps:**
1. Keep both schema and policy as-is
2. Write adapter to transform policy → schema format
3. Validate transformed result

**Pros:**
- No breaking changes
- Gradual migration path

**Cons:**
- Added complexity
- Maintenance burden
- Doesn't solve root problem

### 3.2 Recommended: Approach A (Fix Policy to Match Schema)

**Rationale:**
- Schema is more modern, structured design
- Better for long-term maintenance
- `relations.py` doesn't use this file anyway (uses `relation_transform_rules*.json`)
- Safe to restructure since it's not in critical path

---

## 4. Implementation Plan (Approach A)

### 4.1 Phase 1: Restructure Policy File

#### Step 1: Rename/Restructure Top-Level Fields
```json
{
  "version": "1.1",                          // ✅ Already correct
  "policy_name": "relation_policy",          // ✅ Already correct
  "description": "...",                      // ✅ Already correct

  // CHANGE: Flatten attenuation structure
  "attenuation_rules": [                     // ← WAS: "attenuation": {"rules": [...]}
    {
      "when": "沖 present",                  // ← WAS: "if_together": ["沖", "三合"]
      "attenuate": ["三合"],                 // ← WAS: "apply_to": "三合"
      "factor": 0.7
    }
  ],

  // CHANGE: Restructure confidence_rules
  "confidence_rules": {
    "formula": "conf = clamp01(...)",
    "weights": {                             // ← WAS: "params"
      "w_norm": 0.45,
      "w_conservation": 0.30,
      "w_priority": 0.15,
      "w_conflict": -0.20
    },
    "normalization": {                       // ← MOVE FROM TOP LEVEL
      "score_range": {"min": -20, "max": 20},
      "priority_range": {"min": 0, "max": 100}
    }
  },

  // KEEP AS-IS
  "mutual_exclusion_groups": [...],

  // CHANGE: Group rules by relationship type
  "relationships": {
    "六合": {
      "label_ko": "육합",
      "label_zh": "六合",
      "label_en": "liu-he",
      "nature": "auspicious",
      "score_range": {"min": 0, "max": 10},
      "rules": [
        {
          "branches": ["子", "丑"],          // ← WAS: "pattern"
          "priority": 70,
          "score_hint": 8.0,                 // ← WAS: "score_delta"
          "note_ko": "자축합(土)"            // ← WAS: "notes_ko"
        }
      ]
    },
    "三合": {...},
    "半合": {...},
    // ... etc
  },

  // ADD: New required field
  "aggregation": {                           // ← WAS: "aggregation_contract"
    "score_formula": "weighted_sum",
    "score_note_ko": "가중합 기반 점수 집계"
  },

  // ADD: New required field
  "evidence_template": {
    "relation_type": "",
    "branches_involved": [],
    "element_produced": null,
    "conservation_detail": {},
    "attenuation_applied": null,
    "confidence": 0.0
  },

  "ci_checks": [...]                         // ✅ Already correct
}
```

#### Step 2: Transform attenuation Structure
**Before:**
```json
"attenuation": {
  "rules": [
    {"if_together": ["沖", "三合"], "apply_to": "三合", "factor": 0.7, "notes_ko": "충 존재 시 삼합 약화"}
  ]
}
```

**After:**
```json
"attenuation_rules": [
  {"when": "沖 present", "attenuate": ["三合"], "factor": 0.7}
]
```

**Transformation Logic:**
- `if_together[0]` → `when` (with " present" suffix)
- `apply_to` → `attenuate[0]` (convert to array)
- Remove `notes_ko` (not in schema)

#### Step 3: Restructure confidence_rules
**Before:**
```json
"confidence_rules": {
  "method": "deterministic_linear_v1",
  "params": {...},
  "formula": "..."
}
```

**After:**
```json
"confidence_rules": {
  "formula": "...",
  "weights": {...},       // rename from "params"
  "normalization": {...}  // move from top level
}
```

#### Step 4: Transform rules → relationships
This is the biggest change. Convert flat array to grouped object:

**Algorithm:**
```python
def transform_rules_to_relationships(flat_rules):
    relationships = {}

    for rule in flat_rules:
        kind = rule["kind"]

        # Initialize relationship type if not exists
        if kind not in relationships:
            relationships[kind] = {
                "label_ko": LABELS_KO[kind],
                "label_zh": kind,
                "label_en": LABELS_EN[kind],
                "nature": NATURE_MAP[kind],
                "score_range": SCORE_RANGES[kind],
                "rules": []
            }

        # Transform rule fields
        transformed_rule = {
            "branches": rule["pattern"],        # rename
            "priority": rule["priority"],
            "score_hint": rule["score_delta"],  # rename
            "note_ko": rule["notes_ko"]
        }

        # Add optional fields if present
        if "element_bias" in rule and rule["element_bias"]:
            transformed_rule["element"] = rule["element_bias"]
        if "刑" in kind:
            transformed_rule["xing_type"] = XING_TYPE_MAP[kind]

        relationships[kind]["rules"].append(transformed_rule)

    return relationships
```

**Lookup Tables Needed:**
```python
LABELS_KO = {
    "六合": "육합", "三合": "삼합", "半合": "반합",
    "方合": "방합", "拱合": "공합", "沖": "충",
    "破": "파", "害": "해", "刑_三刑": "삼형",
    "刑_自刑": "자형", "刑_偏刑": "편형"
}

NATURE_MAP = {
    "六合": "auspicious", "三合": "auspicious", "半合": "auspicious",
    "方合": "neutral", "拱合": "neutral",
    "沖": "inauspicious", "破": "inauspicious", "害": "inauspicious",
    "刑_三刑": "inauspicious", "刑_自刑": "inauspicious", "刑_偏刑": "inauspicious"
}

SCORE_RANGES = {
    "六合": {"min": 0, "max": 10},
    "三合": {"min": 0, "max": 20},
    "半合": {"min": 0, "max": 10},
    # ... etc
}
```

#### Step 5: Add Missing Fields
```json
"aggregation": {
  "score_formula": "weighted_sum",  // from aggregation_contract.method
  "score_note_ko": "가중합 계산: Σ(score_delta × weight × attenuation_factor)"
},

"evidence_template": {
  "relation_type": "",
  "branches_involved": [],
  "element_produced": null,
  "conservation_detail": {},
  "attenuation_applied": null,
  "confidence": 0.0
}
```

### 4.2 Phase 2: Update Test File

#### Test Changes Needed

**Change 1: test_summary_all_checks_pass (line 489)**
```python
# BEFORE
assert policy["policy_name"] == "Saju Relation Transformer Policy"

# AFTER
assert policy["policy_name"] == "relation_policy"  # Match schema const
```

**Change 2: All test_caseXX tests (lines 284-478)**
These tests access `policy["rules"]` directly, need to adapt:

```python
# BEFORE
for rule in policy["rules"]:
    if rule["kind"] == "六合" and set(rule["pattern"]) == {"子", "丑"}:
        zi_chou = rule
        break

# AFTER
liuhe_rules = policy["relationships"]["六合"]["rules"]
for rule in liuhe_rules:
    if set(rule["branches"]) == {"子", "丑"}:
        zi_chou = rule
        break
```

**Change 3: CI check tests (lines 256-263)**
```python
# BEFORE
attenuation_rules = policy["attenuation"]["rules"]

# AFTER
attenuation_rules = policy["attenuation_rules"]
```

**Change 4: Confidence tests (lines 113-134)**
```python
# BEFORE
params = policy["confidence_rules"]["params"]

# AFTER
weights = policy["confidence_rules"]["weights"]
```

### 4.3 Phase 3: Create Transformation Script

**File:** `tools/migrate_relation_policy_to_schema_v1.py`

```python
#!/usr/bin/env python3
"""
Migrate relation_policy.json to match relation.schema.json structure.

Usage:
    python tools/migrate_relation_policy_to_schema_v1.py
"""

import json
from pathlib import Path

# Label mappings
LABELS_KO = {
    "六合": "육합", "三合": "삼합", "半合": "반합",
    "方合": "방합", "拱合": "공합", "沖": "충",
    "破": "파", "害": "해", "刑_三刑": "삼형",
    "刑_自刑": "자형", "刑_偏刑": "편형"
}

LABELS_EN = {
    "六合": "liu-he", "三合": "san-he", "半合": "ban-he",
    "方合": "fang-he", "拱合": "gong-he", "沖": "chong",
    "破": "po", "害": "hai", "刑_三刑": "xing-tri",
    "刑_自刑": "xing-self", "刑_偏刑": "xing-bias"
}

NATURE_MAP = {
    "六合": "auspicious", "三合": "auspicious", "半合": "auspicious",
    "方合": "neutral", "拱合": "neutral",
    "沖": "inauspicious", "破": "inauspicious", "害": "inauspicious",
    "刑_三刑": "inauspicious", "刑_自刑": "inauspicious", "刑_偏刑": "inauspicious"
}

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
    "刑_偏刑": {"min": -10, "max": 0}
}


def transform_attenuation(old_structure):
    """Transform attenuation.rules → attenuation_rules."""
    old_rules = old_structure.get("attenuation", {}).get("rules", [])
    new_rules = []

    for rule in old_rules:
        new_rule = {
            "when": f"{rule['if_together'][0]} present",
            "attenuate": [rule["apply_to"]] if isinstance(rule["apply_to"], str) else rule["apply_to"],
            "factor": rule["factor"]
        }
        new_rules.append(new_rule)

    return new_rules


def transform_confidence_rules(policy):
    """Transform confidence_rules structure."""
    old_cr = policy.get("confidence_rules", {})

    return {
        "formula": old_cr.get("formula", ""),
        "weights": old_cr.get("params", {}),  # rename params → weights
        "normalization": {
            "score_range": {
                "min": policy.get("score_bounds", {}).get("min", -20),
                "max": policy.get("score_bounds", {}).get("max", 20)
            },
            "priority_range": {
                "min": 0,
                "max": 100
            }
        }
    }


def transform_rules_to_relationships(flat_rules):
    """Transform flat rules array → grouped relationships object."""
    relationships = {}

    for rule in flat_rules:
        kind = rule["kind"]

        # Initialize relationship type
        if kind not in relationships:
            relationships[kind] = {
                "label_ko": LABELS_KO.get(kind, kind),
                "label_zh": kind,
                "label_en": LABELS_EN.get(kind, kind.lower()),
                "nature": NATURE_MAP.get(kind, "neutral"),
                "score_range": SCORE_RANGES.get(kind, {"min": -10, "max": 10}),
                "rules": []
            }

        # Transform rule fields
        transformed_rule = {
            "branches": rule["pattern"],
            "priority": rule["priority"],
            "score_hint": rule["score_delta"],
            "note_ko": rule.get("notes_ko", "")
        }

        # Add optional fields
        if rule.get("element_bias"):
            transformed_rule["element"] = rule["element_bias"]
        if "刑" in kind:
            if "directionality" in rule:
                transformed_rule["xing_type"] = rule["directionality"]

        relationships[kind]["rules"].append(transformed_rule)

    return relationships


def migrate_policy(input_path, output_path):
    """Migrate policy file to new schema structure."""
    with open(input_path, "r", encoding="utf-8") as f:
        old_policy = json.load(f)

    # Build new structure
    new_policy = {
        "version": old_policy.get("version", "1.1"),
        "policy_name": "relation_policy",  # Schema const
        "description": old_policy.get("description", ""),

        # Transformed fields
        "conservation": old_policy.get("conservation", {}),
        "confidence_rules": transform_confidence_rules(old_policy),
        "mutual_exclusion_groups": old_policy.get("mutual_exclusion_groups", []),
        "attenuation_rules": transform_attenuation(old_policy),
        "relationships": transform_rules_to_relationships(old_policy.get("rules", [])),

        # New required fields
        "aggregation": {
            "score_formula": old_policy.get("aggregation_contract", {}).get("method", "weighted_sum"),
            "score_note_ko": "가중합 계산: Σ(score_delta × weight × attenuation_factor)"
        },
        "evidence_template": {
            "relation_type": "",
            "branches_involved": [],
            "element_produced": None,
            "conservation_detail": {},
            "attenuation_applied": None,
            "confidence": 0.0
        },

        "ci_checks": old_policy.get("ci_checks", [])
    }

    # Write migrated policy
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_policy, f, ensure_ascii=False, indent=2)

    print(f"✅ Migrated {input_path} → {output_path}")
    print(f"   - Transformed {len(old_policy.get('rules', []))} flat rules")
    print(f"   - Created {len(new_policy['relationships'])} relationship groups")
    print(f"   - Migrated {len(old_policy.get('attenuation', {}).get('rules', []))} attenuation rules")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / "saju_codex_batch_all_v2_6_signed" / "policies" / "relation_policy.json"
    output_path = repo_root / "saju_codex_batch_all_v2_6_signed" / "policies" / "relation_policy_v1.2.json"

    migrate_policy(input_path, output_path)
```

### 4.4 Phase 4: Update All Tests

Create `tools/update_relation_tests.py`:

```python
#!/usr/bin/env python3
"""Update test_relation_policy.py to match new schema structure."""

import re
from pathlib import Path

def update_test_file(test_path):
    """Apply regex replacements to update test file."""
    with open(test_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace policy["rules"] access patterns
    content = re.sub(
        r'for rule in policy\["rules"\]:',
        'for rel_type, rel_data in policy["relationships"].items():\n        for rule in rel_data["rules"]:',
        content
    )

    # Replace pattern → branches
    content = content.replace('rule["pattern"]', 'rule["branches"]')

    # Replace score_delta → score_hint
    content = content.replace('rule["score_delta"]', 'rule["score_hint"]')

    # Replace notes_ko → note_ko
    content = content.replace('rule["notes_ko"]', 'rule["note_ko"]')

    # Replace attenuation.rules → attenuation_rules
    content = content.replace('policy["attenuation"]["rules"]', 'policy["attenuation_rules"]')

    # Replace params → weights
    content = content.replace('policy["confidence_rules"]["params"]', 'policy["confidence_rules"]["weights"]')

    # Fix policy_name assertion
    content = content.replace(
        'assert policy["policy_name"] == "Saju Relation Transformer Policy"',
        'assert policy["policy_name"] == "relation_policy"'
    )

    # Write updated content
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Updated {test_path}")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    test_path = repo_root / "services" / "analysis-service" / "tests" / "test_relation_policy.py"
    update_test_file(test_path)
```

---

## 5. Execution Steps

### Step 1: Run Migration Script
```bash
python tools/migrate_relation_policy_to_schema_v1.py
```

### Step 2: Backup Old File
```bash
cp saju_codex_batch_all_v2_6_signed/policies/relation_policy.json \
   saju_codex_batch_all_v2_6_signed/policies/relation_policy_v1.1_backup.json
```

### Step 3: Replace with Migrated Version
```bash
mv saju_codex_batch_all_v2_6_signed/policies/relation_policy_v1.2.json \
   saju_codex_batch_all_v2_6_signed/policies/relation_policy.json
```

### Step 4: Update Tests
```bash
python tools/update_relation_tests.py
```

### Step 5: Run Schema Validation
```bash
pytest services/analysis-service/tests/test_relation_policy.py::test_p0_schema_validation -v
```

### Step 6: Run All Relation Tests
```bash
pytest services/analysis-service/tests/test_relation_policy.py -v
```

### Step 7: Re-sign Policy
```bash
python tools/sign_policies.py saju_codex_batch_all_v2_6_signed/policies/relation_policy.json
```

---

## 6. Edge Cases & Risks

### Risk #1: Breaking Changes for Existing Code
**Mitigation:** Check if any code actually loads this file (it doesn't appear to)

### Risk #2: Test Suite Compatibility
**Mitigation:** Run full test suite after changes

### Risk #3: Signature Validation
**Mitigation:** Re-sign after all changes complete

### Risk #4: Data Loss During Migration
**Mitigation:** Keep backup of original file

---

## 7. Success Criteria

1. ✅ `test_p0_schema_validation` passes (skip removed)
2. ✅ All 14 test cases pass
3. ✅ Schema validation succeeds
4. ✅ RFC-8785 signature valid
5. ✅ No other tests broken
6. ✅ Backup of old file preserved

---

## 8. Rollback Plan

If anything breaks:
```bash
# Restore backup
cp saju_codex_batch_all_v2_6_signed/policies/relation_policy_v1.1_backup.json \
   saju_codex_batch_all_v2_6_signed/policies/relation_policy.json

# Restore test file from git
git checkout services/analysis-service/tests/test_relation_policy.py
```

---

## 9. Alternative: Quick Fix (If Time Constrained)

If 2-3 hours is too long, do **minimal fix** instead:

1. Fix `policy_name` in test (line 489): change to `"relation_policy"`
2. Add stub fields to policy:
```json
"attenuation_rules": [],  // empty for now
"aggregation": {"score_formula": "", "score_note_ko": ""},
"evidence_template": {
  "relation_type": "", "branches_involved": [],
  "element_produced": null, "conservation_detail": {},
  "attenuation_applied": null, "confidence": 0.0
},
"relationships": {}  // empty for now
```
3. Keep skip on test, update reason to: "Partial schema compliance - full migration pending"

**Effort:** 15 minutes
**Risk:** Very low
**Benefit:** Removes blocker, defers full work

---

## 10. Recommendation

**For Production:** Do **Approach A (Full Migration)** - 2-3 hours investment for long-term benefit

**For Quick Win:** Do **Quick Fix** - 15 minutes to remove immediate blocker

**My Recommendation:** Full migration, because:
1. `relations.py` doesn't use this file anyway (low risk)
2. Schema is better designed
3. Proper validation prevents future bugs
4. Technical debt accumulates otherwise

---

**Status:** READY FOR IMPLEMENTATION
**Next Action:** Confirm approach, then execute
