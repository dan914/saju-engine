# Monorepo Import Fix Documentation

**Date:** 2025-11-03
**Issue:** `ModuleNotFoundError: No module named 'app'` when running `poetry run python` from repo root
**Status:** ✅ RESOLVED

## Problem Description

The saju-engine project is a **monorepo** with multiple independent services:

```
services/
├── analysis-service/
│   ├── app/
│   │   └── main.py
│   └── pyproject.toml
├── api-gateway/
│   ├── app/
│   │   └── main.py
│   └── pyproject.toml
└── ... (other services)
```

Each service has its own `pyproject.toml` and is an independent package. When running `poetry run python` from the **repo root**, Python cannot find the service modules because they are not in `sys.path`.

### Symptoms

1. **Direct Python execution fails:**
   ```bash
   poetry run python -c "from app.main import app"
   # ModuleNotFoundError: No module named 'app'
   ```

2. **Tests hang/timeout:**
   ```bash
   poetry run pytest services/analysis-service/tests/test_health.py
   # Hangs during import
   ```

3. **Manual PYTHONPATH required:**
   ```bash
   PYTHONPATH=services/analysis-service poetry run python -c "from app.main import app"
   # Works, but annoying
   ```

## Root Cause

Python's module resolution doesn't automatically add subdirectories to `sys.path`. While `pytest.ini` configures `pythonpath` for pytest, this doesn't affect `poetry run python`.

The services are **not installed as packages** in the Poetry virtualenv, so they're not discoverable.

## Solution: .pth File

Created a **`.pth` file** in the virtualenv's `site-packages` directory that automatically adds all service paths to `sys.path`.

### How .pth Files Work

1. Python automatically reads all `.pth` files in `site-packages` on startup
2. Each line in a `.pth` file is added to `sys.path`
3. This happens **before** any user code runs

### Implementation

**File:** `scripts/setup_dev_environment.py`

```python
#!/usr/bin/env python3
"""Setup .pth file for monorepo service imports."""

import site
from pathlib import Path

def main() -> None:
    repo_root = Path(__file__).parent.parent.resolve()
    site_packages = Path(site.getsitepackages()[0])

    service_dirs = [
        "services/analysis-service",
        "services/api-gateway",
        "services/pillars-service",
        # ... etc
    ]

    pth_content = "\n".join(
        str(repo_root / service_dir) for service_dir in service_dirs
    )

    pth_file = site_packages / "saju_services.pth"
    pth_file.write_text(pth_content, encoding="utf-8")
    print(f"✅ Created {pth_file}")
```

### Setup Instructions

**One-time setup after cloning:**

```bash
poetry install --with dev
poetry run python scripts/setup_dev_environment.py
```

**After adding a new service:**

```bash
# Update scripts/setup_dev_environment.py with the new service
poetry run python scripts/setup_dev_environment.py
```

## Verification

### Test 1: Direct Import
```bash
poetry run python - <<'PY'
from app.main import app
print(f"✅ Imported: {app}")
PY
```

### Test 2: Health Check
```bash
poetry run python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/health")
print(f"✅ Status: {response.status_code}")
print(f"✅ Payload: {response.json()}")
PY
```

### Test 3: Pytest
```bash
poetry run pytest services/analysis-service/tests/test_health.py -v
```

All three should work without `PYTHONPATH` manipulation.

## Alternative Solutions Considered

### 1. ❌ `sitecustomize.py` in site-packages
- **Problem:** System-level `sitecustomize.py` takes precedence
- **Location:** `/usr/lib/python3.12/sitecustomize.py` loaded first
- **Result:** Our customization never runs

### 2. ❌ Install services as editable packages
- **Command:** `poetry install -e services/analysis-service`
- **Problem:** Poetry doesn't support multiple editable packages well in monorepos
- **Result:** Complex dependency management

### 3. ❌ Modify `PYTHONPATH` environment variable
- **Problem:** Must be set every time, not automatic
- **Result:** Developer friction, easy to forget

### 4. ✅ `.pth` file (chosen solution)
- **Pros:** Automatic, persistent, simple
- **Cons:** Absolute paths (but generated dynamically)
- **Result:** Works perfectly, zero developer friction

## Impact on Development Workflow

### Before Fix
```bash
# Had to remember PYTHONPATH every time
PYTHONPATH=services/analysis-service poetry run python script.py

# Tests would hang
poetry run pytest services/analysis-service/tests/  # HANGS
```

### After Fix
```bash
# Just works
poetry run python script.py

# Tests run normally
poetry run pytest services/analysis-service/tests/  # ✅ WORKS
```

## Maintenance

### When to Re-run Setup

1. **After pulling new services**
2. **After virtualenv recreation** (`poetry env remove python`)
3. **After Poetry upgrade** (may recreate virtualenv)

### Troubleshooting

**Issue:** Still getting `ModuleNotFoundError`

**Check 1:** Verify .pth file exists
```bash
poetry run python -c "import site; print(site.getsitepackages()[0])"
# Check if saju_services.pth exists in that directory
```

**Check 2:** Verify paths in .pth file
```bash
cat $(poetry run python -c "import site; print(site.getsitepackages()[0])")/saju_services.pth
# Should show absolute paths to all services
```

**Check 3:** Re-run setup
```bash
poetry run python scripts/setup_dev_environment.py
```

## Related Files

- `scripts/setup_dev_environment.py` - Setup script
- `pytest.ini` - Pytest configuration (separate pythonpath)
- `README.md` - User documentation
- `.pth file location` - `~/.cache/pypoetry/virtualenvs/saju-monorepo-*/lib/python3.*/site-packages/saju_services.pth`

## References

- Python `.pth` files: https://docs.python.org/3/library/site.html
- Poetry monorepo patterns: https://python-poetry.org/docs/managing-dependencies/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
