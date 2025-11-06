# Audit Fixes Report

**Date:** 2025-10-12 KST
**Context:** Fixing issues identified in external audit of Tasks #11 and #17

---

## Issue #1: Task #17 - Hardcoded Test Assertion ✅ FIXED

### Problem
- **File:** `services/tz-time-service/tests/test_routes.py:18`
- **Issue:** Test asserted hardcoded `tzdb_version == "2025a"`, but implementation now dynamically detects `"2025b"`
- **Impact:** Test would fail on systems with newer tzdata

### Fix Applied
**Changed:**
```python
# Before:
assert payload["tzdb_version"] == "2025a"

# After:
# tzdb_version is dynamically detected - just verify it's a non-empty string
assert isinstance(payload["tzdb_version"], str)
assert len(payload["tzdb_version"]) > 0
```

**Location:** `services/tz-time-service/tests/test_routes.py:18-20`

**Verification:** Test now passes regardless of system tzdata version.

---

## Issue #2: Task #11 - Orchestrator Not Using Calculation Methods ✅ FIXED

### Problem
- **File:** `services/analysis-service/app/core/saju_orchestrator.py:771, 782`
- **Issue:** Orchestrator still used hardcoded placeholders:
  - Line 771: `"confidence": 0.8  # TODO: Add confidence...`
  - Line 782: `"impact_weight": item.get("weight", 0.7)`
- **Impact:** New calculation methods in `EngineSummariesBuilder` were never called in production

### Root Cause
The `extract_from_analysis_result()` method was designed for `AnalysisResponse` format (nested `strength`/`strength_details`), but the orchestrator uses a flat `combined` dict from raw engine outputs. Structure mismatch prevented direct use.

### Fix Applied
**Strategy:** Keep orchestrator's extraction logic (which understands its own dict structure), but call the new calculation methods.

**Changes:**
```python
# Before (line 771):
"confidence": 0.8  # TODO: Add confidence to StrengthEvaluator

# After (lines 774-776):
"confidence": EngineSummariesBuilder._calculate_strength_confidence(
    raw_score, bucket
)  # ✅ Use calculation method (not placeholder)

# Before (line 782):
"impact_weight": item.get("weight", 0.7),

# After (lines 787-789):
"impact_weight": EngineSummariesBuilder._calculate_relation_impact_weight(
    rel_type
),  # ✅ Use calculation method (not placeholder)
```

**Location:** `services/analysis-service/app/core/saju_orchestrator.py:759-822`

### Calculation Methods Used

1. **`_calculate_strength_confidence(score, bucket)`** (lines 136-176 of engine_summaries.py)
   - Geometric distance from bucket boundaries
   - Range: 0.60 (at boundary) to 0.95 (at center)
   - Buckets: 극신강 (80-100), 신강 (60-79), 중화 (40-59), 신약 (20-39), 극신약 (0-19)

2. **`_calculate_relation_impact_weight(rel_type)`** (lines 178-198 of engine_summaries.py)
   - Based on traditional 사주 theory
   - Weights:
     - chong (沖): 0.90 (highest impact)
     - sanhe (三合): 0.85
     - he6 (六合): 0.75
     - xing (刑): 0.70
     - po (破): 0.50
     - hai (害): 0.45

### Verification
✅ No more hardcoded `0.8` or `0.7` placeholders
✅ TODO comment removed
✅ Confidence values now calculated based on score position
✅ Impact weights now based on relation type theory

---

## Summary

Both audit findings were **valid and critical**:
- Task #17 had a test that would fail on newer systems
- Task #11 created helper methods but never wired them into production code

Both issues are now **completely resolved**:
- Tests are version-agnostic
- Production code uses calculated values (not placeholders)

**Files Modified:** 2
1. `services/tz-time-service/tests/test_routes.py` (3 lines changed)
2. `services/analysis-service/app/core/saju_orchestrator.py` (64 lines refactored)

**Impact:**
- Task #17: Now properly complete ✅
- Task #11: Now properly complete ✅

---

## Recommendation

Consider adding integration tests that verify:
1. Confidence values are in expected ranges (0.60-0.95)
2. Impact weights match theoretical priorities
3. No placeholders remain in production output

This would catch similar issues before they reach audit stage.
