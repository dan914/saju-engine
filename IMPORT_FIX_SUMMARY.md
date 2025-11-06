# Import Fix Summary

**Date:** 2025-11-03
**Status:** ✅ RESOLVED
**Issue:** `ModuleNotFoundError: No module named 'app'` from repo root

---

## Problem

Running `poetry run python` from the repo root failed to import service modules:

```bash
poetry run python -c "from app.main import app"
# ModuleNotFoundError: No module named 'app'
```

This caused:
- ❌ Direct Python scripts to fail
- ❌ Tests to hang/timeout
- ❌ Requiring manual `PYTHONPATH` manipulation

## Root Cause

This is a **monorepo** with independent services in `services/*/`. Each service has its own `pyproject.toml` and `app/` package. These were not in Python's module search path when running from the repo root.

## Solution

Created a **`.pth` file** in the virtualenv that automatically adds all service directories to `sys.path`.

### Setup (one-time, after cloning)

```bash
poetry install --with dev
poetry run python scripts/setup_dev_environment.py
```

This creates `~/.cache/pypoetry/virtualenvs/.../site-packages/saju_services.pth` with paths to all services.

### Verification

```bash
# Test 1: Direct import
poetry run python -c "from app.main import app; print('✅ Works!')"

# Test 2: Health check
poetry run python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
print(client.get("/health").json())
PY

# Test 3: Pytest
poetry run pytest services/analysis-service/tests/test_health.py -v
```

All should work **without** `PYTHONPATH` manipulation.

## Files Changed

1. **Created:**
   - `scripts/setup_dev_environment.py` - Setup script to create .pth file
   - `docs/MONOREPO_IMPORT_FIX.md` - Detailed technical documentation
   - `sitecustomize.py` - (Not used, system one takes precedence)
   - `IMPORT_FIX_SUMMARY.md` - This file

2. **Modified:**
   - `README.md` - Added development environment setup section

3. **Generated (in virtualenv):**
   - `~/.cache/pypoetry/virtualenvs/saju-monorepo-*/lib/python3.*/site-packages/saju_services.pth`

## Technical Details

### Why .pth Files?

Python automatically loads `.pth` files from `site-packages` on startup. Each line in the file is added to `sys.path`. This is the standard Python mechanism for adding custom paths.

### .pth File Contents

```
/mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine/services/analysis-service
/mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine/services/api-gateway
/mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine/services/pillars-service
...
```

(Absolute paths to each service directory)

### Why Not Other Solutions?

| Solution | Why Not |
|----------|---------|
| `sitecustomize.py` | System-level one takes precedence |
| Editable installs | Poetry doesn't handle multiple editable packages well |
| `PYTHONPATH` env var | Must be set manually, easy to forget |
| **`.pth` file** ✅ | **Automatic, persistent, simple** |

## Maintenance

**Re-run setup when:**
- Adding new services
- Virtualenv is recreated (`poetry env remove python`)
- Poetry is upgraded (may recreate virtualenv)

**Command:**
```bash
poetry run python scripts/setup_dev_environment.py
```

## Impact

### Before
```bash
# ❌ Fails
poetry run python -c "from app.main import app"

# ❌ Hangs
poetry run pytest services/analysis-service/tests/

# ✅ Works (but annoying)
PYTHONPATH=services/analysis-service poetry run python -c "from app.main import app"
```

### After
```bash
# ✅ All work without PYTHONPATH
poetry run python -c "from app.main import app"
poetry run pytest services/analysis-service/tests/
poetry run python scripts/any_script.py
```

## Developer Experience

**What changed:**
- ✅ No more `PYTHONPATH` environment variable manipulation
- ✅ `poetry run python` works from repo root
- ✅ Tests run without hanging
- ✅ FastAPI TestClient works correctly

**What stays the same:**
- `pytest.ini` still configures paths (for pytest specifically)
- Individual services still have their own `pyproject.toml`
- Service isolation is maintained

## Next Steps

1. ✅ Setup script created
2. ✅ Documentation written
3. ✅ README updated
4. ✅ Verification complete
5. 📋 TODO: Add to CI/CD setup instructions
6. 📋 TODO: Document in team onboarding guide

## Questions?

See detailed documentation: `docs/MONOREPO_IMPORT_FIX.md`

---

**Verified:** 2025-11-03 23:30 KST
**Services tested:** analysis-service, api-gateway
**Python version:** 3.12.3
**Poetry version:** 1.x
