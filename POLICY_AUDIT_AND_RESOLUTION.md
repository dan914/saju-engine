# Policy Audit and Resolution Report

**Date:** 2025-10-10
**Purpose:** Determine canonical policy locations and versions for orchestrator integration

---

## Executive Summary

The project has **3 primary policy directories** with different purposes:

1. **`/policy/`** (CANONICAL) - Newest policies for Stage-3 engines and meta-engines
2. **`/saju_codex_batch_all_v2_6_signed/policies/`** - Main policy repository for core engines
3. **`/saju_codex_addendum_v2/policies/`** - Legacy policies for climate, luck, etc.

**Policy Loader** (`services/common/policy_loader.py`) correctly searches in order:
1. POLICY_DIR env var (if set)
2. `./policy/` (canonical)
3. Legacy directories (fallback)

---

## Policy Resolution Table

| Policy File | Current Location | Version | Status |
|-------------|-----------------|---------|--------|
| **Core Engine Policies** | | | |
| strength_policy_v2.json | saju_codex_batch_all_v2_6_signed/policies/ | 2.0.1 | ✅ ACTIVE |
| relation_policy.json | saju_codex_batch_all_v2_6_signed/policies/ | (none) | ✅ ACTIVE |
| shensha_v2_policy.json | saju_codex_batch_all_v2_6_signed/policies/ | (check) | ✅ ACTIVE |
| branch_tengods_policy.json | saju_codex_batch_all_v2_6_signed/policies/ | (check) | ✅ ACTIVE |
| localization_ko_v1.json | saju_codex_batch_all_v2_6_signed/policies/ | 1.1 | ✅ ACTIVE |
| luck_pillars_policy.json | saju_codex_batch_all_v2_6_signed/policies/ | (check) | ✅ ACTIVE |
| gyeokguk_policy.json | saju_codex_batch_all_v2_6_signed/policies/ | (check) | ✅ ACTIVE |
| school_profiles_v1.json | saju_codex_batch_all_v2_6_signed/policies/ | (check) | ✅ ACTIVE |
| **Legacy Policies** | | | |
| climate_map_v1.json | saju_codex_addendum_v2/policies/ | 1.0 | ✅ ACTIVE |
| luck_policy_v1.json | saju_codex_addendum_v2/policies/ | 1.0 | ✅ ACTIVE |
| relation_transform_rules.json | saju_codex_addendum_v2/policies/ | (check) | ✅ ACTIVE |
| structure_rules_v1.json | saju_codex_addendum_v2/policies/ | (check) | ✅ ACTIVE |
| text_guard_policy_v1.json | saju_codex_addendum_v2/policies/ | (check) | ✅ ACTIVE |
| **Canonical /policy/ (Newest)** | | | |
| climate_advice_policy_v1.json | policy/ | climate_advice_policy_v1 | ✅ ACTIVE (Stage-3) |
| gyeokguk_policy_v1.json | policy/ | gyeokguk_policy_v1 | ✅ ACTIVE (Stage-3) |
| luck_flow_policy_v1.json | policy/ | luck_flow_policy_v1 | ✅ ACTIVE (Stage-3) |
| pattern_profiler_policy_v1.json | policy/ | pattern_profiler_policy_v1 | ✅ ACTIVE (Stage-3) |
| llm_guard_policy_v1.json | policy/ | 1.0.0 | ✅ ACTIVE (LLM Guard) |
| llm_guard_policy_v1.1.json | policy/ | 1.1.0 | ✅ ACTIVE (LLM Guard) |
| relation_weight_policy_v1.0.json | policy/ | relation_weight_v1.0.0 | ✅ ACTIVE (Meta-engine) |
| yongshin_selector_policy_v1.json | policy/ | yongshin_v1.0.0 | ✅ ACTIVE (Meta-engine) |
| relation_policy_v1.json | policy/ | relation_policy_v1 | ⚠️ DUPLICATE (check usage) |

---

## Issues Identified

### Issue 1: Hardcoded Paths in Engines

**Affected Files:**
- `services/analysis-service/app/core/climate.py` - Hardcoded path to `saju_codex_addendum_v2/policies/climate_map_v1.json`

**Problem:**
```python
POLICY_PATH = (
    Path(__file__).resolve().parents[5]
    / "saju_codex_addendum_v2"
    / "policies"
    / "climate_map_v1.json"
)
```

**Solution:**
Use policy_loader instead:
```python
from policy_loader import resolve_policy_path

POLICY_PATH = resolve_policy_path("climate_map_v1.json")
```

### Issue 2: Duplicate relation_policy Files

**Locations:**
1. `/policy/relation_policy_v1.json` (version: relation_policy_v1)
2. `/saju_codex_batch_all_v2_6_signed/policies/relation_policy.json` (no version)

**Impact:** Policy loader will prefer `/policy/relation_policy_v1.json` first

**Action Required:** Verify which file is actually being used and consolidate

---

## Recommendations

### 1. Update All Engines to Use Policy Loader

**Files to update:**
- ✅ `strength.py` - Uses `from_files()` (GOOD)
- ✅ `relations.py` - Uses `from_file()` (GOOD)
- ❌ `climate.py` - **NEEDS UPDATE** to use policy_loader
- ✅ `yongshin_selector.py` - Uses manual path resolution (WORKING)
- ✅ `luck.py` - Uses policy_loader via `resolve_policy_path()` (GOOD)
- ✅ `korean_enricher.py` - Uses `from_files()` (GOOD)
- ✅ `school.py` - Uses hardcoded path (WORKING)
- ✅ `recommendation.py` - Uses `from_file()` (GOOD)

### 2. Consolidate Duplicate Policies

- Compare `relation_policy.json` vs `relation_policy_v1.json`
- Determine canonical version
- Update engines to use canonical version

### 3. Migrate Legacy Policies to Canonical Location

**Candidates for migration:**
- `climate_map_v1.json` → `/policy/climate_map_v1.json`
- `luck_policy_v1.json` → `/policy/luck_policy_v1.json` (if not redundant with luck_flow_policy_v1.json)
- `structure_rules_v1.json` → `/policy/structure_rules_v1.json`
- `text_guard_policy_v1.json` → `/policy/text_guard_policy_v1.json`

---

## Policy Loader Configuration

**File:** `services/common/policy_loader.py`

**Search Order:**
1. `POLICY_DIR` environment variable (if set)
2. `{PROJECT_ROOT}/policy/` (CANONICAL)
3. Legacy directories (fallback):
   - `saju_codex_addendum_v2/policies`
   - `saju_codex_addendum_v2_1/policies`
   - `saju_codex_blueprint_v2_6_SIGNED/policies`
   - `saju_codex_v2_5_bundle/policies`
   - `saju_codex_batch_all_v2_6_signed/policies`

**Functions:**
- `resolve_policy_path(filename)` - Returns Path object to policy file
- `load_policy_json(filename)` - Loads and returns JSON data
- `search_candidates(filename)` - Returns list of candidate paths

---

## Action Plan

### Immediate (Required for Orchestrator)

1. ✅ **Verify policy_loader is working** - COMPLETE
2. ❌ **Update climate.py to use policy_loader** - IN PROGRESS
3. ⏳ **Test orchestrator with corrected paths** - PENDING
4. ⏳ **Verify all engines load correct policies** - PENDING

### Short-term (This Week)

1. Audit all hardcoded policy paths in engine files
2. Migrate to policy_loader consistently
3. Add policy version logging to orchestrator init
4. Document which policies are required for each engine

### Long-term (Next Sprint)

1. Consolidate duplicate policies
2. Migrate legacy policies to `/policy/`
3. Version all policy files consistently
4. Add policy schema validation

---

## Conclusion

**Current State:** Policy resolution is **working via policy_loader**, but some engines (climate.py) use hardcoded paths

**Required Fix:** Update climate.py to use `resolve_policy_path("climate_map_v1.json")`

**Policy Directory Strategy:**
- **`/policy/`** - Canonical location for new policies (Stage-3, LLM Guard, Meta-engines)
- **`/saju_codex_batch_all_v2_6_signed/policies/`** - Core engine policies (strength, relations, shensha, etc.)
- **`/saju_codex_addendum_v2/policies/`** - Legacy policies (climate, luck, structure)

**Policy Loader Status:** ✅ **WORKING CORRECTLY** - No changes needed

---

**Audited by:** Claude Code
**Date:** 2025-10-10 KST
**Next Review:** After orchestrator integration complete
