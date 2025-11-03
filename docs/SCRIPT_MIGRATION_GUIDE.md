# Script Migration Guide: sys.path → Poetry-based Imports

**Date:** 2025-11-03
**Status:** Active Migration
**Phase:** 2 - Package Hygiene
**Owner:** Backend Team

---

## Executive Summary

This guide documents the migration of all scripts from `sys.path.insert()` hacks to Poetry-based package imports. The migration eliminates manual path manipulation and enables proper package-based module resolution.

**Benefits:**
- ✅ Eliminates fragile `sys.path` hacks
- ✅ Enables IDE autocomplete and type checking
- ✅ Simplifies debugging and error messages
- ✅ Aligns with Python packaging best practices
- ✅ Makes scripts portable and testable

**Timeline:** Estimated 2-3 days for full migration

---

## Migration Strategy

### Phase 1: Helper Creation ✅ COMPLETE

Created `scripts/_script_loader.py` - A centralized loader module that provides clean imports from all services:
- `get_analysis_module()` - Load from analysis-service
- `get_pillars_module()` - Load from pillars-service
- `get_astro_module()` - Load from astro-service
- `get_tz_time_module()` - Load from tz-time-service
- `get_common_module()` - Load from services.common

### Phase 2: Pattern Documentation 🔄 IN PROGRESS

Document the migration pattern with examples.

### Phase 3: Batch Migration ⏳ PENDING

Update all scripts systematically:
1. `run_*.py` files (6 files) - High priority
2. `scripts/*.py` files (27 files) - Medium priority
3. `tools/*.py` files (1 file) - Low priority

### Phase 4: Verification ⏳ PENDING

Run scripts under Poetry to ensure they work.

---

## Migration Pattern

### Old Pattern (DON'T USE)

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Manual path manipulation (FRAGILE)
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))
sys.path.insert(0, str(repo_root / "services" / "pillars-service"))
sys.path.insert(0, str(repo_root / "services" / "common"))

# Now we can import
from app.core.engine import AnalysisEngine
from app.models import AnalysisRequest
```

**Problems:**
- ❌ Fragile - breaks if directory structure changes
- ❌ IDE doesn't understand imports
- ❌ Type checking fails
- ❌ Import order matters (conflicts)
- ❌ Error messages are confusing

### New Pattern (DO USE)

```python
#!/usr/bin/env python3
"""Script description.

Usage:
    poetry run python scripts/your_script.py
"""

# Use the script loader helper
from scripts._script_loader import get_analysis_module, get_pillars_module

# Load classes/functions explicitly
AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
AnalysisRequest = get_analysis_module("analysis", "AnalysisRequest")
PillarsEngine = get_pillars_module("engine", "PillarsEngine")

# Now use them normally
def main():
    engine = AnalysisEngine()
    # ...
```

**Benefits:**
- ✅ Explicit and clear
- ✅ Works with Poetry
- ✅ IDE autocomplete works
- ✅ Type checking works
- ✅ Clear error messages

---

## Service Module Maps

### Analysis Service (`services/analysis-service/app/`)

**Core Modules (`app.core.*`):**
- `engine` → `AnalysisEngine`
- `strength` → `StrengthEvaluator`
- `strength_v2` → `StrengthEvaluatorV2`
- `relations` → `RelationTransformer`
- `structure` → `StructureDetector`
- `luck` → `LuckCalculator`
- `school` → `SchoolProfileManager`
- `recommendation` → `RecommendationGuard`
- `void` → `VoidCalculator`
- `yuanjin` → `YuanjinDetector`
- `combination_element` → `CombinationElement`
- `yongshin_selector` → `YongshinSelector`, `YongshinSelectorV2`
- `climate` → `ClimateEvaluator`
- `relation_weight` → `RelationWeightEvaluator`
- `evidence_builder` → `EvidenceBuilder`
- `engine_summaries` → `EngineSummariesBuilder`
- `korean_enricher` → `KoreanLabelEnricher`
- `llm_guard` → `LLMGuard`
- `text_guard` → `TextGuard`
- `saju_orchestrator` → `SajuOrchestrator`

**Model Modules (`app.models.*`):**
- `analysis` → `AnalysisRequest`, `AnalysisResponse`, `AnalysisOptions`, `PillarInput`

**Example:**
```python
# Old way
sys.path.insert(0, "services/analysis-service")
from app.core.engine import AnalysisEngine

# New way
AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
```

### Pillars Service (`services/pillars-service/app/`)

**Core Modules (`app.core.*`):**
- `engine` → `PillarsEngine`
- `month` → month calculation functions
- `resolve` → resolution functions
- `input_validator` → validation functions

**Model Modules (`app.models.*`):**
- `pillars` → `PillarsComputeRequest`, `PillarComponent`, `FourPillarsResult`

**Example:**
```python
# Old way
sys.path.insert(0, "services/pillars-service")
from app.core.engine import PillarsEngine

# New way
PillarsEngine = get_pillars_module("engine", "PillarsEngine")
```

### Common Service (`services/common/`)

**Modules:**
- `saju_common.builtins` → `TEN_STEMS`, `TWELVE_BRANCHES`, `STEM_TO_ELEMENT`, `ELEMENT_GENERATES`
- `saju_common.interfaces` → Protocol definitions
- `saju_common.seasons` → Season mapping
- `saju_common.timezone_handler` → Timezone utilities

**Example:**
```python
# Old way
sys.path.insert(0, "services/common")
from saju_common.builtins import TEN_STEMS

# New way
TEN_STEMS = get_common_module("saju_common.builtins", "TEN_STEMS")

# Or use convenience function
from scripts._script_loader import load_saju_constants
TEN_STEMS, TWELVE_BRANCHES, STEM_TO_ELEMENT, ELEMENT_GENERATES = load_saju_constants()
```

---

## Convenience Functions

The script loader provides convenience functions for common imports:

```python
from scripts._script_loader import (
    load_analysis_engine,      # → AnalysisEngine
    load_analysis_models,       # → (AnalysisRequest, AnalysisResponse, AnalysisOptions, PillarInput)
    load_pillars_calculator,    # → calculate_four_pillars (if available in pillars-service)
    load_saju_constants,        # → (TEN_STEMS, TWELVE_BRANCHES, STEM_TO_ELEMENT, ELEMENT_GENERATES)
)

# Use them
AnalysisEngine = load_analysis_engine()
AnalysisRequest, AnalysisResponse, AnalysisOptions, PillarInput = load_analysis_models()
```

---

## Migration Checklist

For each script file:

- [ ] Remove all `sys.path.insert()` lines
- [ ] Remove all `from pathlib import Path` if only used for path manipulation
- [ ] Add `from scripts._script_loader import ...` at the top
- [ ] Replace `from app.X import Y` with `Y = get_*_module("X", "Y")`
- [ ] Add docstring with usage: `poetry run python scripts/...`
- [ ] Test: `poetry run python scripts/your_script.py`
- [ ] Commit changes

---

## Files to Migrate

### Priority 1: run_*.py (6 files) - Core workflow scripts

| File | Lines | Complexity | Owner |
|------|-------|------------|-------|
| `run_full_analysis_2000_09_14.py` | 80 | Medium | Backend |
| `run_full_orchestrator_2000_09_14.py` | 100 | Medium | Backend |
| `run_luck_pillars_integration.py` | 60 | Low | Backend |
| `run_orchestrator_1963_12_13.py` | 90 | Medium | Backend |
| `run_user_ten_gods.py` | 50 | Low | Backend |
| `run_task7_fix.py` | 70 | Low | Backend |

**Estimated Time:** 2-3 hours

### Priority 2: scripts/*.py (27 files) - Utility scripts

| File | Lines | Complexity | Owner |
|------|-------|------------|-------|
| `scripts/probe_analysis.py` | 150 | Medium | Platform |
| `scripts/calculate_pillars_traditional.py` | 200 | High | Backend |
| `scripts/compare_elements_unweighted.py` | 100 | Low | Backend |
| `scripts/analyze_2000_09_14.py` | 120 | Medium | Backend |
| `scripts/analyze_2000_09_14_corrected.py` | 140 | Medium | Backend |
| `scripts/calculate_user_saju.py` | 230 | High | Backend |
| *(21 more files)* | - | - | - |

**Estimated Time:** 4-6 hours

**Special Cases:**
- `calculate_pillars_traditional.py` - Standalone, may need to become a proper service function
- Debug/test scripts - Low priority, can migrate last

### Priority 3: tools/*.py (1 file) - Build tools

| File | Lines | Complexity | Owner |
|------|-------|------------|-------|
| `tools/e2e_smoke_v1_1.py` | 200 | Medium | QA |

**Estimated Time:** 30 minutes

### Service conftest.py files (3 files) - Already handled ✅

These were updated during Phase 1:
- `services/analysis-service/tests/conftest.py` - ✅ Uses test loader pattern
- `services/astro-service/tests/conftest.py` - ⚠️ Still has sys.path
- `services/common/tests/test_saju_common.py` - ⚠️ Still has sys.path

**Estimated Time:** 1 hour

---

## Testing Strategy

### 1. Unit Testing Each Script

```bash
# Test individual script
poetry run python scripts/your_script.py

# If it has command-line args
poetry run python scripts/your_script.py --arg value
```

### 2. Integration Testing

```bash
# Run full analysis pipeline
poetry run python run_full_analysis_2000_09_14.py

# Run orchestrator
poetry run python run_full_orchestrator_2000_09_14.py
```

### 3. CI/CD Validation

Update workflows to use `poetry run`:

```yaml
# .github/workflows/scripts-test.yml
jobs:
  test-scripts:
    steps:
      - name: Install Poetry
        run: pipx install poetry

      - name: Install dependencies
        run: poetry install

      - name: Test key scripts
        run: |
          poetry run python run_full_analysis_2000_09_14.py
          poetry run python scripts/calculate_user_saju.py
```

---

## Common Pitfalls

### 1. Module Name Mismatch

**Problem:**
```python
# Trying to load from wrong module
PillarsEngine = get_pillars_module("pillars", "PillarsEngine")  # ❌ WRONG
```

**Solution:**
```python
# Check the actual module structure
PillarsEngine = get_pillars_module("engine", "PillarsEngine")  # ✅ CORRECT
```

### 2. Missing __init__.py

If imports fail, check that all directories have `__init__.py`:
```bash
find services -type d -exec test ! -e {}/__init__.py \; -print
```

### 3. Circular Imports

The loader may expose circular import issues that were hidden by path hacks.

**Solution:** Refactor to remove circular dependencies or use lazy imports.

### 4. Poetry Environment Not Active

**Problem:**
```bash
$ python scripts/your_script.py
ImportError: No module named 'scripts'
```

**Solution:**
```bash
# Always use poetry run
$ poetry run python scripts/your_script.py
```

---

## Progress Tracking

### Completed ✅

- [x] Created `scripts/_script_loader.py`
- [x] Documented migration pattern
- [x] Updated `tests/_analysis_loader.py` (test helper)
- [x] Updated `scripts/calculate_user_saju.py` (example)

### In Progress 🔄

- [ ] Documenting service module maps
- [ ] Creating migration tool/script

### Pending ⏳

- [ ] Migrate 6 `run_*.py` files
- [ ] Migrate 27 `scripts/*.py` files
- [ ] Migrate 1 `tools/*.py` file
- [ ] Update 3 service `conftest.py` files
- [ ] Update CI/CD workflows

---

## Rollback Plan

If migration causes issues:

1. **Immediate Rollback:** Revert commits
2. **Partial Rollback:** Keep loader, revert specific scripts
3. **Debugging:** Run with `PYTHONPATH=. poetry run python ...`

---

## Next Steps

1. **Complete Documentation** ← YOU ARE HERE
2. **Migrate Priority 1 Files** (run_*.py)
3. **Test Integration**
4. **Migrate Priority 2 Files** (scripts/*.py)
5. **Migrate Priority 3 Files** (tools/*.py)
6. **Update CI/CD**
7. **Remove Legacy sys.path Code**

---

## References

- **ADR:** `docs/adr/0001-services-common-packaging.md`
- **Poetry Strategy:** `docs/poetry-migration-strategy.md`
- **Phase Plan:** `grand audit/phase1_corrected_status.md`
- **Test Pattern:** `tests/_analysis_loader.py`
- **Script Loader:** `scripts/_script_loader.py`

---

**Last Updated:** 2025-11-03
**Next Review:** 2025-11-10
**Status:** Active - Phase 2 Migration
