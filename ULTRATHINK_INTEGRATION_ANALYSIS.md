# Ultrathink: Integration Gap Analysis

**Date:** 2025-10-12 KST  
**Analysis Duration:** 30 minutes  
**Engines Analyzed:** 2 (Relations_weighted, Shensha)

---

## 🔍 Analysis Summary

Both "missing" engines are **actually integrated** but have **implementation bugs** preventing them from working.

| Engine | Initialized | Called | Root Cause | Fix Complexity |
|--------|-------------|--------|------------|----------------|
| Relations_weighted | ✅ Line 131 | ✅ Line 182-184 | Data format mismatch | 🟡 MEDIUM (1-2h) |
| Shensha | ✅ Line 136 | ✅ Line 214 | Missing policy file structure | 🟢 EASY (30min) |

---

## Issue #1: Relations_weighted - Architectural Mismatch

### Current Implementation

**File:** `services/analysis-service/app/core/saju_orchestrator.py`

**Lines 653-687:** `_call_relation_weight()` method exists and is called

**The Bug:**
```python
# Line 663-668: Tries to flatten relations_result
for rel_type in ["he6", "sanhe", "chong", "xing", "po", "hai"]:
    items = relations_result.get(rel_type, [])  # ❌ These keys don't exist!
    for item in items:
        pair = {"type": rel_type, **item}
        pairs_detected.append(pair)
```

### Root Cause: Data Structure Mismatch

**RelationTransformer Output:**
```python
# File: app/core/relations.py:407-423
def _call_relations(...):
    result = self.relations.evaluate(ctx)
    
    # Returns only summary, NOT relation items:
    return {
        "priority_hit": result.priority_hit,  # e.g., "chong"
        "transform_to": result.transform_to,  # e.g., None
        "boosts": result.boosts,              # e.g., []
        "notes": result.notes,                # e.g., ["chong:巳/亥"]
        "extras": result.extras               # e.g., {five_he: {}, zixing: {}}
    }
```

**Problem:** No "chong", "he6", "sanhe" keys with actual pair lists!

### Why This Happened

`RelationTransformer` was designed to return only the **highest priority** relation, not all detected relations. This is evident in the code:

```python
# relations.py:95-140
def evaluate(self, ctx: RelationContext) -> RelationResult:
    # Iterates through priority rules
    for rule in self._priority:
        if rule == "chong":
            pair = self._check_pairs(...)
            if pair:
                # Returns ONLY this relation, stops checking others
                priority_entry = ("chong", None, [], ["chong:" + "/".join(pair)])
                break
```

### Solution Strategy

**Option A: Modify RelationTransformer (RISKY)**
- Change evaluate() to return ALL relations
- Breaks existing API contract
- Requires extensive testing

**Option B: Parse `notes` field (SAFER) ✅**
- Extract relation info from notes: ["chong:巳/亥"]
- Build pairs_detected list from parsed notes
- Non-breaking change
- Minimal code modification

**Implementation:**
```python
# In _call_relation_weight, replace lines 663-668:
pairs_detected = []
notes = relations_result.get("notes", [])

for note in notes:
    # Parse format: "type:branch1/branch2"
    if ":" in note:
        rel_type, branches_str = note.split(":", 1)
        if "/" in branches_str:
            branch1, branch2 = branches_str.split("/", 1)
            pairs_detected.append({
                "type": rel_type,
                "participants": [branch1, branch2],
                "formed": True
            })
```

**Estimated Effort:** 1-2 hours (implementation + testing)

---

## Issue #2: Shensha - Missing Policy File Structure

### Current Implementation

**File:** `services/common/saju_common/engines/shensha.py`

**Lines 26-39:** `list_enabled()` method

```python
def list_enabled(self, pro_mode: bool = False) -> Dict[str, object]:
    # Expects catalog structure:
    # {
    #   "default": {"enabled": bool, "list": [...]},
    #   "pro_mode": {"enabled": bool, "list": [...]}
    # }
    data = self._catalog.get("pro_mode" if pro_mode else "default", {})
    return {"enabled": data.get("enabled", False), "list": data.get("list", [])}
```

### Root Cause: Policy File Structure Mismatch

**Expected Structure:**
```json
{
  "version": "1.0",
  "default": {
    "enabled": true,
    "list": ["taohua", "wenchang", "tianyiguiren", "yima"]
  },
  "pro_mode": {
    "enabled": true,
    "list": ["taohua", "wenchang", "tianyiguiren", "yima", "huagai", "hongyan"]
  }
}
```

**Actual File:** `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
```json
{
  "version": "1.0",
  "policy": {...},  # ❌ Wrong structure!
  "items": [...]    # ❌ No "default" or "pro_mode" keys!
}
```

### Solution Strategy

**Option A: Fix Policy File (PREFERRED) ✅**
- Create correct structure with default/pro_mode
- Set `default.enabled: true`
- Map items to proper IDs

**Option B: Fix Code to Match File**
- More work, existing structure might be intentional

**Implementation:**
```json
{
  "version": "1.0",
  "policy": {
    "impact_on_calculation": false,
    "ui_mode": "pro_only"
  },
  "default": {
    "enabled": true,
    "list": [
      "taohua",
      "wenchang",
      "tianyiguiren",
      "yima"
    ]
  },
  "pro_mode": {
    "enabled": true,
    "list": [
      "taohua",
      "wenchang",
      "tianyiguiren",
      "yima",
      "huagai",
      "hongyan",
      "guchen",
      "guasu"
    ]
  },
  "items": [
    {
      "name": "桃花(도화)",
      "key": "taohua",
      "desc_modern": "표현/매력 강조, 대인 주목도 상승",
      "where_rule": "日支 in {子午卯酉} → 桃花"
    },
    ...
  ]
}
```

**Estimated Effort:** 30 minutes (file modification + testing)

---

## Execution Plan

### Phase 1: Fix Relations_weighted (1-2 hours)

1. **Modify `_call_relation_weight()` method**
   - File: `services/analysis-service/app/core/saju_orchestrator.py`
   - Lines: 663-668
   - Action: Parse `notes` field to build `pairs_detected` list

2. **Test with 2000-09-14 case**
   - Should see: `items: [{type: "chong", participants: ["巳", "亥"], impact_weight: 0.90}]`

3. **Create unit test**
   - Test note parsing logic
   - Test multiple relation types

### Phase 2: Fix Shensha (30 minutes)

1. **Update policy file**
   - File: `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
   - Add: `default` and `pro_mode` structures
   - Set: `default.enabled: true`

2. **Test with 2000-09-14 case**
   - Should see: `shensha: {enabled: true, list: ["taohua", ...]}`

### Phase 3: End-to-End Verification (30 minutes)

1. Run full orchestrator with test case
2. Verify both fixes working
3. Check for regressions
4. Update documentation

**Total Estimated Time:** 2-3 hours

---

## Key Insights

### 1. Integration ≠ Working
Both engines were "integrated" (initialized, called) but not working due to bugs. The audit report correctly identified them as "not working" but the root causes were subtle.

### 2. Architectural Mismatches
The RelationTransformer/RelationWeightEvaluator mismatch shows that even when both engines exist, they may have incompatible data contracts.

### 3. Policy File Evolution
The shensha policy file structure evolved but the code wasn't updated (or vice versa), causing a mismatch.

### 4. Testing Gaps
Unit tests would have caught both issues:
- Test that relations_weighted.items is populated
- Test that shensha.enabled returns true

---

## Recommendations

### Immediate Actions
1. Fix both issues as outlined above
2. Add integration tests for these flows
3. Document data contracts between engines

### Long-term Improvements
1. **API Contract Validation:** Add runtime checks for data structure expectations
2. **Policy File Validation:** Add JSON schema validation on load
3. **Integration Tests:** Test data flow between connected engines
4. **Documentation:** Document each engine's input/output format

---

**Analysis Complete**  
**Next Step:** Implement Phase 1 (Relations_weighted fix)
