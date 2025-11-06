# Sitecustomize.py Retirement Plan (Week 4 Task 3)

**Date:** 2025-11-06
**Status:** 🟡 Partial Complete - Import Cleanup Done, Policy Path Resolution Pending
**Version:** 1.0.0

## Overview

This document tracks the retirement of `sitecustomize.py` path manipulation hacks in favor of proper Python packaging and imports.

**Goal:** Remove dependency on `sitecustomize.py` by:
1. ✅ Using relative imports within services
2. ✅ Using installed `saju-common` package for cross-service imports
3. ⏳ Fixing policy file path resolution (BLOCKER)

---

## Current Status

### ✅ Completed

**1. Import Cleanup (50 absolute imports fixed)**
- Fixed all `from app.core.*` imports to use relative `from .*`
- Fixed all `from services.common import` to `from saju_common import`
- Created `scripts/fix_absolute_imports.py` automation tool

**Files Modified:**
- 22 files in `services/analysis-service/`
- 7 files in `services/*/app/main.py`
- 10+ files using `policy_loader` or `saju_common`

**2. Package Installation**
- `saju-common` v1.4.0 installed as editable package
- All services can import from `saju_common` directly
- No need for sitecustomize.py path hacking for package imports

### ⏳ Remaining Blocker

**Policy File Path Resolution**

**Problem:**
```python
# services/common/saju_common/policy_loader.py:43
def resolve_policy_path(filename):
    # Searches from /services/ as base, but policies are at repo root
    base_paths = [
        Path("/services/policy"),  # ❌ Wrong
        Path("/services/saju_codex_batch_all_v2_6_signed/policies"),  # ❌ Wrong
    ]
```

**Root Cause:**
- `policy_loader.py` assumes it's running from services/ directory
- Actual policy files are at repo root: `/policy/`, `/saju_codex_batch_all_v2_6_signed/policies/`
- sitecustomize.py adds repo root to sys.path, masking this issue

**Impact:**
- Without sitecustomize.py, all policy loads fail with `FileNotFoundError`
- Tests cannot run without sitecustomize.py active

**Solution Required:**
1. Update `policy_loader.py` to use package-relative paths
2. OR move policy files into `saju_common/policies/` package
3. OR use environment variable for policy root path
4. OR update Pydantic Settings to configure policy paths (Task 5)

---

## Changes Made

### Import Fixes Applied

**Pattern 1: Absolute to Relative Imports**
```python
# Before
from app.core.engine import AnalysisEngine

# After
from .engine import AnalysisEngine
```

**Pattern 2: services.common to saju_common**
```python
# Before
from services.common import create_service_app
from services.common.policy_loader import resolve_policy_path

# After
from saju_common import create_service_app
from saju_common.policy_loader import resolve_policy_path
```

### Services Fixed

| Service | Files Modified | Import Fixes |
|---------|----------------|--------------|
| **analysis-service** | 22 files | 50 imports |
| **api-gateway** | 1 file | 1 import |
| **astro-service** | 1 file | 1 import |
| **llm-checker** | 1 file | 1 import |
| **llm-polish** | 1 file | 1 import |
| **pillars-service** | 1 file | 1 import |
| **tz-time-service** | 1 file | 1 import |

**Total:** 28 files, 56 imports fixed

---

## Policy Path Resolution Options

### Option 1: Package-Relative Paths (Recommended)
```python
# saju_common/policy_loader.py
from importlib.resources import files

def resolve_policy_path(filename):
    """Resolve policy file using package resources."""
    # Try saju_common/policies/ first
    try:
        policy_file = files('saju_common').joinpath('policies', filename)
        if policy_file.is_file():
            return str(policy_file)
    except:
        pass

    # Fall back to repo root search
    repo_root = _find_repo_root()
    search_paths = [
        repo_root / "policy",
        repo_root / "saju_codex_batch_all_v2_6_signed" / "policies",
    ]
    ...
```

**Pros:**
- No environment variables needed
- Works with installed packages
- Relocatable

**Cons:**
- Need to bundle policies with package
- OR keep fallback to repo root

### Option 2: Environment Variable
```python
import os
from pathlib import Path

POLICY_ROOT = Path(os.getenv("SAJU_POLICY_ROOT", Path.cwd()))

def resolve_policy_path(filename):
    search_paths = [
        POLICY_ROOT / "policy",
        POLICY_ROOT / "saju_codex_batch_all_v2_6_signed" / "policies",
    ]
    ...
```

**Pros:**
- Simple implementation
- Flexible for different deployments

**Cons:**
- Requires env var configuration
- Not auto-discoverable

### Option 3: Pydantic Settings (Task 5 Integration)
```python
# saju_common/settings.py
from pydantic_settings import BaseSettings

class SajuSettings(BaseSettings):
    policy_root: Path = Field(default_factory=lambda: Path.cwd())
    policy_dirs: list[str] = [
        "policy",
        "saju_codex_batch_all_v2_6_signed/policies",
    ]

    class Config:
        env_prefix = "SAJU_"

settings = SajuSettings()

# policy_loader.py
from .settings import settings

def resolve_policy_path(filename):
    for policy_dir in settings.policy_dirs:
        path = settings.policy_root / policy_dir / filename
        if path.exists():
            return str(path)
    ...
```

**Pros:**
- Integrates with Task 5 (Pydantic Settings)
- Environment variable support built-in
- Validation and defaults

**Cons:**
- Requires Task 5 completion first
- More complex

---

## Recommended Action Plan

**Phase 1: Short-term (This Task)**
- ✅ Fix all absolute imports
- ✅ Document policy path issue
- ⏸️ Keep sitecustomize.py for now (policy paths)
- Create follow-up task for policy resolution

**Phase 2: Task 5 Integration**
- Implement Pydantic Settings (Task 5)
- Update `policy_loader.py` to use Settings
- Configure policy paths via environment variables
- Remove sitecustomize.py completely

**Phase 3: Package Bundling (Optional)**
- Bundle critical policies with `saju_common` package
- Use `importlib.resources` for package-relative paths
- Keep environment override for custom policy dirs

---

## Testing Without sitecustomize.py

**Current State:**
```bash
# Disable sitecustomize
$ mv sitecustomize.py sitecustomize.py.bak

# Try to run tests
$ pytest services/analysis-service/tests/test_korean_enricher.py
ImportError: Policy file not found: climate_map_v1.json
```

**Expected After Fix:**
```bash
# Disable sitecustomize
$ mv sitecustomize.py sitecustomize.py.bak

# Set policy root
$ export SAJU_POLICY_ROOT=$(pwd)

# Tests pass
$ pytest services/analysis-service/tests/test_korean_enricher.py
✅ All tests passing
```

---

## Automation Tools Created

### scripts/fix_absolute_imports.py

**Purpose:** Automatically convert `from app.core.*` to `from .*`

**Usage:**
```bash
# Dry run (show changes)
python scripts/fix_absolute_imports.py --dry-run services/analysis-service/

# Apply fixes
python scripts/fix_absolute_imports.py services/analysis-service/
```

**Statistics:**
- Scans all .py files recursively
- Pattern matches: `from app.core.MODULE`
- Replaces with: `from .MODULE`
- Reports: files scanned, modified, total changes

---

## Dependencies

**Completed:**
- ✅ Task 1: Dependency Container
- ✅ Task 2: Refactor @lru_cache singletons
- ✅ Week 3: saju-common package installation

**Blockers:**
- ⏳ Task 5: Pydantic Settings (needed for policy path config)
- ⏳ Task 6: Consolidate policy assets (may inform path strategy)

---

## Rollback Plan

If issues arise:

1. **Restore sitecustomize.py:**
   ```bash
   git checkout sitecustomize.py
   ```

2. **Revert import changes:**
   ```bash
   git checkout services/*/app/main.py
   git checkout services/analysis-service/app/core/saju_orchestrator.py
   ```

3. **Re-run tests:**
   ```bash
   pytest services/analysis-service/tests/
   ```

---

## Completion Criteria

- [ ] All absolute `from app.*` imports converted to relative
- [ ] All `from services.common` imports converted to `from saju_common`
- [ ] Policy file resolution works without sitecustomize.py
- [ ] All tests pass without sitecustomize.py active
- [ ] sitecustomize.py removed from repo
- [ ] scripts/bootstrap/sitecustomize.py removed
- [ ] Documentation updated

**Current:** 2/6 complete (33%)

---

## Next Steps

1. **Complete Task 5:** Implement Pydantic Settings
2. **Update policy_loader.py:** Use Settings for path resolution
3. **Test without sitecustomize:** Verify all imports work
4. **Remove sitecustomize.py:** Delete both files from repo
5. **Update CI/CD:** Remove sitecustomize installation steps

---

**Document Owner:** Claude
**Last Updated:** 2025-11-06
**Status:** Import cleanup complete, awaiting policy path resolution
