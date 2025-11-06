# Switch to pip (Ditch Poetry)

**Date:** 2025-11-04
**Reason:** Poetry 1.8.4 causes 5-6 minute hangs in production, pip works in <7 seconds

---

## Quick Migration (30 seconds)

```bash
# 1. Remove Poetry artifacts
rm -rf .poetry-1.8/

# 2. Create fresh virtualenv (if needed)
rm -rf .venv/
python3 -m venv .venv

# 3. Activate
source .venv/bin/activate

# 4. Install (already have requirements.txt)
pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup service paths
python scripts/setup_dev_environment.py

# 6. Test
pytest services/analysis-service/tests/test_health.py -q
```

**Result:** 2/2 tests passing in 0.60s (total 6.7s)

---

## Daily Workflow

**Activate environment:**
```bash
source .venv/bin/activate
```

**Run tests:**
```bash
pytest services/analysis-service/tests/ -q
```

**Start dev server:**
```bash
cd services/analysis-service
uvicorn app.main:app --reload
```

---

## Performance Comparison

| Setup | First Run | Subsequent | Notes |
|-------|-----------|------------|-------|
| **pip + venv** | 6.7s | ~2-3s | ✅ Consistent, fast |
| Poetry 1.8.4 (sandbox) | 4.8s | ~2-3s | ✅ Works in sandbox |
| Poetry 1.8.4 (production) | 5-6 min | 5-6 min | ❌ Unusable |

---

## What Changed

**Before (Poetry):**
```bash
export PATH=".poetry-1.8/bin:$PATH"
poetry install --with dev
poetry run pytest
```

**After (pip):**
```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest  # no poetry run prefix needed
```

---

## Documentation

- **Full guide:** `docs/PIP_SETUP_GUIDE.md`
- **Performance analysis:** `docs/STARTUP_PERFORMANCE_ANALYSIS.md`
- **Migration report:** `docs/POETRY_184_MIGRATION_REPORT.md`

---

## Why This Works

Poetry's performance issue is environment-specific (WSL2 filesystem, etc.). Using standard Python tools (`pip` + `venv`) eliminates the Poetry overhead and gives consistent ~6-7 second startup times.

**No code changes needed** - just different dependency installation method.

---

**Status:** ✅ Ready to use
**Recommendation:** Use pip for all development work
