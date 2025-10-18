# Orchestrator Integration Blockers Report

**Date:** 2025-10-10
**Status:** BLOCKED - Critical dependency mismatch found

---

## Summary

Master Orchestrator v1.1 integration is **95% complete** but blocked by a critical dependency issue in `LuckCalculator`.

**What Works:**
- ✅ Orchestrator file copied and syntax fixed
- ✅ Tests passing (1/1) with dependency injection
- ✅ Policy loader working correctly
- ✅ Climate.py updated to use policy_loader
- ✅ All engine factory methods corrected (from_file/from_files/load)

**What's Blocked:**
- ❌ Real engine initialization - LuckCalculator incompatible with saju_common

---

## Critical Blocker: LuckCalculator Dependency Mismatch

### Issue

**File:** `services/analysis-service/app/core/luck.py:39`

```python
self._term_loader = SimpleSolarTermLoader(TERM_DATA_PATH)  # Line 39
```

**Error:**
```
TypeError: TableSolarTermLoader.__init__() takes exactly one argument (the instance to initialize)
```

### Root Cause

`luck.py` expects a file-based SolarTermLoader with these methods:
- `__init__(data_path: Path)` - Accept data directory path
- `load_year(year: int)` - Load solar terms for specific year from CSV files

**But** `saju_common.TableSolarTermLoader` provides:
- `__init__()` - No arguments (Protocol-based)
- `month_branch(date)` - Simple Gregorian month mapping
- `season(date)` - Seasonal mapping

### Evidence

**luck.py expects** (lines 46-48):
```python
terms = list(self._term_loader.load_year(year)) + list(
    self._term_loader.load_year(year + 1)
)
next_term = next((entry for entry in terms if entry.utc_time > birth_utc), None)
```

**This requires:**
1. `load_year()` method (NOT in saju_common)
2. Returns iterable of objects with `utc_time` attribute
3. Loads from CSV files in `/data/` directory

**saju_common.TableSolarTermLoader provides:**
```python
def month_branch(self, d: date) -> str:
    """Get Earth Branch for date's month using Gregorian approximation."""
    return GREGORIAN_MONTH_TO_BRANCH[d.month]

def season(self, d: date) -> str:
    """Get season for date using month branch."""
    branch = self.month_branch(d)
    return BRANCH_TO_SEASON[branch]
```

### Impact

**Cannot initialize MasterOrchestrator** because:
1. `LuckCalculator()` constructor fails
2. No alternative SolarTermLoader available in codebase
3. CSV solar term data exists in `/data/terms_*.csv` but no loader for it

---

## Solutions (3 Options)

### Option 1: Create FileSolarTermLoader (RECOMMENDED)

**Pros:**
- Preserves existing luck.py logic
- Uses actual solar term data (accurate)
- Matches original design intent

**Cons:**
- Requires implementing new loader class
- More code to maintain

**Implementation:**
```python
# services/common/saju_common/solar_term_loader.py
class FileSolarTermLoader(SolarTermLoader):
    """Loads solar terms from CSV files in data/ directory"""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def load_year(self, year: int) -> List[SolarTermEntry]:
        csv_file = self.data_path / f"terms_{year}.csv"
        # Parse CSV and return SolarTermEntry objects
        ...
```

**Effort:** ~2 hours

### Option 2: Simplify LuckCalculator

**Pros:**
- Quick fix
- Uses existing saju_common
- No new dependencies

**Cons:**
- Less accurate (Gregorian approximation vs. actual solar terms)
- Loses precision for luck start age calculation

**Implementation:**
Rewrite `compute_start_age()` to use month_branch() instead of load_year()

**Effort:** ~30 minutes

### Option 3: Use astro-service (BEST LONG-TERM)

**Pros:**
- Astronomically precise
- Separates concerns properly
- Already exists in architecture

**Cons:**
- Requires inter-service communication
- More complex integration
- Orchestrator now depends on astro-service

**Implementation:**
Make LuckCalculator call astro-service API for solar term data

**Effort:** ~4 hours

---

## Recommended Path Forward

### Immediate (Today)

**Option 1: Create FileSolarTermLoader**

1. Create `services/common/saju_common/file_solar_term_loader.py`
2. Implement CSV parser for `/data/terms_*.csv` files
3. Export from `saju_common/__init__.py`
4. Update `luck.py` to use `FileSolarTermLoader`
5. Test orchestrator

**Estimated time:** 2-3 hours

### Short-term (This Week)

- Verify all engines work with real orchestrator
- Run golden case tests
- Document engine initialization patterns

### Long-term (Next Sprint)

- Migrate LuckCalculator to use astro-service API
- Remove CSV file dependency
- Improve solar term precision

---

## Additional Findings

### 1. Policy Resolution Working ✅

After audit, confirmed:
- Policy loader searches correctly: `policy/` → legacy dirs
- All policies resolved to correct locations
- climate.py now uses policy_loader (fixed today)

### 2. Engine Factory Methods Corrected ✅

Fixed all factory method calls in master_orchestrator_real.py:
- `StrengthEvaluator.from_files()` ✅
- `RelationTransformer.from_file()` ✅
- `ClimateEvaluator.from_file()` ✅
- `YongshinSelector()` ✅ (no factory)
- `LuckCalculator()` ❌ (BLOCKED)
- `KoreanLabelEnricher.from_files()` ✅
- `SchoolProfileManager.load()` ✅
- `RecommendationGuard.from_file()` ✅

### 3. Test Status

**Unit tests:** ✅ 1/1 passing (with dependency injection)
**Integration test:** ❌ Blocked by LuckCalculator

---

## Files Modified Today

1. ✅ `services/analysis-service/app/core/master_orchestrator_real.py`
   - Fixed escaped docstring (line 25-27)
   - Updated all factory methods (lines 39-46)

2. ✅ `services/analysis-service/tests/test_master_orchestrator_real.py`
   - Fixed import (line 2): `from app.core.master_orchestrator_real`

3. ✅ `services/analysis-service/app/core/climate.py`
   - Replaced hardcoded path with policy_loader (lines 11-19)

4. ✅ `.github/workflows/orchestrator_real_ci.yml`
   - Copied from bundle

5. ✅ `POLICY_AUDIT_AND_RESOLUTION.md` (NEW)
   - Comprehensive policy audit report

6. ✅ `ORCHESTRATOR_INTEGRATION_BLOCKERS.md` (NEW - THIS FILE)
   - Blocker documentation

---

## Next Steps

**User Decision Required:**

Which solution should we implement?
1. **FileSolarTermLoader** (2-3 hours, accurate)
2. **Simplify LuckCalculator** (30 min, less accurate)
3. **Use astro-service** (4 hours, best long-term)

Once decided, I can implement immediately.

---

**Reported by:** Claude Code
**Date:** 2025-10-10 21:50 KST
**Severity:** BLOCKER
**Priority:** P0 (blocks all orchestrator usage)
