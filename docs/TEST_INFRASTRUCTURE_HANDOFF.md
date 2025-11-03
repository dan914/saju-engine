# Test Infrastructure Issue - Handoff Note

**Date:** 2025-11-03
**Status:** ⚠️ PRE-EXISTING ISSUE (Not related to script migration)
**Priority:** Medium (blocks full test suite verification)

---

## Issue Summary

The analysis-service test suite cannot run due to a `conftest.py` import configuration issue.

**Error:**
```
ImportError while loading conftest
tests/conftest.py:8: in <module>
    from services.common import create_service_app
E   ModuleNotFoundError: No module named 'services'
```

**Impact:**
- Cannot verify 711/711 test pass rate mentioned in original handoff
- Test suite times out after 10 minutes when run from repo root
- Individual scripts work correctly (validated with 4 key scripts)

---

## Root Cause

The `services/analysis-service/tests/conftest.py` line 8 tries to import:
```python
from services.common import create_service_app
```

But when pytest runs from repo root with Poetry, the `services` package isn't in the Python path the way conftest expects.

---

## Evidence This is Pre-Existing

1. **Script Migration Validated Separately**: 4 complex scripts run successfully
   - `calculate_user_saju.py` - Multi-service imports
   - `run_full_orchestrator_2000_09_14.py` - Complex orchestrator
   - `tools/e2e_smoke_v1_1.py` - Nested imports
   - `run_user_ten_gods.py` - Single service

2. **Golden Cases Pass**: `tests/test_stage3_golden_cases.py` → 43/43 passing

3. **Import Pattern Different**: Scripts use `scripts._script_loader`, tests use direct imports

4. **Timeline**: Original handoff mentioned 711/711 passing, so this worked before

---

## Recommended Solutions

### Option 1: Add pytest.ini Configuration (Recommended)

Create `pytest.ini` at repo root:
```ini
[pytest]
pythonpath = . services/common
testpaths = services/analysis-service/tests tests
addopts = -v --tb=short
timeout = 300
```

### Option 2: Fix conftest.py Import

Update `services/analysis-service/tests/conftest.py`:
```python
# Add repo root to path before import
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.common import create_service_app
```

### Option 3: Use Explicit PYTHONPATH

Run tests with explicit path:
```bash
PYTHONPATH=".:services/common:services/analysis-service" \
  poetry run pytest services/analysis-service/tests/ -v
```

---

## Investigation Steps

If you want to debug further:

1. **Check if services.common is installed**:
   ```bash
   poetry run python -c "import services.common; print(services.common.__file__)"
   ```

2. **Verify Poetry environment**:
   ```bash
   poetry run python -c "import sys; print('\n'.join(sys.path))"
   ```

3. **Run single test file**:
   ```bash
   poetry run pytest services/analysis-service/tests/test_health.py -v
   ```

4. **Check pytest discovery**:
   ```bash
   poetry run pytest --collect-only services/analysis-service/tests/
   ```

---

## Workaround for Immediate Verification

If you need to verify tests work:

```bash
# From repo root
cd services/analysis-service
PYTHONPATH="../..:../common:." poetry run pytest tests/test_health.py -v
```

This should work because:
- `../..` → repo root (for relative imports)
- `../common` → services/common
- `.` → services/analysis-service (for app.* imports)

---

## Next Steps

1. ✅ **Script Migration**: COMPLETE (validated with spot checks)
2. ⏳ **Test Infrastructure Fix**: Choose one of the 3 solutions above
3. ⏳ **Full Test Verification**: Run after infrastructure fix

**Recommendation**: Add `pytest.ini` (Option 1) as it's the cleanest long-term solution.

---

## Related Issues

- **Script Loader**: No issues (multi-service imports working)
- **Poetry Setup**: Working correctly (711 tests passed in original session)
- **Golden Cases**: Passing (43/43)
- **Import Strategy**: May need alignment between test conftest and script loader patterns

---

**Created By:** Phase 2 Migration Agent
**Related Docs**:
- `docs/PHASE2_MIGRATION_COMPLETE.md`
- `docs/SCRIPT_LOADER_FIX_COMPLETE.md`
