# Climate Balancer v1.0 - Design Document

**Version:** v1.0 (MVP)
**Date:** 2025-10-09 KST
**Status:** Deterministic policy-based implementation

---

## 1. Overview

Climate Balancer MVP는 **완전 결정적(Deterministic)** 형태의 조후 조언 매핑 엔진입니다.

### Key Design Principles

1. **No LLM Generation**: 정책 파일 기반 단순 매칭 → 모델 교체 무영향
2. **Single Rule Match**: AND 조건으로 최초 1건 매칭 → 우선순위는 순서
3. **Single Line Output**: 한 줄 조언만 반환 (80자 제한)
4. **Policy Signature**: RFC-8785 JCS + SHA-256 서명으로 무결성 보장

---

## 2. Architecture

### 2.1 Data Flow

```
Engine Summaries v1.1
  ├─ strength: { phase, elements }
  ├─ climate: { flags }
  └─ context: { season, month_branch }
        ↓
Climate Balancer MVP (match.py)
  ├─ Load policy/climate_advice_policy_v1.json
  ├─ Iterate advice_table (top-down)
  └─ Match first rule (AND conditions)
        ↓
Output: { advice, matched_policy_id, evidence_ref }
```

### 2.2 Matching Algorithm

```python
for rule in policy["advice_table"]:
    when = rule["when"]

    # Condition 1: season (OR within list)
    if "season" in when:
        if context.season not in when["season"]:
            continue

    # Condition 2: strength_phase (OR within list)
    if "strength_phase" in when:
        if strength.phase not in when["strength_phase"]:
            continue

    # Condition 3: balance (AND - all keys must match exactly)
    if "balance" in when:
        for element, level in when["balance"].items():
            if strength.elements[element] != level:
                continue to next rule

    # Condition 4: imbalance_flags (AND - all flags must exist)
    if "imbalance_flags" in when:
        for flag in when["imbalance_flags"]:
            if flag not in climate.flags:
                continue to next rule

    # All conditions met → MATCH
    return rule["id"], rule["advice"]

# No match → fallback
return None, policy["output"]["fallback"]
```

---

## 3. Policy Structure

### 3.1 Rule Example

```json
{
  "id": "WOOD_OVER_FIRE_WEAK",
  "when": {
    "season": ["봄"],
    "strength_phase": ["왕", "상"],
    "balance": { "wood": "high", "fire": "low" }
  },
  "advice": "불기운을 보강해 과다한 목의 발산을 순환시켜 주세요.",
  "rationale": "목왕하화약 → 생극순환 보정",
  "severity": "medium"
}
```

### 3.2 Rule Coverage

| Season | Rule Count | Coverage |
|--------|------------|----------|
| 봄 (Spring) | 1 | 목왕하화약 |
| 여름 (Summer) | 2 | 화왕수약, 토과건조 |
| 장하 (Late Summer) | 2 | 토과건조, 토습 |
| 가을 (Autumn) | 2 | 금왕목쇠, 추조금강 |
| 겨울 (Winter) | 2 | 동절수부족, 한수과다 |
| **Total** | **8** | **All seasons** |

### 3.3 Priority Order

Rules are matched **top-to-bottom** in `advice_table`. More specific rules (more conditions) should be placed **higher** to prevent premature matching by general rules.

**Example Priority:**
1. `EARTH_EXCESS_HUMIDITY` (season + flags) → specific
2. `FIRE_OVER_WATER_WEAK` (season + phase + balance) → medium
3. Fallback (no conditions) → general

---

## 4. Input Contract

### 4.1 Engine Summaries v1.1 Extensions

```json
{
  "strength": {
    "phase": "왕|상|휴|수|사",
    "elements": {
      "wood": "low|normal|high",
      "fire": "low|normal|high",
      "earth": "low|normal|high",
      "metal": "low|normal|high",
      "water": "low|normal|high"
    }
  },
  "climate": {
    "flags": ["earth_excess", "dryness", "humidity", "coldness"]
  },
  "context": {
    "season": "봄|여름|장하|가을|겨울",
    "month_branch": "string"
  }
}
```

### 4.2 Field Descriptions

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `strength.phase` | enum | StrengthEvaluator | 왕상휴수사 (Wang state) |
| `strength.elements` | object | StrengthEvaluator | 5원소별 강도 (low/normal/high) |
| `climate.flags` | array | ClimateEvaluator | 불균형 플래그 (optional) |
| `context.season` | enum | BRANCH_TO_SEASON | 계절 매핑 |
| `context.month_branch` | string | Pillars | 월지 |

---

## 5. Output Contract

### 5.1 Response Schema

```json
{
  "advice": "string (1 line, ≤80 chars)",
  "matched_policy_id": "string | null",
  "evidence_ref": "string"
}
```

### 5.2 Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `advice` | string | 한 줄 조언 (fallback 포함) |
| `matched_policy_id` | string \| null | 매칭된 규칙 ID (없으면 null) |
| `evidence_ref` | string | Evidence bundle 참조 경로 |

---

## 6. LLM Guard Rules

### 6.1 Climate MVP Guards

| Rule ID | Description | Severity | Action |
|---------|-------------|----------|--------|
| CLIMATE-ADVICE-001 | advice 있을 때 policy_id 필수 | medium | revise |
| CLIMATE-ADVICE-002 | advice는 한 줄만 허용 | low | revise |
| CLIMATE-ADVICE-003 | 문자 수 ≤80 제한 | low | revise |

### 6.2 Rationale

- **CLIMATE-ADVICE-001**: 조언이 있으면 반드시 정책 매칭 근거 필요
- **CLIMATE-ADVICE-002**: 모델 교체 시 생성 편차 방지 (단일 문장 강제)
- **CLIMATE-ADVICE-003**: 80자 제한으로 간결성 보장 (모바일 UI 대응)

---

## 7. Test Coverage

### 7.1 Test Matrix

| Test Case | Season | Phase | Balance | Flags | Expected Match |
|-----------|--------|-------|---------|-------|----------------|
| test_spring_wood_over_fire_weak | 봄 | 왕 | 목high/화low | - | WOOD_OVER_FIRE_WEAK |
| test_summer_fire_over_water_weak | 여름 | 상 | 화high/수low | - | FIRE_OVER_WATER_WEAK |
| test_summer_earth_excess_dryness | 여름 | 휴 | normal | earth_excess, dryness | EARTH_EXCESS_DRYNESS |
| test_late_summer_earth_excess_humidity | 장하 | 휴 | normal | earth_excess, humidity | EARTH_EXCESS_HUMIDITY |
| test_autumn_metal_over_wood_weak | 가을 | 왕 | 금high/목low | - | METAL_OVER_WOOD_WEAK |
| test_autumn_metal_dryness_relief | 가을 | 수 | 금high | dryness | METAL_DRYNESS_RELIEF |
| test_winter_water_deficit | 겨울 | 휴 | 수low | - | WATER_DEFICIT_IN_WINTER |
| test_winter_water_over_fire_weak_with_coldness | 겨울 | 사 | 수high/화low | coldness | WATER_OVER_FIRE_WEAK |
| test_balanced_fallback | 봄 | 휴 | all normal | - | None (fallback) |

**Total:** 9 tests (8 golden + 1 fallback)

### 7.2 Coverage

- **All seasons**: 봄/여름/장하/가을/겨울 전체 커버
- **All phases**: 왕/상/휴/수/사 전체 사용
- **Balance conditions**: 5원소 low/normal/high 조합
- **Flag conditions**: earth_excess, dryness, humidity, coldness

---

## 8. Future Enhancements (Post-MVP)

### 8.1 Multi-Match Weighted Ranking

**Current:** First match only (top-down)
**Future:** Collect all matches → rank by severity + proximity score

```python
matches = []
for rule in policy["advice_table"]:
    if match(rule, context):
        score = calculate_proximity(rule, context)
        matches.append((rule, score))

# Sort by severity (high > medium > low) then score (desc)
matches.sort(key=lambda x: (severity_weight(x[0]), x[1]), reverse=True)

# Return top N matches
return matches[:3]
```

### 8.2 Pattern Profiler Integration

**Current:** Static policy only
**Future:** Add natural language context from Pattern Profiler

```json
{
  "advice": "불기운을 보강해...",
  "matched_policy_id": "WOOD_OVER_FIRE_WEAK",
  "pattern_context": {
    "profiler_summary": "사주에 화 기운이 미약하여...",
    "recommended_actions": ["남쪽 방향 활동", "붉은색 옷 착용"]
  }
}
```

### 8.3 Extended Guard Rules (v1.2)

| Rule ID | Description |
|---------|-------------|
| CLIMATE-ADVICE-004 | Severity와 balance 수준 일관성 검증 |
| CLIMATE-ADVICE-005 | 용신 전략과 조후 조언 충돌 검증 |
| CLIMATE-ADVICE-006 | 다중 매칭 시 중복/모순 조언 검증 |

---

## 9. Deployment Checklist

### 9.1 Pre-Deployment

- [x] Policy JSON 검증 (schema validation)
- [x] Policy 서명 (psa_cli.py sign)
- [x] 9개 테스트 전체 통과 (pytest)
- [ ] Core pipeline 통합 (strength.py 이후 호출)
- [ ] Evidence bundle 연동 (matched_policy_id → evidence_ref)

### 9.2 CI/CD

- [x] GitHub Actions workflow (placeholder_guard.yml)
- [x] Schema validation step
- [x] Pytest execution step
- [x] PSA signature verification (optional)

### 9.3 Monitoring

- [ ] Matched rule distribution (histogram)
- [ ] Fallback rate (should be <10%)
- [ ] Guard violation rate (should be 0%)

---

## 10. API Integration Example

### 10.1 Core Pipeline Integration

```python
# services/analysis-service/app/core/engine.py

from app.core.climate_balancer import match_climate_advice

def analyze(request: AnalysisRequest) -> AnalysisResponse:
    # ... existing engines ...

    strength_result = strength_evaluator.evaluate(...)
    climate_flags = climate_evaluator.get_flags(...)

    # Prepare context
    ctx = {
        "strength": {
            "phase": strength_result.phase,
            "elements": strength_result.elements
        },
        "climate": {
            "flags": climate_flags
        },
        "context": {
            "season": get_season(request.pillars.month.branch),
            "month_branch": request.pillars.month.branch
        }
    }

    # Match advice
    policy_id, advice = match_climate_advice(ctx)

    # Add to response
    response.climate_advice = {
        "advice": advice,
        "matched_policy_id": policy_id,
        "evidence_ref": f"climate_advice/{policy_id}" if policy_id else None
    }

    return response
```

---

## 11. References

- **Policy:** `policy/climate_advice_policy_v1.json`
- **Schema:** `schema/climate_advice_policy.schema.json`
- **Tests:** `tests/test_climate_advice_mvp.py`
- **Guards:** `guards/llm_guard_rules_climate_mvp_v1.json`
- **Spec:** `docs/engines/climate_balancer_mvp.spec.json`

---

## 12. Changelog

### [2025-10-09] v1.0 (MVP)

- Initial deterministic policy-based implementation
- 8 rules covering all seasons (봄/여름/장하/가을/겨울)
- 9 tests (8 golden + 1 fallback)
- 3 LLM Guard rules (single-line + 80-char limit)
- RFC-8785 JCS signature support

---

**Document Status:** ✅ Complete (MVP)
**Next Review:** After Pattern Profiler integration (Stage 3)
