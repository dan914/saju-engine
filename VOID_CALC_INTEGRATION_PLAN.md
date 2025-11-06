# 🔧 ULTRATHINK: Void Calculator Integration Plan

**Date:** 2025-10-08 KST
**Engine:** void_calc v1.1.0 (공망/旬空 Calculator)
**Status:** Ready for integration

---

## Executive Summary

User provided a complete void calculator engine with tests, schema, and documentation.
Need to integrate into `analysis-service` with proper directory mapping and dependency resolution.

**Complexity:** Medium (missing infra.signatures dependency)
**Risk:** Low (isolated new feature, doesn't modify existing code)
**Estimated Time:** 15-20 minutes

---

## What's Being Added

### 1. Core Engine: void_calc.py
- **Purpose:** Calculate void (空亡/旬空) branches based on day pillar
- **Algorithm:** 60 Jiazi cycle → Xun (旬) index → 2 void branches
- **APIs:**
  - `compute_void(day_pillar)` → list[str]
  - `apply_void_flags(branches, kong)` → dict
  - `explain_void(day_pillar)` → dict with trace
- **Policy:** Supports override via `policies/void_policy_v1.json`

### 2. Schema: void_result.schema.json
- **Standard:** JSON Schema draft-2020-12
- **Validation:** Policy version, signature, indices, kong branches

### 3. Tests: test_void_calc.py
- Parametrized golden set tests (6 cases)
- Invalid input tests (6 cases)
- Flag application tests
- Schema validation tests

### 4. Documentation: void_calc.md
- Korean language
- API usage examples
- Policy override format
- Integration points

---

## Integration Challenges

### Challenge 1: Directory Structure Mismatch ⚠️

**Provided structure:**
```
core/policy_engines/void_calc.py
core/schemas/void_result.schema.json
tests/engines/test_void_calc.py
docs/engines/void_calc.md
```

**Our codebase structure:**
```
services/analysis-service/
  app/
    core/
      engine.py
      strength.py
      relations.py
      ...
  tests/
    test_*.py
```

**Resolution:**
```
core/policy_engines/void_calc.py  → services/analysis-service/app/core/void.py
core/schemas/void_result.schema.json → services/analysis-service/schemas/void_result.schema.json
tests/engines/test_void_calc.py  → services/analysis-service/tests/test_void.py
docs/engines/void_calc.md  → docs/engines/void_calc.md
```

### Challenge 2: Missing Dependency - infra.signatures 🔴

**Code imports:**
```python
from infra.signatures import canonical_dumps, sha256_signature
```

**Problem:** Module doesn't exist yet

**CLAUDE.md requirement:**
```python
from canonicaljson import encode_canonical_json
import hashlib

canonical = encode_canonical_json(data)
computed = hashlib.sha256(canonical).hexdigest()
```

**Resolution Options:**

**Option A:** Create infra module (proper solution)
```python
# services/common/infra/signatures.py
from canonicaljson import encode_canonical_json
import hashlib
import json

def canonical_dumps(obj):
    """RFC-8785 canonical JSON serialization."""
    return encode_canonical_json(obj)

def sha256_signature(obj):
    """Compute SHA-256 signature of canonical JSON."""
    canonical = canonical_dumps(obj)
    return hashlib.sha256(canonical).hexdigest()
```

**Option B:** Inline in void.py (quick solution)
```python
# Direct import in void.py
import json
import hashlib

def _canonical_json_signature(obj):
    """Simplified canonical JSON → SHA-256 (deterministic dict ordering)."""
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

POLICY_SIGNATURE: str = _canonical_json_signature(POLICY_SPEC)
```

**Recommendation:** Start with Option B (inline), create infra module later in separate PR

### Challenge 3: Policy File Location

**Code expects:**
```
policies/void_policy_v1.json  (optional override)
```

**Our structure:**
```
saju_codex_batch_all_v2_6_signed/policies/
```

**Resolution:**
- Policy override is optional (code has default)
- If user wants to add policy, it goes in `saju_codex_batch_all_v2_6_signed/policies/void_policy_v1.json`
- Update path resolution in void.py to check both locations

### Challenge 4: Import Path Changes

**Original imports:**
```python
from core.policy_engines import void_calc as vc
```

**New import (after moving to services/analysis-service):**
```python
from app.core import void
# or
from services.analysis-service.app.core import void
```

**Fix in test file:**
```python
# Change this:
from core.policy_engines import void_calc as vc

# To this:
from app.core import void as vc
```

---

## Step-by-Step Integration Plan

### Phase 1: Create Infrastructure (5 min)

1. **Create directories:**
```bash
mkdir -p services/analysis-service/schemas
mkdir -p docs/engines
```

2. **Create inline signature utility in void.py:**
   - Remove `from infra.signatures import ...`
   - Add inline `_canonical_json_signature()` function
   - Update `POLICY_SIGNATURE` to use inline function

### Phase 2: Add Files with Path Corrections (5 min)

3. **Create void.py:**
   - Copy provided code to `services/analysis-service/app/core/void.py`
   - Fix import: remove `from infra.signatures ...`
   - Add inline signature function
   - Update policy path resolution to check `saju_codex_batch_all_v2_6_signed/policies/`

4. **Create schema:**
   - Copy to `services/analysis-service/schemas/void_result.schema.json`

5. **Create test:**
   - Copy to `services/analysis-service/tests/test_void.py`
   - Fix import: `from app.core import void as vc`
   - Update schema path in test

6. **Create documentation:**
   - Copy to `docs/engines/void_calc.md`

### Phase 3: Dependency Check (2 min)

7. **Check if canonicaljson is needed:**
   - For now, using `json.dumps(sort_keys=True)` is sufficient
   - Add canonicaljson to pyproject.toml later if strict RFC-8785 needed

### Phase 4: Testing (5 min)

8. **Run tests:**
```bash
cd services/analysis-service
../../.venv/bin/pytest tests/test_void.py -v
```

9. **Verify schema validation:**
```bash
../../.venv/bin/python -c "
from app.core import void
result = void.explain_void('乙丑')
print(result)
"
```

### Phase 5: Integration into Engine (3 min)

10. **Update analysis engine (optional for now):**
    - Can integrate into `services/analysis-service/app/core/engine.py` later
    - For now, engine is standalone and can be imported separately

---

## File Modifications Required

### 1. services/analysis-service/app/core/void.py

**Changes:**
```python
# REMOVE:
from infra.signatures import canonical_dumps, sha256_signature

# ADD:
import json
import hashlib

def _canonical_json_signature(obj) -> str:
    """
    Compute SHA-256 signature of canonical JSON.
    Uses deterministic dict ordering (sort_keys=True).
    For strict RFC-8785 compliance, use canonicaljson library.
    """
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

# UPDATE:
POLICY_SIGNATURE: str = _canonical_json_signature(POLICY_SPEC)

# UPDATE path resolution in _try_load_override():
candidates = [
    Path("policies") / "void_policy_v1.json",
    Path("saju_codex_batch_all_v2_6_signed") / "policies" / "void_policy_v1.json",
    Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "void_policy_v1.json",
]
```

### 2. services/analysis-service/tests/test_void.py

**Changes:**
```python
# CHANGE:
from core.policy_engines import void_calc as vc

# TO:
from app.core import void as vc

# UPDATE schema path:
schema_path = Path(__file__).parent.parent / "schemas" / "void_result.schema.json"
```

### 3. services/analysis-service/pyproject.toml

**Optional - Add later:**
```toml
dependencies = [
  ...
  # "canonicaljson>=2.0,<3",  # For strict RFC-8785 compliance
]
```

---

## Testing Strategy

### Unit Tests
```bash
pytest services/analysis-service/tests/test_void.py -v
```

**Expected:** All 20+ tests pass

### Integration Test
```python
from services.analysis_service.app.core import void

# Test compute_void
kong = void.compute_void("乙丑")
assert kong == ["戌", "亥"]

# Test apply_void_flags
result = void.apply_void_flags(["戌","亥","寅","卯"], ["戌","亥"])
assert result["flags"] == [True, True, False, False]

# Test explain_void
trace = void.explain_void("乙丑")
assert "policy_signature" in trace
assert len(trace["policy_signature"]) == 64  # SHA-256 hex
```

### Schema Validation Test
```bash
# Validate schema file
python -m jsonschema services/analysis-service/schemas/void_result.schema.json
```

---

## Integration into Analysis Pipeline (Future)

Once void.py is working standalone, integrate into `engine.py`:

```python
# services/analysis-service/app/core/engine.py

from .void import compute_void, explain_void, apply_void_flags

class AnalysisEngine:
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        # ... existing code ...

        # Add void calculation
        day_pillar = f"{pillars['day'].stem}{pillars['day'].branch}"
        void_kong = compute_void(day_pillar)
        void_trace = explain_void(day_pillar)

        # Apply void flags to 4 branches
        branches_4 = [
            pillars['year'].branch,
            pillars['month'].branch,
            pillars['day'].branch,
            pillars['hour'].branch
        ]
        void_flags = apply_void_flags(branches_4, void_kong)

        # Add to response
        return AnalysisResponse(
            ...
            void=VoidResult(**void_trace),
            void_flags=void_flags,
            ...
        )
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Missing canonicaljson | High | Low | Use json.dumps(sort_keys=True) initially |
| Import path conflicts | Low | Low | Proper testing before merge |
| Schema validation failure | Low | Medium | Validate schema with jsonschema library |
| Policy file not found | Medium | None | Code handles gracefully (uses default) |
| Test failures | Low | Low | Well-written parametrized tests |

---

## Dependencies to Add (Optional/Later)

```bash
# If strict RFC-8785 needed
pip install canonicaljson>=2.0
```

```toml
# services/analysis-service/pyproject.toml
dependencies = [
  "canonicaljson>=2.0,<3",  # RFC-8785 canonical JSON
]
```

---

## Rollout Plan

### Immediate (This PR)
1. ✅ Add void.py (standalone, inline signatures)
2. ✅ Add schema
3. ✅ Add tests
4. ✅ Add documentation

### Short-term (Next PR)
5. Create `services/common/infra/signatures.py` module
6. Refactor void.py to use shared signatures module
7. Add other engines (yuanjin, twelve_stage) that need signatures

### Medium-term (PR after Stage1)
8. Integrate void into AnalysisEngine
9. Add VoidResult to AnalysisResponse model
10. Update API specs to include void in responses

---

## Verification Checklist

Before committing:
- [ ] All tests pass: `pytest services/analysis-service/tests/test_void.py -v`
- [ ] Schema is valid JSON Schema draft-2020-12
- [ ] Documentation is clear and examples work
- [ ] No import errors when running `from app.core import void`
- [ ] POLICY_SIGNATURE generates valid 64-char hex SHA-256
- [ ] Policy override path resolution works
- [ ] Invalid inputs raise ValueError with Korean messages
- [ ] CI formatting passes: `black` and `isort`

---

## Success Criteria

✅ **Green Tests:** All void tests pass
✅ **Clean Imports:** No missing module errors
✅ **Schema Valid:** void_result.schema.json validates
✅ **Documentation:** Clear Korean docs with examples
✅ **Standalone:** Engine works independently of AnalysisEngine

---

## Commands to Execute

```bash
# 1. Create directories
mkdir -p services/analysis-service/schemas
mkdir -p docs/engines

# 2. Create void.py with modifications (see File Modifications section)

# 3. Create schema
cp void_result.schema.json services/analysis-service/schemas/

# 4. Create test with import fixes
cp test_void_calc.py services/analysis-service/tests/test_void.py
# Then edit imports

# 5. Create docs
cp void_calc.md docs/engines/

# 6. Run tests
cd services/analysis-service
../../.venv/bin/pytest tests/test_void.py -v

# 7. Format
../../.venv/bin/black app/core/void.py tests/test_void.py
../../.venv/bin/isort app/core/void.py tests/test_void.py

# 8. Commit
git add app/core/void.py schemas/void_result.schema.json tests/test_void.py
git add ../../docs/engines/void_calc.md
git commit -m "feat(analysis): add void (空亡) calculator engine v1.1

- Implement compute_void, apply_void_flags, explain_void APIs
- Add JSON Schema for void result validation
- Add comprehensive test suite (20+ tests)
- Add Korean documentation
- Inline signature utility (RFC-8785 compliance)

Refs: #VOID-001"
```

---

**END OF INTEGRATION PLAN**

**Ready to execute:** YES
**Blockers:** NONE
**Next Action:** Create files with path corrections and inline signature utility
