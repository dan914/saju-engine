# FastAPI Startup Performance Analysis

**Date:** 2025-11-04
**Context:** Poetry 1.8.4 migration validation
**Issue:** TestClient hangs 5-6 minutes in production environment vs. 4.8s in sandbox

---

## Executive Summary

**Findings:**
- ✅ **Code is NOT the bottleneck** - All engines initialize in 142ms
- ✅ **Poetry 1.8.4 is NOT the problem** - Total startup is 4.8s in sandbox
- ⚠️ **Environment-specific issue** - 60-75x performance degradation in production vs. sandbox

**Root Cause Candidates:**
1. **I/O Performance**: Slow filesystem (WSL2 on Windows, network drives, NTFS)
2. **Python Import Caching**: `__pycache__` generation on slow filesystem
3. **File Descriptor Limits**: Resource exhaustion during initialization
4. **Antivirus/Security Software**: Real-time scanning during module loads
5. **WSL2 Overhead**: Cross-filesystem access between Windows and Linux

---

## Performance Baseline (Sandbox Environment)

### Overall Startup Timing
```
Total startup time:        4.792s
├─ Import FastAPI:         2.465s (51%)
├─ Create TestClient:      1.043s (22%)
├─ Import dependencies:    0.959s (20%)
├─ Load AnalysisEngine:    0.201s (4%)
└─ Load LLMGuard:          0.011s (<1%)
```

### Component-Level Timing (SajuOrchestrator.__init__)
**Total: 142ms for 29 components**

Top 10 slowest components:
1. LuckSeedBuilder: 24ms (17%)
2. StrengthEvaluator: 16ms (11%)
3. lifecycle_stages.json: 14ms (10%)
4. LLMGuard: 14ms (10%)
5. RelationWeightEvaluator: 11ms (8%)
6. KoreanLabelEnricher: 10ms (7%)
7. branch_tengods_policy.json: 8ms (6%)
8. luck_pillars_policy.json: 8ms (6%)
9. RelationTransformer: 6ms (5%)
10. PatternProfiler: 4ms (3%)

**Key Insight:** Even the "slowest" component takes only 24ms. There is NO code-level bottleneck.

---

## Diagnostic Scripts Provided

### 1. `scripts/diagnose_startup.py`
High-level timing of FastAPI app initialization and TestClient creation.

**Usage:**
```bash
poetry run python scripts/diagnose_startup.py
```

**What it measures:**
- FastAPI import time
- App creation time
- TestClient initialization
- First /health request
- Second /health request (cached)

### 2. `scripts/profile_orchestrator_init.py`
Fine-grained profiling of all 29 engine initializations.

**Usage:**
```bash
poetry run python scripts/profile_orchestrator_init.py
```

**What it measures:**
- Individual engine load times
- Policy file load times
- Sorted timing summary
- Percentage breakdown

---

## Recommended Next Steps

### Step 1: Run Diagnostics in Production Environment
```bash
# From repo root
export PATH="/mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine/.poetry-1.8/bin:$PATH"

# Run high-level diagnostic
poetry run python scripts/diagnose_startup.py

# Run detailed profiling
poetry run python scripts/profile_orchestrator_init.py
```

**Expected outputs:**
- Sandbox environment: ~4.8s total, 142ms for engines
- Production environment: >5 minutes total, ???ms for engines

### Step 2: Identify Bottleneck Category

#### If engines load slowly (>10 seconds total):
**Likely cause:** Filesystem I/O performance
- Policy JSON files are on slow network drive
- NTFS performance issues in WSL2
- Antivirus scanning JSON files

**Solution:**
- Move repo to native WSL2 filesystem (`/home/`)
- Disable antivirus scanning for project directory
- Check disk I/O with `iostat -x 1`

#### If engines load fast (<1 second) but TestClient slow:
**Likely cause:** Python import caching or uvloop
- `__pycache__` generation on slow filesystem
- Event loop initialization overhead

**Solution:**
- Pre-compile all `.pyc` files: `poetry run python -m compileall services/`
- Check for uvloop: `poetry run python -c "import asyncio; print(asyncio.get_event_loop_policy())"`
- Try disabling uvloop if installed

#### If "Import FastAPI" takes >30 seconds:
**Likely cause:** Dependency tree bloat or network-based imports
- Check for network-mounted site-packages
- Inspect `.venv` location (must be local)

**Solution:**
- Verify `.venv` is in project directory: `ls -la .venv/`
- Check for stale NFS mounts: `df -h`

### Step 3: WSL2-Specific Diagnostics

#### Check filesystem type:
```bash
df -T /mnt/c/Users/PW1234/.vscode/sajuv2/saju-engine
```
**Expected:** `drvfs` (slow) or `ext4` (fast)

**If drvfs:** Repo is on Windows filesystem via `/mnt/c/`, which has 10-100x slower I/O.

**Solution:** Move repo to native WSL2 filesystem:
```bash
# Copy repo to WSL2 native filesystem
cp -r /mnt/c/Users/PW1234/.vscode/sajuv2 ~/sajuv2/

# Reinstall Poetry 1.8.4 in new location
cd ~/sajuv2/saju-engine
export POETRY_HOME=$PWD/.poetry-1.8
python3 scripts/install-poetry.py --version 1.8.4 --yes
export PATH="$POETRY_HOME/bin:$PATH"

# Regenerate virtualenv
rm -rf .venv/
poetry install --with dev
poetry run python scripts/setup_dev_environment.py

# Test performance
poetry run python scripts/diagnose_startup.py
```

#### Check file descriptor limits:
```bash
ulimit -n  # Should be ≥1024
```

#### Check for antivirus interference:
```bash
# Windows Defender real-time scanning can cause massive slowdowns
# Exclude project directory in Windows Security settings
```

---

## Expected Performance Targets

### Acceptable Performance (WSL2 on drvfs)
- Total startup: 10-30 seconds
- Engine initialization: 500ms - 2s
- Import FastAPI: 5-15 seconds

### Good Performance (WSL2 on ext4 or native Linux)
- Total startup: 3-7 seconds
- Engine initialization: 100-300ms
- Import FastAPI: 1-3 seconds

### Current Sandbox Performance (Reference)
- Total startup: 4.8 seconds ✅
- Engine initialization: 142ms ✅
- Import FastAPI: 2.5 seconds ✅

### Production Performance (Reported)
- Total startup: 5-6 minutes ❌ (60-75x slower)
- Engine initialization: Unknown
- Import FastAPI: Unknown

---

## Technical Details

### Startup Sequence
1. **Python interpreter startup** (~50ms)
2. **Import FastAPI and dependencies** (includes pydantic, starlette, uvicorn)
3. **Create FastAPI app** (instantiate app object)
4. **Import app.api.dependencies** (triggers imports of all core modules)
5. **Load AnalysisEngine singleton**
   - Creates SajuOrchestrator instance
   - Loads 29 engines sequentially
   - Loads 8 policy JSON files from disk
6. **Load LLMGuard singleton**
7. **Create TestClient** (creates ASGI app test wrapper)
8. **First request** (warms up any remaining lazy-loaded components)

### Engine Initialization Order
Per `SajuOrchestrator.__init__()`:

**Core Engines (7):**
1. StrengthEvaluator (v2.0) - 16ms
2. RelationTransformer - 6ms
3. RelationWeightEvaluator - 11ms
4. RelationAnalyzer - 3ms
5. ClimateEvaluator - 3ms
6. YongshinSelector - 3ms
7. ShenshaCatalog - 2ms

**Policy-Driven Engines (8):**
8. TenGodsCalculator - 8ms (policy load)
9. LuckSeedBuilder - 24ms
10. AnnualLuckCalculator - <1ms
11. MonthlyLuckCalculator - <1ms
12. DailyLuckCalculator - <1ms
13. TwelveStagesCalculator - 14ms (policy load)
14. LuckCalculator - 8ms (policy load)

**MVP Engines (4):**
15. ClimateAdvice - 3ms
16. LuckFlow - 3ms
17. GyeokgukClassifier - 3ms
18. PatternProfiler - 4ms

**Post-Processing Engines (6):**
19. EngineSummariesBuilder - <1ms
20. KoreanLabelEnricher - 10ms
21. SchoolProfileManager - 2ms
22. RecommendationGuard - 3ms
23. LLMGuard - 14ms
24. TextGuard - 2ms

**Utilities (2):**
25. FileSolarTermLoader - <1ms
26. BasicTimeResolver - <1ms

---

## Conclusion

**Poetry 1.8.4 migration is technically successful.** The performance problem is **NOT caused by**:
- Code inefficiency (engines initialize in 142ms)
- Poetry version (4.8s total startup is acceptable)
- Python path configuration (.pth file works correctly)

**The 5-6 minute hang is caused by environmental factors:**
- Filesystem performance (likely primary cause)
- WSL2 cross-filesystem overhead
- Potential antivirus/security software interference
- Possible Python import caching issues

**Recommended Action:**
1. Run both diagnostic scripts in production environment
2. Move repo to native WSL2 filesystem (`/home/`) if on `/mnt/c/`
3. Exclude project directory from antivirus scanning
4. Report diagnostic script output for further analysis

---

**Prepared by:** Claude Code
**Script Artifacts:**
- `scripts/diagnose_startup.py` - High-level timing
- `scripts/profile_orchestrator_init.py` - Component-level profiling
