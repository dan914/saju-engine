# 🔧 ULTRATHINK: Combination Element Transformer Integration Plan

**Date:** 2025-10-08 KST
**Engine:** combination_element v1.2.0 (합화오행 Transformer)
**Status:** Ready for integration

---

## Executive Summary

User provided combination_element transformer engine - transforms element distribution based on relationships (sanhe/liuhe/stem_combo/clash) with weighted moves and priorities.

**Complexity:** Medium-High (most complex engine so far)
**Risk:** Low (isolated transformation logic)
**Estimated Time:** 15-20 minutes

---

## What's Being Added

### 1. Core Engine: combination_element.py
- **Purpose:** Transform 5-element distribution based on relationships
- **Algorithm:** Priority-based weighted moves with normalization
- **Features:**
  - Sanhe (삼합) - primary move (+0.20)
  - Liuhe (육합) - secondary move (+0.10)
  - Stem combo (천간합) - tertiary move (+0.08)
  - Clash (충) - negative move (-0.10)
  - Policy override support
  - Improved fairness in normalization
- **API:**
  - `transform_wuxing(relations, dist_raw, policy)` → (dict, list[dict])
  - `normalize_distribution(dist)` → dict

### 2. Schema: combination_trace.schema.json
- **Standard:** JSON Schema draft-2020-12
- **Validation:** Array of trace objects with reason/target/moved_ratio/weight/order/policy_signature

### 3. Tests: test_combination_element.py
- 7+ test cases
- Sanhe primary move test
- Liuhe secondary move test
- Clash negative move test
- Multiple rules normalization test
- Trace schema validation test
- Policy override test
- Fairness tests (improved normalization)

### 4. Documentation: combination_element.md
- Korean language
- API examples
- Policy override format
- Rules summary

---

## Integration Changes Required

### 1. Replace infra.signatures Import
Same as void/yuanjin - use inline `_canonical_json_signature()`.

### 2. Update Policy Path Resolution
```python
candidates = [
    Path("policies") / "combination_policy_v1.json",
    Path("saju_codex_batch_all_v2_6_signed") / "policies" / "combination_policy_v1.json",
    Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "combination_policy_v1.json",
]
```

### 3. Fix Test Imports
```python
from app.core import combination_element as ce
```

### 4. Update Documentation Imports
```python
from app.core.combination_element import transform_wuxing
```

### 5. Include Normalization Improvement
The diff includes an improved `normalize_distribution()` function with fairer residual distribution to prevent bias when summing to 1.0.

---

## Key Features

### Policy Specification
```python
{
    "sanhe": {"ratio": 0.20, "order": 1},      # 局成 (formation)
    "liuhe": {"ratio": 0.10, "order": 2},      # 六合
    "stem_combo": {"ratio": 0.08, "order": 3}, # 天干合
    "clash": {"ratio": -0.10, "order": 4},     # 충 (negative)
}
```

### Move Algorithm
1. **Positive ratio** (sanhe/liuhe/stem_combo):
   - Take `ratio` amount proportionally from other elements
   - Add to target element

2. **Negative ratio** (clash):
   - Take `|ratio|` amount from target element
   - Distribute proportionally to other elements

3. **Priority rules:**
   - Lower order number = higher priority
   - Within same order, only first target is applied
   - After each move, normalize to sum=1.0

### Improved Normalization
**Old approach:** Add all residual to largest element (can create bias)

**New approach (fairness enhancement):**
1. First normalize: vals / sum
2. Distribute residual proportionally to current weights
3. Clamp negatives to 0
4. Final micro-adjustment to largest element if needed

This prevents bias when one element is already dominant.

---

## Implementation Steps

1. ✅ Create integration plan
2. Create `services/analysis-service/app/core/combination_element.py`:
   - Remove `from infra.signatures import sha256_signature`
   - Add inline `_canonical_json_signature()` function
   - Update policy path candidates
   - Include improved `normalize_distribution()` function
3. Create `services/analysis-service/schemas/combination_trace.schema.json`
4. Create `services/analysis-service/tests/test_combination_element.py`:
   - Fix import: `from app.core import combination_element as ce`
   - Include all test cases including fairness tests
5. Create `docs/engines/combination_element.md`:
   - Update import examples
6. Run tests
7. Format with black/isort
8. Commit and push

---

## Expected Results

**Tests:** All tests should pass (7+ test cases)
**Format:** Clean black/isort formatting
**Integration:** Standalone transformer ready for AnalysisEngine integration

---

**Ready to execute:** YES
**Dependencies:** None (inline signature utility)
**Next Action:** Create files with improvements
