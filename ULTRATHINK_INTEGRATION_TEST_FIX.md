# 🧠 Ultrathink: Integration Test Fix Analysis

**Date:** 2025-10-12 KST
**Issue:** Dynamic import failing for @dataclass decorator
**Status:** Root cause identified, solution ready

---

## 🔍 Root Cause Analysis

### The Problem

```python
# Current code (BROKEN)
spec = importlib.util.spec_from_file_location("luck_pillars", luck_pillars_path)
luck_pillars = importlib.util.module_from_spec(spec)
spec.loader.exec_module(luck_pillars)  # ❌ Fails here
```

**Why it fails:**
1. `spec_from_file_location("luck_pillars", path)` creates a spec with `name="luck_pillars"`
2. `module_from_spec(spec)` creates module object with `__module__="luck_pillars"`
3. `exec_module()` runs the module code, which includes:
   ```python
   @dataclass
   class BirthContext:
       ...
   ```
4. The `@dataclass` decorator internally calls:
   ```python
   ns = sys.modules.get(cls.__module__).__dict__  # cls.__module__ = "luck_pillars"
   ```
5. `sys.modules.get("luck_pillars")` returns `None` because we never registered it
6. `None.__dict__` → **AttributeError**

### Why Unit Tests Work

```python
# In pytest (WORKS)
from app.core.luck_pillars import LuckCalculator
```

**Why it works:**
1. pytest adds `services/analysis-service` to `sys.path`
2. `import app.core.luck_pillars` triggers normal Python import machinery
3. Python's import system **automatically registers** `app.core.luck_pillars` in `sys.modules`
4. When `@dataclass` runs, `sys.modules.get("app.core.luck_pillars")` returns the module
5. Everything works

---

## ✅ The Solution

```python
# Fixed code (WORKING)
spec = importlib.util.spec_from_file_location(
    "analysis_service.luck_pillars",  # Use namespaced name
    luck_pillars_path
)
luck_pillars = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = luck_pillars  # ✅ Register BEFORE exec_module
spec.loader.exec_module(luck_pillars)
```

**Critical addition:**
```python
sys.modules[spec.name] = luck_pillars  # <-- This line fixes everything
```

**Why it works:**
1. Module is registered in `sys.modules` **before** code execution
2. When `@dataclass` decorator runs and calls `sys.modules.get("analysis_service.luck_pillars")`
3. It finds our pre-registered module object
4. `.__dict__` works correctly
5. Decorator completes successfully

---

## 🎯 Implementation Plan

### Step 1: Fix test script
- Add `sys.modules[spec.name] = module` before `exec_module()`
- Use namespaced module name to avoid conflicts

### Step 2: Run with venv Python
```bash
cd "/Users/yujumyeong/coding/ projects/사주"
.venv/bin/python3 test_luck_pillars_standalone.py
```

### Step 3: Verify output
Expected results:
- ✅ Policy version: "luck_pillars_v1"
- ✅ Direction: "forward" (male × 庚陽)
- ✅ Start age: 7.98 (from ctx override)
- ✅ First pillar: 丙戌 (乙酉 + 1)
- ✅ Pillar count: 10
- ✅ All decades numbered 1-10
- ✅ All spans are 10 years
- ✅ Policy signature: 64-char hex
- ✅ Current luck: Decade 2 or 3 (age 25.1)

### Step 4: Document completion
Only after verified output:
- Create `PHASE_2_COMPLETION_REPORT.md`
- Update `CODEBASE_MAP_v1.3.0.md` → v1.4.0
- Mark 18/18 features (100% completion)

---

## 📝 Technical Notes

### Why sys.modules Registration Matters

Python's import system maintains `sys.modules` as a cache of all imported modules. Key behaviors:

1. **Normal import**: `import foo` → Python registers `foo` in `sys.modules` automatically
2. **Dynamic import**: `importlib.util.spec_from_file_location()` → **NO automatic registration**
3. **Decorator introspection**: Many decorators (including `@dataclass`) use `sys.modules` to resolve module-level state

### Alternative Solutions (Not Used)

**Option A: Add parent directory to sys.path**
```python
sys.path.insert(0, str(Path(__file__).parent / "services" / "analysis-service"))
from app.core.luck_pillars import LuckCalculator  # Normal import
```
❌ Rejected: Requires fixing complex cross-service imports

**Option B: Mock sys.modules in decorator**
```python
import sys
sys.modules['luck_pillars'] = type('MockModule', (), {'__dict__': {}})()
```
❌ Rejected: Fragile, requires patching before import

**Option C: Use exec() instead of importlib**
```python
with open(luck_pillars_path) as f:
    code = f.read()
exec(code, globals())
```
❌ Rejected: Loses module isolation, pollutes global namespace

**✅ Option D: Register in sys.modules (CHOSEN)**
- Minimal change (1 line)
- Follows Python import conventions
- No side effects
- Recommended by Python documentation

---

## 🔬 Verification Checklist

Before declaring Phase 2 complete:

- [ ] Test script runs without errors
- [ ] All 10 pillars generated
- [ ] First pillar matches expected (丙戌)
- [ ] Direction matches expected (forward)
- [ ] Start age matches expected (7.98)
- [ ] Current luck detection works
- [ ] Policy signature is valid hex
- [ ] All verification checks show ✅
- [ ] Output is deterministic (run twice, same signature)

---

**Analysis Complete**
**Next Action:** Apply fix and run verification
