# Analysis Service: What Needs to Be Added/Fixed

**Current Status:** 9/21 tests passing (43%)
**Goal:** Get to 100% tests passing

---

## Issues Categorized by Severity

### 🔴 CRITICAL - Simple Bug Fixes (6 issues)

These are **easy fixes** - just undefined variables or missing arguments:

#### 1. **NameError: FIVE_HE_POLICY_PATH not defined**
**Files:** `app/core/relations.py`
**Line:** 54-55
**Problem:**
```python
# Code uses FIVE_HE_POLICY_PATH which doesn't exist
if FIVE_HE_POLICY_PATH.exists():  # ← NameError!
```

**Solution:**
```python
# Add this at top of file with other path definitions (after line 23):
FIVE_HE_POLICY_PATH = (
    FIVE_HE_POLICY_V12
    if FIVE_HE_POLICY_V12.exists()
    else FIVE_HE_POLICY_V10
)
```

**Affected tests:** 5 relation tests
- `test_sanhe_transform_priority`
- `test_banhe_priority_when_two_members_present`
- `test_sanhui_boost_when_no_transform`
- `test_chong_detected_when_conflict`
- `test_five_he_and_zixing_extras`

---

#### 2. **TypeError: SimpleSolarTermLoader() takes no arguments**
**Files:** `app/core/luck.py`
**Line:** 47
**Problem:**
```python
# From pillars-service, SimpleSolarTermLoader requires table_path
self._term_loader = SimpleSolarTermLoader(TERM_DATA_PATH)  # ← Wrong!
```

**Solution:**
```python
# SimpleSolarTermLoader is a dataclass that requires table_path parameter
self._term_loader = SimpleSolarTermLoader(table_path=TERM_DATA_PATH)
```

**Affected tests:** 2 luck tests
- `test_compute_luck_start_age`
- `test_luck_direction_default`

---

#### 3. **NameError: name 'F' is not defined**
**Files:** `app/core/llm_guard.py` (likely)
**Problem:**
```python
# Somewhere in the code, undefined variable 'F' is used
result = F.some_method()  # ← What is F?
```

**Need to investigate:** Check `app/core/llm_guard.py` or related files

**Affected tests:** 2 llm_guard tests
- `test_llm_guard_roundtrip`
- `test_llm_guard_detects_trace_mutation`

---

### 🟡 MEDIUM - Logic Implementation Issues (6 issues)

These require **implementing missing logic** in placeholder functions:

#### 4. **Structure confidence calculation is wrong**
**Files:** `app/core/structure.py`
**Tests failing:**
- `test_structure_primary_selected_with_confidence`
- `test_structure_candidates_only_when_below_primary_threshold`

**Problem:**
```python
# Test expects:
ctx = StructureContext(scores={"정관": 12, "편재": 7, "비겁": 5})
result = detector.evaluate(ctx)
assert result.primary == "정관"
assert result.confidence == "high"  # ← Getting 'mid' instead

# And:
ctx = StructureContext(scores={"정관": 8, "편재": 7, "비겁": 5})
result = detector.evaluate(ctx)
assert len(result.candidates) >= 2  # ← Getting only 1
```

**Issue:** Confidence thresholds and candidate filtering logic is incorrect

**What to check:**
- Confidence threshold logic (what score = "high" vs "mid" vs "low"?)
- Candidate filtering (when to include multiple candidates?)
- Policy file: `/policies/structure_rules_v2_6.json` or similar

---

#### 5. **Analyze endpoint returns wrong data**
**Files:** `app/core/engine.py`, `app/api/routes.py`
**Test:** `test_analyze_returns_sample_response`

**Problem:** Main integration test fails - likely cascades from issue #1 (FIVE_HE_POLICY_PATH)

**After fixing issue #1, retest this**

---

### 🟢 LOW PRIORITY - May Already Work (0 issues)

**None!** All current failures have identifiable causes.

---

## Quick Fix Checklist

Apply these fixes in order:

### ✅ Step 1: Fix FIVE_HE_POLICY_PATH (affects 5 tests)

**File:** `services/analysis-service/app/core/relations.py`

**Add after line 24:**
```python
FIVE_HE_POLICY_PATH = (
    FIVE_HE_POLICY_V12
    if FIVE_HE_POLICY_V12.exists()
    else FIVE_HE_POLICY_V10
)
```

**Expected result:** +5 tests passing (14/21 = 67%)

---

### ✅ Step 2: Fix SimpleSolarTermLoader argument (affects 2 tests)

**File:** `services/analysis-service/app/core/luck.py`

**Change line 47:**
```python
# OLD:
self._term_loader = SimpleSolarTermLoader(TERM_DATA_PATH)

# NEW:
self._term_loader = SimpleSolarTermLoader(table_path=TERM_DATA_PATH)
```

**Expected result:** +2 tests passing (16/21 = 76%)

---

### ✅ Step 3: Find and fix undefined 'F' (affects 2 tests)

**Files to check:**
```bash
grep -rn "\\bF\\." app/core/llm_guard.py
grep -rn "\\bF\\[" app/core/llm_guard.py
grep -rn "name 'F'" tests/test_llm_guard.py
```

**Likely issue:** Missing import or typo (F instead of f, or F instead of some class)

**Expected result:** +2 tests passing (18/21 = 86%)

---

### ⚠️ Step 4: Fix structure confidence logic (affects 2 tests)

**File:** `services/analysis-service/app/core/structure.py`

**Need to:**
1. Read the policy file to understand thresholds
2. Check confidence calculation logic
3. Check candidate filtering logic

**Investigation needed:**
```python
# What are the actual thresholds?
# - score >= X → confidence = "high"
# - score >= Y → confidence = "mid"
# - score < Y → confidence = "low"

# When to include candidates?
# - Include all scores within N points of top score?
# - Include all scores above threshold T?
```

**Check these files:**
- `app/core/structure.py` - implementation
- `policies/structure_rules_v2_*.json` - configuration
- `saju_codex_*/policies/structure_*.json` - versioned configs

**Expected result:** +2 tests passing (20/21 = 95%)

---

### ⚠️ Step 5: Verify analyze endpoint (affects 1 test)

**File:** `app/api/routes.py` or `app/core/engine.py`

**After fixing steps 1-4, retest:**
```bash
pytest tests/test_analyze.py::test_analyze_returns_sample_response -v
```

**Expected result:** +1 test passing (21/21 = 100%)

---

## Estimated Effort

| Step | Effort | Time | Impact |
|------|--------|------|--------|
| Step 1: FIVE_HE_POLICY_PATH | ⭐ Trivial | 2 min | +5 tests |
| Step 2: SimpleSolarTermLoader | ⭐ Trivial | 1 min | +2 tests |
| Step 3: Find 'F' | ⭐⭐ Easy | 5-10 min | +2 tests |
| Step 4: Structure logic | ⭐⭐⭐ Medium | 20-30 min | +2 tests |
| Step 5: Verify analyze | ⭐ Trivial | 2 min | +1 test |
| **TOTAL** | | **30-45 min** | **+12 tests** |

---

## What's Actually Missing vs Broken

### ✅ Already Implemented (Working)
- Climate evaluator (2 tests passing)
- Text guard (2 tests passing)
- Recommendation guard (2 tests passing)
- Health checks (2 tests passing)
- Shensha catalog (1 test passing)

### 🔧 Implemented but Broken (Simple Fixes)
- Relations transformer (5 tests) - just missing constant definition
- Luck calculator (2 tests) - just wrong argument syntax
- LLM guard (2 tests) - undefined variable 'F'

### ⚠️ Implemented but Incomplete (Logic Issues)
- Structure detector (2 tests) - confidence thresholds need tuning
- Analyze endpoint (1 test) - integration issue

### ❌ Not Implemented (Empty Stubs)
- **None!** All components have actual code

---

## Summary

**Good news:** The analysis service is **mostly complete**!

**Quick wins:**
- 3 trivial fixes = +9 tests (76% → 86%)
- 1 medium fix = +2 tests (86% → 95%)
- 1 retest = +1 test (95% → 100%)

**Not needed:**
- No major features missing
- No external integrations required
- No database setup needed
- No API changes needed

**Just needs:**
- Fix 3 typos/missing constants
- Tune 1 algorithm's thresholds

This is **30-45 minutes of work** to get from 43% to 100%!

---

## Next Actions

**If you want me to fix these:**

1. I can apply steps 1-3 immediately (trivial fixes)
2. For step 4, I'll need to read the policy files to understand the thresholds
3. Step 5 should auto-pass after steps 1-4

**To proceed:**
Just say "fix the analysis service" and I'll apply all fixes sequentially.

---

**Report prepared by:** Claude Code (Sonnet 4.5)
**Date:** 2025-10-04
**Analysis of:** services/analysis-service test failures
