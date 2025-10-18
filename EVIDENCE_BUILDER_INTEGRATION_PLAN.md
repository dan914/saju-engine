# Evidence Builder Integration Plan (ULTRATHINK)

**Component:** Evidence Builder v1.0
**Type:** Meta-Engine / Orchestration Layer
**Date:** 2025-10-08 KST
**Status:** 🔍 Analysis Phase

---

## Executive Summary

Evidence Builder is a **meta-engine** that collects Stage-1 engine outputs (void, yuanjin, wuxing_adjust) into a single unified Evidence object with:

- **Deterministic sorting** by section type
- **RFC-8785 canonical JSON** + SHA-256 signatures
- **Section-level signatures** (each engine output signed separately)
- **Evidence-level signature** (entire collection signed)
- **Shared timestamp** (all sections use same `created_at` for determinism)
- **Optional sections** (can include subset of engines)
- **Type uniqueness** (no duplicate section types)
- **KO-first** annotations

**Purpose:** Provide auditable, reproducible evidence trail for `/report` generation pipeline.

---

## Architecture Analysis

### Input Flow
```
Stage-1 Engines (3)
├─ void.explain_void() → {policy_version, policy_signature, kong, ...}
├─ yuanjin.explain_yuanjin() → {policy_version, policy_signature, hits, ...}
└─ combination_element.transform_wuxing() → {dist, trace}
         ↓
Evidence Builder
├─ Normalize inputs → sections[]
├─ Add section_signature to each
├─ Sort by type (deterministic)
└─ Add evidence_signature to whole
         ↓
Evidence Object (JSON)
{
  "evidence_version": "evidence_v1.0.0",
  "evidence_signature": "<64-hex>",
  "sections": [
    {
      "type": "void",
      "engine_version": "void_calc_v1.1.0",
      "engine_signature": "<64-hex>",
      "source": "core/policy_engines/void_calc.py",
      "payload": {...},
      "created_at": "2024-01-01T00:00:00Z",
      "section_signature": "<64-hex>"
    },
    ...
  ]
}
```

### Dependencies
```
evidence_builder.py
├─ REQUIRES: infra.signatures (sha256_signature, canonical_dumps)
│  └─ SOLUTION: Inline utility (like other engines)
├─ IMPORTS: void.py (optional, for payload validation)
├─ IMPORTS: yuanjin.py (optional, for payload validation)
├─ IMPORTS: combination_element.py (for POLICY_VERSION, POLICY_SIGNATURE)
└─ EXPORTS: build_evidence(), add_section(), finalize_evidence()
```

---

## File Mapping

### 1. evidence_builder.py
**Source:** `core/evidence/evidence_builder.py`
**Target:** `services/analysis-service/app/core/evidence_builder.py`

**Changes needed:**
```python
# BEFORE:
from infra.signatures import canonical_dumps, sha256_signature

# AFTER:
import hashlib
import json

def _canonical_json_signature(obj) -> str:
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

# Alias for compatibility
sha256_signature = _canonical_json_signature
canonical_dumps = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

**Import path updates:**
```python
# Line ~114 (wuxing_adjust normalization):
# BEFORE:
from core.policy_engines.combination_element import POLICY_VERSION as _WV, POLICY_SIGNATURE as _WS

# AFTER:
from app.core.combination_element import POLICY_VERSION as _WV, POLICY_SIGNATURE as _WS
```

**Source path updates:**
```python
# Line ~82 (void section):
"source": "services/analysis-service/app/core/void.py",

# Line ~99 (yuanjin section):
"source": "services/analysis-service/app/core/yuanjin.py",

# Line ~121 (wuxing_adjust section):
"source": "services/analysis-service/app/core/combination_element.py",
```

### 2. evidence.schema.json
**Source:** `core/schemas/evidence.schema.json`
**Target:** `services/analysis-service/schemas/evidence.schema.json`

**No changes needed** - Schema is standalone JSON

### 3. test_evidence_builder.py
**Source:** `tests/evidence/test_evidence_builder.py`
**Target:** `services/analysis-service/tests/test_evidence_builder.py`

**Changes needed:**
```python
# BEFORE:
from infra.signatures import sha256_signature
from core.evidence import evidence_builder as eb
from core.policy_engines.combination_element import POLICY_SIGNATURE as WUX_SIG, POLICY_VERSION as WUX_VER

# AFTER:
from app.core import evidence_builder as eb
from app.core.combination_element import POLICY_SIGNATURE as WUX_SIG, POLICY_VERSION as WUX_VER

# Inline sha256_signature for tests
import hashlib
import json

def sha256_signature(obj):
    canonical_str = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
```

**Schema path update:**
```python
# Line ~115 (test_schema_presence_and_patterns):
# BEFORE:
schema = json.loads(Path("core/schemas/evidence.schema.json").read_text(encoding="utf-8"))

# AFTER:
schema = json.loads(Path(__file__).parent.parent / "schemas" / "evidence.schema.json").read_text(encoding="utf-8"))
```

### 4. evidence_builder.md
**Source:** `docs/engines/evidence_builder.md`
**Target:** `docs/engines/evidence_builder.md`

**Changes needed:**
- Update source paths to `services/analysis-service/app/core/*.py`
- Add integration examples with AnalysisEngine

---

## Integration Points

### With Existing Engines

**Void Calculator:**
```python
from app.core import void as vc
from app.core import evidence_builder as eb

# Compute void
day_pillar = "乙丑"
void_result = vc.explain_void(day_pillar)

# Build evidence
evidence = eb.build_evidence({"void": void_result})
```

**Yuanjin Detector:**
```python
from app.core import yuanjin as yj

branches = ["子", "丑", "寅", "未"]
yuanjin_result = yj.explain_yuanjin(branches)

evidence = eb.build_evidence({"yuanjin": yuanjin_result})
```

**Combination Element:**
```python
from app.core import combination_element as ce

relations = {...}
dist_raw = {...}
dist, trace = ce.transform_wuxing(relations, dist_raw)

wuxing_result = {
    "engine_version": ce.POLICY_VERSION,
    "engine_signature": ce.POLICY_SIGNATURE,
    "dist": dist,
    "trace": trace
}

evidence = eb.build_evidence({"wuxing_adjust": wuxing_result})
```

**Combined Evidence (All 3):**
```python
inputs = {
    "void": void_result,
    "yuanjin": yuanjin_result,
    "wuxing_adjust": wuxing_result
}
evidence = eb.build_evidence(inputs)

# Result:
{
  "evidence_version": "evidence_v1.0.0",
  "evidence_signature": "<64-hex>",
  "sections": [
    {"type": "void", ...},           # Sorted: void
    {"type": "wuxing_adjust", ...},  # Sorted: wuxing_adjust
    {"type": "yuanjin", ...}         # Sorted: yuanjin
  ]
}
```

### With AnalysisEngine

**Future integration (Phase 2):**
```python
# services/analysis-service/app/core/engine.py

class AnalysisEngine:
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        # ... existing logic ...

        # Build evidence from Stage-1 engines
        from app.core import evidence_builder as eb

        evidence_inputs = {}

        # Void calculation
        if request.options.get("include_void", True):
            void_result = self._compute_void(pillars)
            evidence_inputs["void"] = void_result

        # Yuanjin detection
        if request.options.get("include_yuanjin", True):
            yuanjin_result = self._detect_yuanjin(pillars)
            evidence_inputs["yuanjin"] = yuanjin_result

        # Wuxing adjustment
        if request.options.get("include_wuxing_adjust", True):
            wuxing_result = self._adjust_wuxing(relations, dist_raw)
            evidence_inputs["wuxing_adjust"] = wuxing_result

        # Build evidence
        evidence = eb.build_evidence(evidence_inputs)

        # Attach to response
        response.evidence = evidence

        return response
```

---

## API Surface

### build_evidence(inputs: dict) -> dict
**Primary API** - Collect engine outputs into Evidence

**Parameters:**
- `inputs`: Dict with optional keys: `void`, `yuanjin`, `wuxing_adjust`

**Returns:**
```python
{
  "evidence_version": "evidence_v1.0.0",
  "evidence_signature": "<64-hex>",
  "sections": [
    {
      "type": "void|yuanjin|wuxing_adjust",
      "engine_version": "<engine_version>",
      "engine_signature": "<64-hex>",
      "source": "<file_path>",
      "payload": {...},
      "created_at": "YYYY-MM-DDTHH:MM:SSZ",
      "section_signature": "<64-hex>"
    }
  ]
}
```

**Raises:**
- `ValueError`: If required fields missing in inputs
- `ValueError`: If duplicate section type

### add_section(ev: dict, section: dict) -> dict
**Manual section addition** - For advanced use cases

**Raises:**
- `ValueError`: If section type duplicated
- `ValueError`: If section format invalid

### finalize_evidence(ev: dict) -> dict
**Finalization** - Sort sections + compute evidence_signature

**Raises:**
- `ValueError`: If sections empty

---

## Testing Strategy

### Test Coverage Matrix

| Test Case | Purpose | Expected |
|-----------|---------|----------|
| `test_build_evidence_with_three_sections_and_order` | Full integration | 3 sections, sorted by type |
| `test_optional_single_section` | Partial input | 1 section, valid signatures |
| `test_duplicate_type_add_raises` | Type uniqueness | ValueError |
| `test_schema_presence_and_patterns` | Schema validation | Patterns match |
| `test_deterministic_signature_same_inputs` | Idempotency | Same inputs → same signatures |
| `test_finalize_error_on_empty_sections` | Empty validation | ValueError |
| `test_invalid_created_at_in_add_section` | Timestamp validation | ValueError |

**Target:** 7 tests passing

### Test Data Requirements

**Void sample:**
```python
{
  "policy_version": "void_calc_v1.1.0",
  "policy_signature": "<64-hex>",
  "day_index": 1,
  "xun_start": 0,
  "kong": ["戌", "亥"]
}
```

**Yuanjin sample:**
```python
{
  "policy_version": "yuanjin_v1.1.0",
  "policy_signature": "<64-hex>",
  "present_branches": ["子", "丑", "寅", "未"],
  "hits": [["子", "未"]],
  "pair_count": 1
}
```

**Wuxing sample:**
```python
{
  "engine_version": "combination_element_v1.2.0",
  "engine_signature": "<64-hex>",
  "dist": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
  "trace": [
    {
      "reason": "sanhe",
      "target": "water",
      "moved_ratio": 0.20,
      "weight": 0.20,
      "order": 1,
      "policy_signature": "<64-hex>"
    }
  ]
}
```

---

## Signature Mechanics

### Section Signature
Computed from canonical JSON of **6 required fields** only:
```python
section_base = {
  "type": "void",
  "engine_version": "void_calc_v1.1.0",
  "engine_signature": "<64-hex>",
  "source": "services/analysis-service/app/core/void.py",
  "payload": {...},
  "created_at": "2024-01-01T00:00:00Z"
}
section_signature = sha256(canonical_json(section_base))
```

### Evidence Signature
Computed from **2 fields** only:
```python
evidence_base = {
  "evidence_version": "evidence_v1.0.0",
  "sections": [...]  # Full sections with section_signature
}
evidence_signature = sha256(canonical_json(evidence_base))
```

**Why separate signatures?**
- **Section signature** = Verify individual engine output integrity
- **Evidence signature** = Verify entire collection integrity
- **Two-level verification** = Detect tampering at section or evidence level

---

## Determinism Guarantees

### Timestamp Freezing
All sections share **same `created_at`** timestamp:
```python
created_at = _now_utc_iso()  # "2024-01-01T00:00:00Z"
for sec in sections:
    sec["created_at"] = created_at  # Shared timestamp
```

**Why?** Same inputs → same signatures (idempotent)

### Sorting
Sections sorted by `type` (alphabetical):
```python
ev["sections"] = sorted(ev["sections"], key=lambda s: s["type"])
# Result: ["void", "wuxing_adjust", "yuanjin"]
```

**Why?** Order independence → deterministic signature

### Canonical JSON
```python
json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

**Why?** Dict key order → deterministic serialization

---

## Policy Specification

```python
POLICY_SPEC = {
  "version": "evidence_v1.0.0",
  "allowed_types": ["void", "yuanjin", "wuxing_adjust", "shensha", "relation_hits", "strength"],
  "required_fields": ["type", "engine_version", "engine_signature", "source", "payload", "created_at"],
  "created_at_format": "YYYY-MM-DDTHH:MM:SSZ"
}
```

**Extensibility:**
- `allowed_types` can be extended (shensha, relation_hits, strength planned)
- Each section type has flexible `payload` (type-specific structure)

---

## Error Handling

### Input Validation
```python
# Missing required field
inputs = {"void": {"policy_version": "v1.1.0"}}  # Missing kong
# → ValueError: "void 입력에 필수 키 누락: kong"

# Invalid type
inputs = {"unknown": {...}}
# → (Silently ignored - only known types processed)
```

### Section Validation
```python
# Duplicate type
ev = build_evidence({"void": void_result})
add_section(ev, void_section_again)
# → ValueError: "섹션 타입 중복: void"

# Invalid created_at
section = {
    "type": "void",
    "created_at": "2024-01-01 00:00:00Z"  # Space instead of T
    # ...
}
# → ValueError: "created_at은 UTC ISO8601(Z) 형식이어야 합니다."
```

### Finalization Validation
```python
# Empty sections
ev = {"evidence_version": "v1.0.0", "sections": []}
finalize_evidence(ev)
# → ValueError: "sections가 비어 있습니다."
```

---

## Schema Structure

### Evidence Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "evidence",
  "type": "object",
  "required": ["evidence_version", "evidence_signature", "sections"],
  "properties": {
    "evidence_version": {"type": "string", "minLength": 1},
    "evidence_signature": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "engine_version", "engine_signature", "source", "payload", "created_at", "section_signature"],
        "properties": {
          "type": {"type": "string", "enum": ["void", "yuanjin", "wuxing_adjust", "shensha", "relation_hits", "strength"]},
          "engine_version": {"type": "string", "minLength": 1},
          "engine_signature": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
          "source": {"type": "string", "minLength": 1},
          "payload": {"type": "object"},
          "created_at": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"},
          "section_signature": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
        }
      }
    }
  }
}
```

**Key constraints:**
- `evidence_signature`: 64-char hex (SHA-256)
- `section_signature`: 64-char hex (SHA-256)
- `created_at`: ISO8601 with Z (UTC only)
- `type`: Enum of 6 allowed types
- `payload`: Flexible object (type-specific)

---

## Implementation Checklist

### Phase 1: Core Module
- [ ] Create `app/core/evidence_builder.py`
  - [ ] Replace `infra.signatures` with inline utility
  - [ ] Update import paths (`app.core.*`)
  - [ ] Update source paths (services/analysis-service/...)
  - [ ] Add docstrings (Korean + English)
- [ ] Create `schemas/evidence.schema.json`
  - [ ] Copy as-is (no changes)

### Phase 2: Tests
- [ ] Create `tests/test_evidence_builder.py`
  - [ ] Replace `infra.signatures` with inline utility
  - [ ] Update import paths (`app.core.*`)
  - [ ] Fix schema path (use `Path(__file__).parent.parent`)
  - [ ] Add 7 test cases
- [ ] Run tests: `pytest tests/test_evidence_builder.py -v`
- [ ] Target: **7/7 passing**

### Phase 3: Documentation
- [ ] Create `docs/engines/evidence_builder.md`
  - [ ] Update paths to analysis-service
  - [ ] Add integration examples
  - [ ] Add signature verification examples
- [ ] Update `CLAUDE.md` with Evidence Builder entry
- [ ] Update `ENGINE_INTEGRATION_SESSION_REPORT.md`

### Phase 4: Integration (Future)
- [ ] Integrate with AnalysisEngine
- [ ] Add `evidence` field to AnalysisResponse
- [ ] Add options for optional sections
- [ ] Update API docs

---

## Risks and Mitigations

### Risk 1: Import Circular Dependency
**Issue:** `evidence_builder` imports `combination_element`, which might import from `evidence_builder` in future

**Mitigation:**
- Keep `evidence_builder` as **pure orchestration** layer (no business logic)
- Engines should NOT import `evidence_builder`
- If needed, use lazy imports (`try/except` blocks already present)

### Risk 2: Timestamp Variability
**Issue:** `_now_utc_iso()` returns different values each call → non-deterministic signatures

**Mitigation:**
- Tests use `monkeypatch` to freeze timestamp
- Production code uses single call at start of `build_evidence()`
- All sections share **same timestamp** (determinism preserved)

### Risk 3: Schema Evolution
**Issue:** Adding new section types breaks old Evidence objects

**Mitigation:**
- `allowed_types` is extensible (append-only)
- Old Evidence objects remain valid (subset of types)
- Schema versioning (`evidence_version` field)

### Risk 4: Signature Mismatch
**Issue:** Different JSON serialization → different signatures

**Mitigation:**
- Use **canonical JSON** (sort_keys=True, separators=(",", ":"))
- Same as other engines (consistent approach)
- Tests verify deterministic signatures

---

## Success Criteria

1. ✅ All 7 tests passing
2. ✅ No import errors
3. ✅ Deterministic signatures (same inputs → same output)
4. ✅ Schema validation passes
5. ✅ Integration with existing 3 engines works
6. ✅ Code formatted (black + isort)
7. ✅ Documentation complete

---

## Timeline Estimate

- **Phase 1 (Core):** 20 minutes
- **Phase 2 (Tests):** 15 minutes
- **Phase 3 (Docs):** 10 minutes
- **Total:** ~45 minutes

---

## Next Steps

1. **User approval** - Review this plan
2. **Implementation** - Follow Phase 1-3 checklist
3. **Verification** - Run all tests (target: 7/7 passing)
4. **Documentation** - Create/update docs
5. **Commit** - Single commit with all files
6. **Report** - Update integration report

---

## Open Questions

1. **Should Evidence be attached to AnalysisResponse now, or Phase 2?**
   - Recommendation: Phase 2 (keep engines standalone per user request)

2. **Do we need Evidence validation in AnalysisEngine?**
   - Recommendation: Yes, but Phase 2 (after integration)

3. **Should we add Evidence to SAJU_REPORT_SCHEMA_v1.0?**
   - Recommendation: Yes, but Phase 2 (update schema + samples)

---

## Conclusion

Evidence Builder is a **critical orchestration layer** that will enable:
- **Auditability** - Full trace of engine outputs
- **Reproducibility** - Deterministic signatures
- **Verification** - Two-level signature validation
- **Extensibility** - Easy to add new engine types

**Status:** Ready for implementation pending user approval.

**Recommendation:** Proceed with Phase 1-3 now, defer AnalysisEngine integration to Phase 2 (per user's earlier request to wait until all engines ready).
