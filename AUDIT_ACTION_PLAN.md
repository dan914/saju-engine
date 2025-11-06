# Audit Action Plan - Complete Task Roadmap

**Date:** 2025-10-11
**Source:** Codebase Audit v2.0 + Verification Report
**Total Tasks:** 17 issues
**Status:** All tasks added to todo list, organized by priority

---

## Quick Stats

### By Severity:
- 🔴 **Critical:** 3 tasks (blocks functionality)
- 🟠 **High:** 7 tasks (technical debt causing issues)
- 🟡 **Medium:** 5 tasks (code quality/testing)
- 🟢 **Low:** 2 tasks (optimizations)

### By Estimated Effort:
- **Quick wins (<30 min):** 4 tasks
- **Medium (1-4 hours):** 8 tasks
- **Large (4+ hours):** 5 tasks

### By Service:
- **analysis-service:** 6 tasks
- **pillars-service:** 2 tasks
- **tz-time-service:** 3 tasks
- **astro-service:** 1 task
- **policy/:** 2 tasks
- **tests/:** 2 tasks
- **cross-cutting:** 1 task

---

## Priority Roadmap

### Phase 1: Critical Blockers (Do This Week)

**Goal:** Unblock production API and fix crashes

#### 🔴 Task 1: Fix climate.py import path (1 minute)
- **File:** `services/analysis-service/app/core/climate.py:12`
- **Issue:** `parents[4] / "common"` goes outside repo
- **Fix:** Change to `parents[4] / "services" / "common"`
- **Blocker:** Yes - ClimateEvaluator cannot initialize
- **Effort:** 1 minute ⚡

```python
# Line 12: Change this
_COMMON_PATH = Path(__file__).resolve().parents[4] / "common"
# To this
_COMMON_PATH = Path(__file__).resolve().parents[4] / "services" / "common"
```

---

#### 🔴 Task 2: Wire real AnalysisEngine (2-4 hours)
- **File:** `services/analysis-service/app/core/engine.py:14-26`
- **Issue:** Only runs 4 Stage-3 engines, returns dict with incomplete data
- **Missing:** ten_gods, relations, strength, structure, luck, shensha
- **Fix:** Integrate SajuOrchestrator to produce full AnalysisResponse
- **Blocker:** Yes - Production API unusable without core analysis
- **Effort:** 2-4 hours

**Sub-tasks:**
1. Import SajuOrchestrator
2. Extract birth context from request.options
3. Convert orchestrator output to AnalysisResponse format
4. Return AnalysisResponse object (not dict)

---

#### 🔴 Task 3: Fix guard pipeline type mismatch (15 minutes)
- **File:** `services/analysis-service/app/api/routes.py:35-40`
- **Issue:** Engine returns dict, guard expects AnalysisResponse object
- **Crash:** `AttributeError` when accessing `.model_dump()` or `.structure.primary`
- **Fix:** Ensure engine returns AnalysisResponse, or wrap dict
- **Blocker:** Yes - /analyze endpoint crashes
- **Effort:** 15 minutes
- **Dependency:** Must do after Task 2

```python
# Option A (preferred): Engine returns AnalysisResponse directly
response = engine.analyze(payload)  # Now returns AnalysisResponse

# Option B: Wrap dict if engine can't be changed immediately
response_dict = engine.analyze(payload)
response = AnalysisResponse.model_validate(response_dict)
```

---

### Phase 2: High Priority Technical Debt (This Month)

**Goal:** Fix hardcoded values, sign policies, restore validations

#### 🟠 Task 4: Remove hardcoded pillars trace (2-3 hours)
- **File:** `services/pillars-service/app/core/engine.py:31-39`
- **Issue:** Static delta_t=57.4, tzdb="2025a", all flags false
- **Fix:** Compute real values from TimeResolver, EvidenceBuilder
- **Impact:** Audit trail unusable, consumers cannot trust trace
- **Effort:** 2-3 hours

---

#### 🟠 Task 5: Fix EvidenceBuilder defaults (1-2 hours)
- **File:** `services/pillars-service/app/core/evidence.py:98-102`
- **Issue:** Default parameters hide real values
- **Fix:** Pass actual deltaT, tzdb, branch roots, combos from calculator
- **Effort:** 1-2 hours

---

#### 🟠 Task 6: Replace TimezoneConverter stub (3-4 hours)
- **File:** `services/tz-time-service/app/core/converter.py:1`
- **Issue:** Placeholder, returns delta_t=0.0, no metadata
- **Fix:** Implement real LMT adjustments, delta-T propagation, trace copy
- **Effort:** 3-4 hours

---

#### 🟠 Task 7: Fix TimeEventDetector hardcoded DST (2-3 hours)
- **File:** `services/tz-time-service/app/core/events.py:26`
- **Issue:** Always adds 1987-1988 DST for Seoul, ignores request year
- **Fix:** Gate events by request.instant window, expand dataset
- **Effort:** 2-3 hours

---

#### 🟠 Task 8: Remove hardcoded astro trace (1-2 hours)
- **File:** `services/astro-service/app/core/service.py:29`
- **Issue:** Fixed delta_t=57.4, tzdb="2025a", zero diffs
- **Fix:** Source delta-T from delta_t.py, emit real metadata
- **Effort:** 1-2 hours

---

#### 🟠 Task 9: Sign all policy files (1 hour)
- **Files:** 9 policies total
  - 5 Stage-3: climate_advice_policy_v1.json, gyeokguk_policy_v1.json, luck_flow_policy_v1.json, pattern_profiler_policy_v1.json, relation_policy_v1.json
  - 4 support: seasons_wang_map_v2.json, strength_grading_tiers_v1.json, yongshin_dual_policy_v1.json, zanggan_table.json
- **Issue:** `<TO_BE_FILLED_BY_PSA>` or missing signature fields
- **Fix:** Canonicalize with RFC-8785, compute SHA-256, replace placeholders
- **Impact:** Violates stated security model
- **Effort:** 1 hour

**Script to help:**
```python
from canonicaljson import encode_canonical_json
import hashlib
import json

def sign_policy(policy_file):
    with open(policy_file) as f:
        data = json.load(f)
    
    # Remove signature if present
    data_copy = {k: v for k, v in data.items() if k != "policy_signature"}
    
    # Canonicalize and hash
    canonical = encode_canonical_json(data_copy)
    sha256 = hashlib.sha256(canonical).hexdigest()
    
    # Update
    data["policy_signature"] = sha256
    
    with open(policy_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Signed: {policy_file} -> {sha256}")
```

---

#### 🟠 Task 10: Re-enable relation schema test (30 minutes)
- **File:** `services/analysis-service/tests/test_relation_policy.py:60`
- **Issue:** `@pytest.mark.skip` bypasses schema validation
- **Fix:** Update relation.schema.json, remove skip decorator
- **Impact:** Policy regressions go unnoticed
- **Effort:** 30 minutes

---

### Phase 3: Medium Priority Quality Issues (Next Month)

**Goal:** Improve test coverage, clean up code, add validations

#### 🟡 Task 11: Fix EngineSummaries placeholder confidences (1-2 hours)
- **File:** `services/analysis-service/app/core/engine_summaries.py:148`
- **Issue:** Hard-coded confidence=0.8/0.75, impact_weight=0.7
- **Fix:** Calculate from strength/yongshin, pull from policy
- **Impact:** LLM Guard decisions unreliable
- **Effort:** 1-2 hours

---

#### 🟡 Task 12: Fix Stage-3 golden test skips (2-3 hours)
- **File:** `tests/test_stage3_golden_cases.py:54/69/86/102`
- **Issue:** Multiple pytest.skip() when expectations missing
- **Fix:** Populate expected keys or separate test cases
- **Effort:** 2-3 hours

---

#### 🟡 Task 13: Delete backup files (1 minute) ⚡
- **Files:** 
  - `services/analysis-service/app/core/strength.py.backup_v1`
  - `services/analysis-service/app/core/yongshin_selector.py.backup_v1`
- **Issue:** 500+ line backups clutter production tree
- **Fix:** Delete or archive outside import path
- **Effort:** 1 minute

```bash
rm services/analysis-service/app/core/*.backup_v1
```

---

#### 🟡 Task 14: Add validation for 4 support policies (3-4 hours)
- **Files:** 
  - `policy/seasons_wang_map_v2.json`
  - `policy/strength_grading_tiers_v1.json`
  - `policy/yongshin_dual_policy_v1.json`
  - `policy/zanggan_table.json`
- **Issue:** No JSON Schema, no tests, no signatures
- **Fix:** Author schemas, add unit tests, sign policies
- **Effort:** 3-4 hours

---

#### 🟡 Task 15: Complete skeleton services (4-6 hours or mark WIP)
- **Files:**
  - `services/api-gateway/app/main.py`
  - `services/llm-polish/app/main.py`
  - `services/llm-checker/app/main.py`
- **Issue:** Only health metadata, no routing/tests
- **Fix Options:**
  - A) Mark as WIP in deployment (1 minute)
  - B) Implement minimal routes + tests (4-6 hours)
- **Effort:** 4-6 hours or 1 minute (depending on approach)

---

### Phase 4: Low Priority Optimizations (Next Quarter)

**Goal:** Long-term refactoring and improvements

#### 🟢 Task 16: Package services.common properly (2-3 hours)
- **File:** Multiple (relations.py:13, etc.)
- **Issue:** Repeated `sys.path.insert()` indicates packaging debt
- **Fix:** Install services.common as real package, remove path hacks
- **Effort:** 2-3 hours (affects multiple files)

---

#### 🟢 Task 17: Fix hardcoded tzdb_version (30 minutes)
- **File:** `services/tz-time-service/app/api/routes.py:22`
- **Issue:** TimezoneConverter factory hard-codes "2025a"
- **Fix:** Pull from config or tzdata introspection
- **Effort:** 30 minutes

---

## Suggested Sprint Plan

### Sprint 1 (This Week - 4-6 hours total):

**Day 1 (2 hours):**
- ✅ Task 1: Fix climate.py path (1 min)
- ✅ Task 13: Delete backups (1 min)
- ✅ Task 2: Wire AnalysisEngine (2-4 hours)

**Day 2 (30 min):**
- ✅ Task 3: Fix guard pipeline (15 min)
- ✅ Test /analyze endpoint works

**Day 3 (2 hours):**
- ✅ Task 9: Sign all policies (1 hour)
- ✅ Task 10: Re-enable schema test (30 min)
- ✅ Run full test suite

---

### Sprint 2 (Next Week - 8-12 hours):

**Focus:** Hardcoded trace values

- ✅ Task 4: Pillars trace (2-3 hours)
- ✅ Task 5: EvidenceBuilder (1-2 hours)
- ✅ Task 8: Astro trace (1-2 hours)
- ✅ Task 6: TimezoneConverter (3-4 hours)
- ✅ Task 7: TimeEventDetector (2-3 hours)

---

### Sprint 3 (This Month - 6-9 hours):

**Focus:** Testing and quality

- ✅ Task 11: EngineSummaries confidence (1-2 hours)
- ✅ Task 12: Golden test skips (2-3 hours)
- ✅ Task 14: Support policy validation (3-4 hours)

---

### Sprint 4 (Next Quarter - 7-10 hours):

**Focus:** Services and refactoring

- ✅ Task 15: Skeleton services (4-6 hours or mark WIP)
- ✅ Task 16: Package common properly (2-3 hours)
- ✅ Task 17: tzdb_version config (30 min)

---

## Quick Wins (Do First)

These can be done in <30 minutes and provide immediate value:

1. ⚡ Fix climate.py path (1 min) - **CRITICAL**
2. ⚡ Delete backup files (1 min) - **MEDIUM**
3. ⚡ Fix guard pipeline type (15 min) - **CRITICAL** (after Task 2)
4. ⚡ Re-enable schema test (30 min) - **HIGH**

---

## Dependencies

```
Task 3 (guard fix) → depends on → Task 2 (engine wire)
Task 9 (sign policies) → should do before → Task 14 (support policy validation)
Task 4,5,6,7,8 (trace fixes) → can be done in parallel
```

---

## Testing Strategy

After each phase, run:

```bash
# Phase 1 tests
cd services/analysis-service
env PYTHONPATH=. ../../.venv/bin/pytest tests/test_analyze.py -v

# Phase 2 tests
cd services/pillars-service
PYTHONPATH=".:../common" pytest tests/ -v

cd services/tz-time-service
pytest tests/ -v

# Full suite
cd <repo-root>
./scripts/run_all_tests.sh
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] /analyze endpoint returns 200 without crashing
- [ ] AnalysisResponse includes all required fields
- [ ] ClimateEvaluator loads successfully

### Phase 2 Complete When:
- [ ] All trace metadata reflects real computed values
- [ ] All 9 policies have valid RFC-8785 signatures
- [ ] Relation schema test passes (not skipped)

### Phase 3 Complete When:
- [ ] No backup files in production tree
- [ ] All support policies have schemas and tests
- [ ] EngineSummaries uses real confidence calculations

### Phase 4 Complete When:
- [ ] No sys.path.insert() hacks remain
- [ ] All services have functional routes or marked WIP
- [ ] Config drives all version numbers

---

## Risk Assessment

### High Risk (Could Break Things):
- Task 2 (wire engine) - touches API contract
- Task 4-8 (trace fixes) - changes output format
- Task 16 (package refactor) - affects all imports

### Low Risk (Safe Changes):
- Task 1, 13 (file edits/deletes)
- Task 9 (add signatures)
- Task 10 (enable test)
- Task 17 (config change)

---

## Estimated Total Effort

- **Phase 1 (Critical):** 4-6 hours
- **Phase 2 (High):** 10-15 hours
- **Phase 3 (Medium):** 7-11 hours
- **Phase 4 (Low):** 7-10 hours

**Grand Total:** 28-42 hours (roughly 1 week of focused work)

---

## Notes

- All 17 tasks have been added to the todo list
- Tasks are marked with emoji indicators (🔴🟠🟡🟢)
- Start with Phase 1 critical blockers this week
- Can parallelize Phase 2 tasks across team members
- Phase 4 can be deferred if timeline is tight

---

**Created:** 2025-10-11  
**Updated:** 2025-10-11  
**Status:** Ready for execution  
**Next Step:** Start with Task 1 (climate.py fix - 1 minute)
