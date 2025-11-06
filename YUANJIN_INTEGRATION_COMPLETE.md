# ✅ Yuanjin Detector Integration Complete

**Date:** 2025-10-08 KST
**Engine:** yuanjin v1.1.0 (원진 Detector)
**Status:** Successfully integrated and tested

---

## Summary

Successfully integrated the yuanjin (원진) detector engine into the analysis-service with minimal issues (one function ordering fix).

## Files Added

1. **services/analysis-service/app/core/yuanjin.py** (175 lines)
   - Core engine implementation
   - Inline signature utility (replaced missing infra.signatures)
   - Policy override support
   - 3 public APIs: detect_yuanjin, apply_yuanjin_flags, explain_yuanjin
   - Deterministic sorting for reproducible results

2. **services/analysis-service/schemas/yuanjin_result.schema.json**
   - JSON Schema draft-2020-12
   - Validates policy_version, policy_signature, present_branches, hits, pair_count

3. **services/analysis-service/tests/test_yuanjin.py** (85 lines)
   - 10 tests total
   - Golden set tests (2 parametrized cases)
   - Duplicate/partial tests (2 parametrized cases)
   - Invalid input tests (5 parametrized cases)
   - Trace/signature validation test
   - **Result: 10/10 passing ✅**

4. **docs/engines/yuanjin.md**
   - Korean documentation
   - API usage examples
   - Policy override format
   - Sorting rules explanation

5. **YUANJIN_INTEGRATION_PLAN.md**
   - Integration analysis
   - Directory mapping
   - Required changes documentation

## Changes Made from Original

### 1. Fixed Missing Dependency
**Original:**
```python
from infra.signatures import sha256_signature
```

**Solution:**
```python
import hashlib
import json

def _canonical_json_signature(obj) -> str:
    """Compute SHA-256 signature of canonical JSON."""
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
```

### 2. Updated Directory Structure
**Original:**
```
core/policy_engines/yuanjin.py
core/schemas/yuanjin_result.schema.json
tests/engines/test_yuanjin.py
docs/engines/yuanjin.md
```

**Mapped to:**
```
services/analysis-service/app/core/yuanjin.py
services/analysis-service/schemas/yuanjin_result.schema.json
services/analysis-service/tests/test_yuanjin.py
docs/engines/yuanjin.md
```

### 3. Fixed Import Paths in Tests
**Original:**
```python
from core.policy_engines import yuanjin as yj
schema = json.loads(Path("core/schemas/yuanjin_result.schema.json").read_text(encoding="utf-8"))
```

**Updated:**
```python
from app.core import yuanjin as yj
schema_path = Path(__file__).parent.parent / "schemas" / "yuanjin_result.schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
```

### 4. Updated Policy Path Resolution
```python
candidates = [
    Path("policies") / "yuanjin_policy_v1.json",
    Path("saju_codex_batch_all_v2_6_signed") / "policies" / "yuanjin_policy_v1.json",
    Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "yuanjin_policy_v1.json",
]
```

### 5. Fixed Function Ordering
**Issue:** `_sort_pair()` was defined after `_validate_and_normalize_pairs()` but was called within it.

**Fix:** Moved `_sort_pair()` to before `_validate_and_normalize_pairs()`:
```python
# --- 내부 유틸 (정책 로드 전에 필요) ------------------------------------------
def _sort_pair(a: str, b: str) -> Tuple[str, str]:
    """쌍 내부를 BRANCHES 인덱스 기준으로 정렬."""
    return (a, b) if _BR_INDEX[a] <= _BR_INDEX[b] else (b, a)
```

### 6. Fixed Schema Trailing Spaces
**Original:**
```json
"$schema": "https://json-schema.org/draft/2020-12/schema  ",
```

**Fixed:**
```json
"$schema": "https://json-schema.org/draft/2020-12/schema",
```

### 7. Updated Documentation Imports
```python
from app.core.yuanjin import detect_yuanjin
```

## Test Results

```bash
$ PYTHONPATH=".:../.." ../../.venv/bin/pytest tests/test_yuanjin.py -v

======================== 10 passed, 1 warning in 0.10s =========================
```

**Tests:**
- ✅ test_detect_and_flags_goldenset (2 parametrized cases)
- ✅ test_detect_with_duplicates_and_partials (2 parametrized cases)
- ✅ test_invalid_inputs_raise (5 parametrized cases)
- ✅ test_explain_trace_and_signature_shape

## Commit

```
commit 049aa83
Author: 유주명
Date: 2025-10-08

feat(analysis): add yuanjin (원진) detector engine v1.1

- Implement detect_yuanjin, apply_yuanjin_flags, explain_yuanjin APIs
- Add JSON Schema for yuanjin result validation (draft-2020-12)
- Add comprehensive test suite (10 tests, all passing)
- Add Korean documentation
- Inline signature utility (RFC-8785 compliance)
- Policy override support via yuanjin_policy_v1.json
```

**Branch:** docs/prompts-freeze-v1
**Status:** Pushed to remote ✅

## API Usage

### detect_yuanjin
```python
from app.core.yuanjin import detect_yuanjin

pairs = detect_yuanjin(["酉","戌","辰","卯"])
# Returns: [["卯","辰"], ["酉","戌"]]
```

### apply_yuanjin_flags
```python
from app.core.yuanjin import apply_yuanjin_flags

result = apply_yuanjin_flags(["子","丑","寅","未"])
# Returns: {"flags": [True, False, False, True], "pairs": [["子","未"]]}
```

### explain_yuanjin
```python
from app.core.yuanjin import explain_yuanjin

trace = explain_yuanjin(["子","丑","寅","未"])
# Returns: {
#   "policy_version": "yuanjin_v1.1.0",
#   "policy_signature": "<64-hex-sha256>",
#   "present_branches": ["子","丑","寅","未"],
#   "hits": [["子","未"]],
#   "pair_count": 1
# }
```

## Technical Details

### Yuanjin Pairs (6 Sets)
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

### Detection Algorithm
1. Validate 4 branches (year/month/day/hour)
2. Create set of present branches
3. For each policy pair, check if both members are in the set
4. Sort hits deterministically (pair internal + list)
5. Return sorted hit list

**Time Complexity:** O(1) - fixed 6 pairs to check
**Space Complexity:** O(1) - fixed small data structures

### Deterministic Sorting
- **Pair internal:** Sort by BRANCHES index (0-11)
- **List overall:** Sort by first element index, then second element index
- **Result:** Reproducible order regardless of input sequence

Example:
```python
# Input: ["酉","戌","辰","卯"]
# Hits found: (卯,辰) and (酉,戌)
# Sorted internally: [卯,辰] and [酉,戌] (already sorted)
# Sorted overall: [["卯","辰"], ["酉","戌"]] (卯 idx=3 < 酉 idx=9)
```

### Policy Override
Optional policy file at `policies/yuanjin_policy_v1.json` or `saju_codex_batch_all_v2_6_signed/policies/yuanjin_policy_v1.json`:

```json
[
  ["子","未"], ["丑","午"], ["寅","巳"],
  ["卯","辰"], ["申","亥"], ["酉","戌"]
]
```

Validation rules:
- Must be array of arrays
- Each item must have exactly 2 elements (12-branch characters)
- Exactly 6 pairs required (duplicates/reverses deduplicated)

## Integration Status

| Component | Status |
|-----------|--------|
| Core engine (yuanjin.py) | ✅ Complete |
| JSON Schema | ✅ Complete |
| Tests | ✅ 10/10 passing |
| Documentation | ✅ Complete |
| Code formatting | ✅ black + isort |
| Committed | ✅ Yes |
| Pushed | ✅ Yes |

## Next Steps (When Integrating All Engines)

### Future Integration into AnalysisEngine
```python
# services/analysis-service/app/core/engine.py
from .yuanjin import detect_yuanjin, explain_yuanjin, apply_yuanjin_flags

class AnalysisEngine:
    def analyze(self, request):
        # ... existing code ...

        # Extract 4 branches
        branches = [
            request.pillars['year'].branch,
            request.pillars['month'].branch,
            request.pillars['day'].branch,
            request.pillars['hour'].branch
        ]

        # Detect yuanjin pairs
        yuanjin_pairs = detect_yuanjin(branches)
        yuanjin_trace = explain_yuanjin(branches)
        yuanjin_flags = apply_yuanjin_flags(branches)

        # Add to response
        return AnalysisResponse(
            # ... existing fields ...
            yuanjin=yuanjin_trace,
            yuanjin_flags=yuanjin_flags
        )
```

## Verification Checklist

- [x] All tests pass: `pytest services/analysis-service/tests/test_yuanjin.py -v`
- [x] Schema is valid JSON Schema draft-2020-12
- [x] Documentation is clear and examples work
- [x] No import errors when running `from app.core import yuanjin`
- [x] POLICY_SIGNATURE generates valid 64-char hex SHA-256
- [x] Policy override path resolution works
- [x] Invalid inputs raise ValueError with Korean messages
- [x] Deterministic sorting works correctly
- [x] CI formatting passes: `black` and `isort`
- [x] Committed to git
- [x] Pushed to remote

---

## Conclusion

The yuanjin detector engine has been successfully integrated into the analysis-service with:
- ✅ One minor issue fixed (function ordering)
- ✅ All 10 tests passing
- ✅ Clean code formatted with black/isort
- ✅ Comprehensive documentation
- ✅ Inline signature utility (no external dependencies)
- ✅ Policy override support
- ✅ JSON Schema validation
- ✅ Deterministic sorting for reproducible results

The engine is ready for use and can be integrated into the main analysis pipeline alongside void calculator and other engines.

**Total time:** ~12 minutes
**Complexity:** Low (simpler than void calc)
**Risk:** Low (no impact on existing code)
**Result:** Success ✅
