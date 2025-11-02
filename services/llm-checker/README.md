# LLM Guard/Checker Service - WIP

**Status:** ⚠️ Work In Progress - Not Production Ready

**Version:** 0.1.0-WIP

**Estimated Effort to MVP:** 4-6 hours

---

## Current State

This service is a FastAPI skeleton that provides the basic health check endpoint via `create_service_app()` from `services.common`. It does **NOT** currently implement any LLM Guard validation logic.

**What Works:**
- Health check endpoint (via common service app)
- Basic FastAPI application structure
- Service metadata (app name, version, rule_id)

**What's Missing:**
- LLM Guard v1.1 pre-generation validation
- Post-generation validation
- 6 guard families implementation
- Verdict logic (allow/block/revise)
- Policy loader for llm_guard_policy_v1.1.json
- Comprehensive tests

---

## What This Service Should Do

The LLM Guard/Checker Service validates LLM inputs and outputs to ensure they comply with policy constraints. It should:

1. **Pre-Generation Validation:**
   - Check template variables are within policy bounds
   - Verify no prohibited content in input
   - Ensure deterministic fields aren't being overridden
   - Validate trace integrity (evidence chains)
   - Return verdict: `allow` / `block` + reason

2. **Post-Generation Validation:**
   - Verify generated text matches policy constraints
   - Check for prohibited content (harm guard)
   - Validate Korean-first labels (KO_FIRST_LABELS)
   - Ensure no hallucinated data (EVIDENCE_BOUND)
   - Return verdict: `allow` / `block` / `revise` + reason

3. **Guard Families (6 total):**
   - **DETERMINISM**: Engine-calculated values must not change
   - **TRACE_INTEGRITY**: Evidence chains must be verifiable
   - **EVIDENCE_BOUND**: All claims must have evidence
   - **POLICY_BOUND**: Stay within policy-defined ranges
   - **KO_FIRST_LABELS**: Korean labels must be present
   - **HARM_GUARD**: No medical/legal/investment advice

---

## TODO Checklist

- [ ] Add LLM Guard v1.1 pre-generation validation routes (`POST /guard/pre`)
- [ ] Add post-generation validation routes (`POST /guard/post`)
- [ ] Implement DETERMINISM guard family
- [ ] Implement TRACE_INTEGRITY guard family
- [ ] Implement EVIDENCE_BOUND guard family
- [ ] Implement POLICY_BOUND guard family
- [ ] Implement KO_FIRST_LABELS guard family
- [ ] Implement HARM_GUARD guard family
- [ ] Add verdict logic (allow/block/revise)
- [ ] Add policy loader for `llm_guard_policy_v1.1.json`
- [ ] Add comprehensive tests (all 6 families + cross-engine)
- [ ] Add integration with llm-polish service
- [ ] Add logging/monitoring for violations
- [ ] Add metrics dashboard (violations by family)

---

## Implementation Notes

### Example: Pre-Generation Validation Route

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

router = APIRouter(tags=["guard"])

class PreValidationRequest(BaseModel):
    template_id: str
    variables: dict
    engine_outputs: dict  # Raw engine outputs for comparison

class ValidationVerdict(BaseModel):
    verdict: Literal["allow", "block"]
    reason: str | None
    violated_rules: list[str]

@router.post("/guard/pre", response_model=ValidationVerdict)
async def validate_pre_generation(request: PreValidationRequest):
    """Validate inputs before LLM generation."""
    from app.guard import LLMGuard

    guard = LLMGuard.from_file("policy/llm_guard_policy_v1.1.json")

    # Run all 6 guard families
    violations = []

    # 1. DETERMINISM: Check if trying to override engine outputs
    determinism_check = guard.check_determinism(
        variables=request.variables,
        engine_outputs=request.engine_outputs,
    )
    if not determinism_check["passed"]:
        violations.append({
            "family": "DETERMINISM",
            "rule": determinism_check["rule_id"],
            "reason": determinism_check["reason"],
        })

    # 2. TRACE_INTEGRITY: Verify evidence chains
    trace_check = guard.check_trace_integrity(
        variables=request.variables,
        engine_outputs=request.engine_outputs,
    )
    if not trace_check["passed"]:
        violations.append({
            "family": "TRACE_INTEGRITY",
            "rule": trace_check["rule_id"],
            "reason": trace_check["reason"],
        })

    # 3. POLICY_BOUND: Check values are within policy ranges
    policy_check = guard.check_policy_bounds(
        variables=request.variables,
        engine_outputs=request.engine_outputs,
    )
    if not policy_check["passed"]:
        violations.append({
            "family": "POLICY_BOUND",
            "rule": policy_check["rule_id"],
            "reason": policy_check["reason"],
        })

    # Verdict
    if violations:
        return ValidationVerdict(
            verdict="block",
            reason=f"Failed {len(violations)} guard checks",
            violated_rules=[v["rule"] for v in violations],
        )
    else:
        return ValidationVerdict(
            verdict="allow",
            reason=None,
            violated_rules=[],
        )
```

### Example: Post-Generation Validation Route

```python
class PostValidationRequest(BaseModel):
    template_id: str
    variables: dict
    generated_text: str
    engine_outputs: dict

class PostValidationVerdict(BaseModel):
    verdict: Literal["allow", "block", "revise"]
    reason: str | None
    violated_rules: list[str]
    suggested_fixes: list[str] | None

@router.post("/guard/post", response_model=PostValidationVerdict)
async def validate_post_generation(request: PostValidationRequest):
    """Validate LLM output after generation."""
    from app.guard import LLMGuard

    guard = LLMGuard.from_file("policy/llm_guard_policy_v1.1.json")

    violations = []

    # 4. EVIDENCE_BOUND: Check all claims have evidence
    evidence_check = guard.check_evidence_bound(
        generated_text=request.generated_text,
        engine_outputs=request.engine_outputs,
    )
    if not evidence_check["passed"]:
        violations.append({
            "family": "EVIDENCE_BOUND",
            "rule": evidence_check["rule_id"],
            "reason": evidence_check["reason"],
            "severity": "high",
        })

    # 5. KO_FIRST_LABELS: Verify Korean labels are present
    ko_check = guard.check_ko_first_labels(
        generated_text=request.generated_text,
    )
    if not ko_check["passed"]:
        violations.append({
            "family": "KO_FIRST_LABELS",
            "rule": ko_check["rule_id"],
            "reason": ko_check["reason"],
            "severity": "medium",
        })

    # 6. HARM_GUARD: Check for prohibited content
    harm_check = guard.check_harm_guard(
        generated_text=request.generated_text,
    )
    if not harm_check["passed"]:
        violations.append({
            "family": "HARM_GUARD",
            "rule": harm_check["rule_id"],
            "reason": harm_check["reason"],
            "severity": "critical",
        })

    # Verdict logic
    if any(v["severity"] == "critical" for v in violations):
        return PostValidationVerdict(
            verdict="block",
            reason="Critical violation detected",
            violated_rules=[v["rule"] for v in violations],
            suggested_fixes=None,
        )
    elif violations:
        return PostValidationVerdict(
            verdict="revise",
            reason=f"{len(violations)} violations, retry recommended",
            violated_rules=[v["rule"] for v in violations],
            suggested_fixes=[
                "Use lower temperature (0.3)",
                "Add explicit Korean label constraints",
                "Include evidence citations",
            ],
        )
    else:
        return PostValidationVerdict(
            verdict="allow",
            reason=None,
            violated_rules=[],
            suggested_fixes=None,
        )
```

### Example: DETERMINISM Guard Implementation

```python
class LLMGuard:
    def __init__(self, policy: dict):
        self.policy = policy
        self.determinism_rules = policy["guard_families"]["DETERMINISM"]

    def check_determinism(self, variables: dict, engine_outputs: dict) -> dict:
        """
        DETERMINISM Guard Family.

        Rule: LLM must not modify engine-calculated deterministic values.

        Examples:
        - strength.level (from StrengthEvaluator)
        - relations.chong (from RelationTransformer)
        - structure.primary (from StructureDetector)
        """
        for rule in self.determinism_rules["rules"]:
            field_path = rule["field"]
            engine_value = self._get_nested(engine_outputs, field_path)
            variable_value = variables.get(field_path)

            if variable_value is not None and variable_value != engine_value:
                return {
                    "passed": False,
                    "rule_id": rule["rule_id"],
                    "reason": f"Attempted to override {field_path}: {engine_value} → {variable_value}",
                }

        return {"passed": True}

    def _get_nested(self, data: dict, path: str):
        """Get nested value from dict using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            value = value.get(key, {})
        return value
```

### Example: HARM_GUARD Implementation

```python
def check_harm_guard(self, generated_text: str) -> dict:
    """
    HARM_GUARD Family.

    Rule: LLM must not provide medical/legal/investment advice.

    Prohibited patterns:
    - "병원에 가세요" → "전문가와 상담하세요"
    - "이 주식을 사세요" → "투자는 신중히 결정하세요"
    - "이혼하세요" → "관계 전문가와 상담하세요"
    """
    prohibited_patterns = self.policy["guard_families"]["HARM_GUARD"]["prohibited"]

    for pattern in prohibited_patterns:
        if pattern["regex"]:
            import re
            if re.search(pattern["pattern"], generated_text):
                return {
                    "passed": False,
                    "rule_id": pattern["rule_id"],
                    "reason": f"Prohibited pattern: {pattern['description']}",
                }
        elif pattern["pattern"] in generated_text:
            return {
                "passed": False,
                "rule_id": pattern["rule_id"],
                "reason": f"Prohibited content: {pattern['description']}",
            }

    return {"passed": True}
```

---

## Guard Families Reference

| Family | Purpose | Check Point | Severity |
|--------|---------|-------------|----------|
| **DETERMINISM** | Prevent engine output modification | Pre-generation | Critical |
| **TRACE_INTEGRITY** | Verify evidence chains | Pre-generation | High |
| **EVIDENCE_BOUND** | All claims need evidence | Post-generation | High |
| **POLICY_BOUND** | Stay within policy ranges | Pre-generation | Medium |
| **KO_FIRST_LABELS** | Korean labels required | Post-generation | Medium |
| **HARM_GUARD** | No harmful advice | Post-generation | Critical |

---

## Testing Strategy

1. **Unit Tests:**
   - Test each guard family independently
   - Verify all rule IDs from policy
   - Test edge cases (empty strings, null values)

2. **Integration Tests:**
   - Test with real engine outputs
   - Verify verdict logic (allow/block/revise)
   - Test cross-engine validation

3. **Regression Tests:**
   - Test against known violations
   - Verify fixes don't break existing checks
   - Test policy version upgrades

4. **Load Tests:**
   - Measure validation latency (< 100ms target)
   - Test concurrent validation requests
   - Verify no false positives under load

---

## Dependencies

**Required Services:**
- None (standalone validation service)

**Python Packages:**
- fastapi
- pydantic
- jsonschema (for policy validation)

**Policy Files:**
- `policy/llm_guard_policy_v1.1.json` (guard rules)
- `saju_codex_batch_all_v2_6_signed/policies/strength_policy_v2.json` (for POLICY_BOUND)
- `saju_codex_batch_all_v2_6_signed/policies/relation_policy.json` (for POLICY_BOUND)

---

## Next Steps

1. Implement LLMGuard class (2 hours)
2. Add all 6 guard families (2 hours)
3. Add pre/post validation routes (1 hour)
4. Add policy loader (0.5 hours)
5. Add comprehensive tests (2 hours)
6. Add logging/monitoring (0.5 hours)

**Total Estimated Effort:** 4-6 hours

---

## References

- **LLM_GUARD_V1_ANALYSIS_AND_PLAN.md** - Detailed implementation plan (730 lines)
- **policy/llm_guard_policy_v1.1.json** - Guard rules policy
- **guards/llm_guard_rules_*.json** - Guard rules for specific engines
