# 🔧 ULTRATHINK: Yuanjin Detector Integration Plan

**Date:** 2025-10-08 KST
**Engine:** yuanjin v1.1.0 (원진 Detector)
**Status:** Ready for integration

---

## Executive Summary

User provided yuanjin (원진) detector engine - detects conflicting pairs among 4 earthly branches.
Integration follows same pattern as void calculator: inline signatures, path mapping, test fixes.

**Complexity:** Low (similar to void calc)
**Risk:** Low (isolated new feature)
**Estimated Time:** 10-15 minutes

---

## What's Being Added

### 1. Core Engine: yuanjin.py
- **Purpose:** Detect yuanjin (원진) pairs among 4 branches
- **Algorithm:** Set-based O(1) detection of 6 predefined pairs
- **APIs:**
  - `detect_yuanjin(branches)` → list[list[str]]
  - `apply_yuanjin_flags(branches)` → dict
  - `explain_yuanjin(branches)` → dict with trace
- **Policy:** 6 default pairs, supports override via `policies/yuanjin_policy_v1.json`

### 2. Schema: yuanjin_result.schema.json
- **Standard:** JSON Schema draft-2020-12
- **Validation:** policy_version, signature, present_branches, hits, pair_count

### 3. Tests: test_yuanjin.py
- Golden set tests
- Duplicate/partial tests
- Invalid input tests
- Trace/signature tests
- Schema validation

### 4. Documentation: yuanjin.md
- Korean language
- API examples
- Policy override format

---

## Directory Mapping

**Provided structure:**
```
core/policy_engines/yuanjin.py
core/schemas/yuanjin_result.schema.json
tests/engines/test_yuanjin.py
docs/engines/yuanjin.md
```

**Target structure:**
```
services/analysis-service/app/core/yuanjin.py
services/analysis-service/schemas/yuanjin_result.schema.json
services/analysis-service/tests/test_yuanjin.py
docs/engines/yuanjin.md
```

---

## Integration Changes Required

### 1. Replace infra.signatures Import

**Original:**
```python
from infra.signatures import sha256_signature
```

**Replace with (copy from void.py):**
```python
import hashlib
import json

def _canonical_json_signature(obj) -> str:
    """Compute SHA-256 signature of canonical JSON."""
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

# Then use it:
POLICY_SIGNATURE: str = _canonical_json_signature(_POLICY_SPEC)
```

### 2. Update Policy Path Resolution

**Original paths:**
```python
candidates = [
    Path("policies") / "yuanjin_policy_v1.json",
    Path(__file__).resolve().parents[3] / "policies" / "yuanjin_policy_v1.json",
    Path(__file__).resolve().parents[2] / "policies" / "yuanjin_policy_v1.json",
    Path(__file__).resolve().parents[1] / "policies" / "yuanjin_policy_v1.json",
]
```

**Update to:**
```python
candidates = [
    Path("policies") / "yuanjin_policy_v1.json",
    Path("saju_codex_batch_all_v2_6_signed") / "policies" / "yuanjin_policy_v1.json",
    Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "yuanjin_policy_v1.json",
]
```

### 3. Fix Test Imports

**Original:**
```python
from core.policy_engines import yuanjin as yj
schema = json.loads(Path("core/schemas/yuanjin_result.schema.json").read_text(encoding="utf-8"))
```

**Update to:**
```python
from app.core import yuanjin as yj
schema_path = Path(__file__).parent.parent / "schemas" / "yuanjin_result.schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
```

### 4. Fix Documentation Imports

**Original:**
```python
from core.policy_engines.yuanjin import detect_yuanjin
```

**Update to:**
```python
from app.core.yuanjin import detect_yuanjin
```

### 5. Fix Schema Typo

**Original (line 2):**
```json
"$schema": "https://json-schema.org/draft/2020-12/schema  ",
```

**Fix (remove trailing spaces):**
```json
"$schema": "https://json-schema.org/draft/2020-12/schema",
```

---

## Implementation Steps

1. ✅ Create integration plan
2. Create `services/analysis-service/app/core/yuanjin.py`:
   - Remove `from infra.signatures import sha256_signature`
   - Add inline `_canonical_json_signature()` function
   - Update `POLICY_SIGNATURE` to use inline function
   - Update policy path candidates
3. Create `services/analysis-service/schemas/yuanjin_result.schema.json`:
   - Fix $schema trailing spaces
4. Create `services/analysis-service/tests/test_yuanjin.py`:
   - Fix import: `from app.core import yuanjin as yj`
   - Fix schema path
5. Create `docs/engines/yuanjin.md`:
   - Update import examples
6. Run tests
7. Format with black/isort
8. Commit and push

---

## Expected Results

**Tests:** All tests should pass (10+ test cases)
**Format:** Clean black/isort formatting
**Integration:** Standalone engine ready for future AnalysisEngine integration

---

## Yuanjin Pairs (Default Policy)

```python
[
    ["子", "未"],  # Zi-Wei
    ["丑", "午"],  # Chou-Wu
    ["寅", "巳"],  # Yin-Si
    ["卯", "辰"],  # Mao-Chen
    ["申", "亥"],  # Shen-Hai
    ["酉", "戌"],  # You-Xu
]
```

---

**Ready to execute:** YES
**Dependencies:** None (inline signature utility)
**Next Action:** Create files with path corrections
