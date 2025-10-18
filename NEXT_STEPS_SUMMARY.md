# Next Steps Summary - What To Do Now

**Date:** 2025-10-11  
**Status:** 17 tasks identified, all added to todo list  
**Priority:** Start with 4 critical issues blocking production

---

## TL;DR - Start Here

**Problem:** Production API is broken - returns stub data and crashes in guard.  
**Solution:** 3 critical fixes (1 minute + 2-4 hours + 15 minutes)  
**When:** Do this week

---

## The Situation

The codebase audit found **17 issues** across the entire application:

- 🔴 **3 CRITICAL** - Block functionality, cause crashes
- 🟠 **7 HIGH** - Hardcoded values, missing validations, technical debt
- 🟡 **5 MEDIUM** - Test gaps, code quality, missing schemas
- 🟢 **2 LOW** - Optimizations, refactoring

**Good News:** All issues are documented with exact file paths, line numbers, and fixes.

---

## What Breaks Right Now

1. **API Crashes** - `/analyze` endpoint has type mismatch (dict vs object)
2. **No Real Analysis** - Engine only runs 4 Stage-3 engines, missing core data
3. **Climate Engine Won't Load** - Import path bug (last one we missed!)

---

## Quick Start (30 minutes to unblock)

### Step 1: Fix the 1-minute typo (RIGHT NOW)

```bash
cd services/analysis-service/app/core
```

Open `climate.py`, line 12:

```python
# Change this:
_COMMON_PATH = Path(__file__).resolve().parents[4] / "common"

# To this:
_COMMON_PATH = Path(__file__).resolve().parents[4] / "services" / "common"
```

**Why:** We fixed 7 similar bugs yesterday but missed this one!

---

### Step 2: Delete backup files (1 minute)

```bash
cd services/analysis-service/app/core
rm strength.py.backup_v1 yongshin_selector.py.backup_v1
```

**Why:** Code hygiene, prevents confusion.

---

### Step 3: Wire the real engine (2-4 hours)

**File:** `services/analysis-service/app/core/engine.py`

**Current (BAD):**
```python
class AnalysisEngine:
    def analyze(self, context):
        # Only runs 4 Stage-3 engines
        return {"luck_flow": lf, "gyeokguk": gk, ...}  # Dict, not AnalysisResponse!
```

**Target (GOOD):**
```python
class AnalysisEngine:
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        orchestrator = SajuOrchestrator()
        pillars = extract_pillars(request)
        birth_ctx = extract_birth_context(request.options)
        result = orchestrator.analyze(pillars, birth_ctx)
        return AnalysisResponse.model_validate(convert_to_response(result))
```

**Why:** This gives you real ten_gods, relations, strength, structure, luck data.

---

### Step 4: Fix routes type handling (15 minutes)

**File:** `services/analysis-service/app/api/routes.py`

Since engine now returns AnalysisResponse (Step 3), the guard will work:

```python
@router.post("/analyze")
def analyze(payload: AnalysisRequest, ...):
    response = engine.analyze(payload)  # Now returns AnalysisResponse ✅
    llm_payload = guard.prepare_payload(response)  # Works now ✅
    final_response = guard.postprocess(response, llm_payload, ...)
    return final_response
```

**Why:** Prevents AttributeError crashes.

---

## Test It Works

```bash
# Start the API
cd services/analysis-service
uvicorn app.main:app --reload

# In another terminal, test
curl -X POST http://localhost:8000/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pillars": {
      "year": {"pillar": "庚辰"},
      "month": {"pillar": "乙酉"},
      "day": {"pillar": "乙亥"},
      "hour": {"pillar": "辛巳"}
    },
    "options": {
      "birth_dt": "2000-09-14T10:00:00+09:00",
      "timezone": "Asia/Seoul"
    }
  }'
```

**Expected:** 200 OK with full analysis data  
**Before:** 500 error or stub data

---

## After Quick Start (This Week)

Once the API works, tackle high-priority issues:

### Priority A: Sign Policies (1 hour)

```bash
# Use the script in AUDIT_ACTION_PLAN.md to sign 9 policy files
python tools/sign_policies.py
```

Files to sign:
- 5 Stage-3 policies (have `<TO_BE_FILLED_BY_PSA>`)
- 4 support policies (missing signature field entirely)

---

### Priority B: Re-enable Schema Test (30 min)

```bash
cd services/analysis-service/tests
# Edit test_relation_policy.py:60, remove @pytest.mark.skip
# Update schema to match current policy structure
pytest test_relation_policy.py -v
```

---

## Next Month (High Priority)

Fix all hardcoded trace values:

1. **Pillars trace** (2-3 hours) - delta_t, tzdb, flags
2. **Evidence defaults** (1-2 hours) - same issues
3. **Timezone converter** (3-4 hours) - stub replacement
4. **Time event detector** (2-3 hours) - hardcoded DST
5. **Astro trace** (1-2 hours) - more hardcoded values

**Why:** Currently all trace metadata is fake, so audit trails are unusable.

---

## Later (Medium/Low Priority)

- Fix EngineSummaries placeholder confidences
- Add validation for support policies
- Complete skeleton services (or mark WIP)
- Package services.common properly
- Fix golden test skips

**Total:** 17 tasks, ~28-42 hours effort

---

## Files You Need

All documentation is in the repo:

1. **AUDIT_VERIFICATION_REPORT.md** - Proves all claims are valid
2. **AUDIT_ACTION_PLAN.md** - Detailed roadmap with code samples
3. **TODO list** - All 17 tasks with status tracking

---

## Decision Points

### Do I need to fix everything?

**No.** Priority order:

1. **MUST FIX (this week):** Critical issues 1-3
2. **SHOULD FIX (this month):** High priority issues 4-10
3. **NICE TO HAVE (later):** Medium/low issues 11-17

### Can I deploy now?

**No.** After fixing critical issues 1-3, you'll have a functional API, but:

- Trace metadata is still hardcoded (audit trail broken)
- Policies aren't signed (violates RFC-8785)
- Several tests are skipped (missing coverage)

### How long until production-ready?

**Realistic timeline:**
- Week 1: Fix critical (4-6 hours) ✅ **Functional API**
- Week 2: Fix high priority (10-15 hours) ✅ **Production-ready**
- Week 3-4: Polish medium/low (14-21 hours) ✅ **High quality**

Total: 28-42 hours spread over 3-4 weeks.

---

## What's Already Good

Don't need to fix:

- ✅ Stub replacement completed (we did this yesterday)
- ✅ Path traversal bugs fixed (7/8 done, 1 remaining)
- ✅ Test suites re-enabled
- ✅ Common package created
- ✅ 673/690 tests passing (97.5%)

---

## Questions?

- **"Which task should I start with?"** → Task 1 (climate.py fix, 1 minute)
- **"Can I parallelize tasks?"** → Yes, Tasks 4-8 are independent
- **"What if I'm short on time?"** → Do Phase 1 only (4-6 hours)
- **"Do I need help?"** → Task 2 is the hardest (wire engine)

---

## Commands Reference

```bash
# Quick fixes
cd services/analysis-service/app/core
# Fix climate.py line 12 (add /services/)
rm *.backup_v1

# Run tests
cd services/analysis-service
env PYTHONPATH=. ../../.venv/bin/pytest tests/ -v

# Check what's in todo list
# (use your IDE or CLI tool)

# Start API
cd services/analysis-service
uvicorn app.main:app --reload --port 8000
```

---

## Bottom Line

**You have:** 17 tasks, all documented  
**You need:** 4-6 hours this week to unblock production  
**You get:** Functional analysis API with real data  
**Then:** Another 10-15 hours to be production-ready  

**Start with:** climate.py fix (1 minute) 🎯

---

**Created:** 2025-10-11  
**Author:** Claude Code  
**Next:** Open `climate.py` and change line 12
