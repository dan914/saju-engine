# Luck Flow v1.0 — Design (Policy-Only, Deterministic)

**Version:** v1.0 (Policy Package)
**Date:** 2025-10-09 KST
**Status:** Deterministic policy-based scoring

---

## 1. 목적/범위

**대운/세운 변화**로부터 운의 **방향성(trend: rising/stable/declining)**과 **강도(score 0~1)**를 정책 기반으로 산출합니다.

본 버전은 **정책·스키마·테스트 전용**이며, 런타임 엔진은 후속에서 정책을 로드해 점수 합산만 구현합니다.

---

## 2. 입력/출력

### 2.1 입력 (engine_summaries_v1_1)

| Field | Type | Description |
|-------|------|-------------|
| `yongshin.primary` | string | 용신 오행 (목/화/토/금/수) |
| `strength.elements.{wood,fire,earth,metal,water}` | enum | low/normal/high |
| `climate.balance_index` | integer | 조후 균형 지수 [-2..+2] |
| `relation.flags` | array | 관계 플래그 (combine, sanhe, chong, harm) |
| `daewoon.current` | string | 현재 대운 (예: "丙午") |
| `daewoon.next` | string | 다음 대운 (예: "丁未") |
| `daewoon.turning_to_support_primary` | boolean | 대운이 용신 지원 방향으로 전환 |
| `daewoon.turning_to_counter_primary` | boolean | 대운이 용신 대립 방향으로 전환 |
| `sewoon.current` | string | 현재 세운 (예: "丙辰") |
| `sewoon.supports_primary` | boolean | 세운이 용신 지원 |
| `sewoon.counters_primary` | boolean | 세운이 용신 대립 |
| `context.year` | integer | 년도 |
| `context.age` | integer | 나이 |

### 2.2 출력

| Field | Type | Description |
|-------|------|-------------|
| `policy_version` | string | 정책 버전 |
| `trend` | enum | rising/stable/declining |
| `score` | number | 운의 강도 [0..1] |
| `confidence` | number | 신뢰도 [0..1] |
| `drivers[]` | array | 긍정 신호 목록 (max 4) |
| `detractors[]` | array | 부정 신호 목록 (max 4) |
| `evidence_ref` | string | Evidence bundle 참조 경로 |

---

## 3. 스코어링 알고리즘

### 3.1 신호-가중치 합산

```
delta_raw = Σ (weight_i × signal_i)
```

각 신호가 트리거되면 해당 가중치를 합산합니다.

### 3.2 클램프

```
delta = clamp(delta_raw, [-1.0, +1.0])
```

합산 점수를 [-1.0, +1.0] 범위로 제한합니다.

### 3.3 방향성 분류

```
if delta ≥ +0.15:
    trend = "rising"
elif delta ≤ -0.15:
    trend = "declining"
else:
    trend = "stable"
```

### 3.4 점수 및 신뢰도

- **score**: `|delta|` (0..1 범위의 절대값)
- **confidence**: `min(1.0, (트리거된 신호 개수) / 4.0)`

---

## 4. 신호 정의 (요약)

### 4.1 가중치 테이블

| Signal | Weight | Condition |
|--------|--------|-----------|
| `element_gain_primary` | +0.35 | 용신 오행이 `high` |
| `element_loss_primary` | -0.35 | 용신 오행이 `low` |
| `climate_alignment` | +0.30 | `balance_index ≥ 1` |
| `climate_misalignment` | -0.30 | `balance_index ≤ -1` |
| `relation_support` | +0.25 | `flags ∋ {combine, sanhe}` |
| `relation_clash` | -0.25 | `flags ∋ {chong, harm}` |
| `sewoon_alignment` | +0.25 | `sewoon.supports_primary = true` |
| `sewoon_opposition` | -0.25 | `sewoon.counters_primary = true` |
| `transition_daewoon_positive` | +0.20 | `daewoon.turning_to_support_primary = true` |
| `transition_daewoon_negative` | -0.20 | `daewoon.turning_to_counter_primary = true` |
| `yongshin_match` | +0.10 | 용신 존재 + 용신 오행 `high` |

### 4.2 신호 우선순위

가중치가 큰 신호일수록 운의 방향성에 더 큰 영향을 미칩니다:
1. **element_gain/loss_primary (±0.35)**: 용신 오행 상태가 가장 중요
2. **climate_alignment/misalignment (±0.30)**: 조후 균형 차선
3. **relation/sewoon (±0.25)**: 관계 및 세운 지원/대립
4. **transition_daewoon (±0.20)**: 대운 전환 방향
5. **yongshin_match (+0.10)**: 중복 보상 (용신 존재 확인)

---

## 5. Evidence 라우팅

```
evidence_ref = "luck_flow/{context.year}/{daewoon.current}/{sewoon.current}"
```

예시:
```
evidence_ref = "luck_flow/2026/丙午/丙辰"
```

---

## 6. 정책 예제

### 6.1 Rising Example (EX_RISING_FIRE)

**Context:**
- 용신: 화 (火)
- 화 오행: high
- 조후 균형: +1 (aligned)
- 관계: combine
- 대운 전환: 지원 방향
- 세운: 지원

**신호 트리거:**
- `element_gain_primary` (+0.35)
- `climate_alignment` (+0.30)
- `relation_support` (+0.25)
- `transition_daewoon_positive` (+0.20)
- `sewoon_alignment` (+0.25)
- `yongshin_match` (+0.10)

**합산:** +1.45 → **클램프:** +1.0
**결과:** `trend = "rising"`, `score = 1.0`

### 6.2 Stable Example (EX_STABLE_TRANSITION)

**Context:**
- 용신: 목 (木)
- 모든 오행: normal
- 조후 균형: 0
- 관계: 없음
- 대운/세운: 중립

**신호 트리거:** 없음

**합산:** 0.0
**결과:** `trend = "stable"`, `score = 0.0`

### 6.3 Declining Example (EX_DECLINING_EARTH)

**Context:**
- 용신: 토 (土)
- 토 오행: low
- 조후 균형: -1 (misaligned)
- 관계: chong
- 대운 전환: 대립 방향
- 세운: 대립

**신호 트리거:**
- `element_loss_primary` (-0.35)
- `climate_misalignment` (-0.30)
- `relation_clash` (-0.25)
- `transition_daewoon_negative` (-0.20)
- `sewoon_opposition` (-0.25)

**합산:** -1.35 → **클램프:** -1.0
**결과:** `trend = "declining"`, `score = 1.0`

---

## 7. 결정성 보장

### 7.1 LLM 비개입

- 모든 결과는 **고정 정책 + 클램프 규칙**에 의해 결정
- LLM 생성 없음 → 모델 교체 무영향

### 7.2 정책 서명

- **RFC-8785 JCS**: Canonical JSON 정규화
- **SHA-256**: 정책 파일 무결성 검증
- `policy_signature` 필드에 서명 저장

### 7.3 재현성

동일한 입력 → 동일한 출력 (100% 재현 가능)

---

## 8. 확장 계획 (Full v2.0)

### 8.1 세운 세분화

**현재 (v1.0):**
- 연운(년 세운)만 처리

**계획 (v2.0):**
- **월운/일운**: 세운을 월/일 레벨로 확장
- **이동 평균**: ±1년 범위 평균으로 노이즈 감쇄

### 8.2 신호 동적 보정

**현재 (v1.0):**
- 고정 가중치 (모든 상황 동일)

**계획 (v2.0):**
- **계절 보정**: 봄/여름/가을/겨울별 가중치 조정
- **격국 보정**: 격국 유형별 신호 중요도 변경
- **용신 전략 보정**: 부억/억부/조후/통관별 가중치 재조정

### 8.3 Pattern Profiler 통합

**현재 (v1.0):**
- 정책 매칭 결과만 (drivers/detractors 목록)

**계획 (v2.0):**
- **자연어 리포트**: Pattern Profiler와 결합한 설명 생성
- **행동 권장**: 방향/색상/활동 등 구체적 조언

### 8.4 Guard v1.2 확대

**현재 (v1.0):**
- 4개 기본 규칙 (enum, range, length, evidence_ref)

**계획 (v1.2):**
- **LUCK-005**: 경계치 신호 감쇄 검증
- **LUCK-006**: 충돌 신호 상쇄 검증
- **LUCK-007**: 용신-운세 일관성 검증

---

## 9. 테스트 커버리지

### 9.1 Test Cases

| Test | Example ID | Expected Trend |
|------|-----------|----------------|
| `test_rising_example_from_policy_examples` | EX_RISING_FIRE | rising |
| `test_stable_example_from_policy_examples` | EX_STABLE_TRANSITION | stable |
| `test_declining_example_from_policy_examples` | EX_DECLINING_EARTH | declining |
| `test_threshold_boundary_clamping` | EX_CLAMP_RISING_PEAK | rising (clamped) |

### 9.2 Coverage

- **Rising/Stable/Declining**: 모든 방향성 커버
- **Clamping**: 경계치 초과 케이스 검증
- **Signal Combination**: 다중 신호 조합 테스트

---

## 10. 런타임 통합 (후속 작업)

### 10.1 정책 로더

```python
import json
from pathlib import Path

policy = json.loads(Path("policy/luck_flow_policy_v1.json").read_text())
weights = policy["scoring"]["weights"]
signals = policy["signals"]
```

### 10.2 엔진 구현

```python
def evaluate_luck_flow(ctx, policy):
    delta_raw = 0.0
    drivers = []
    detractors = []

    for sig_name, sig in policy["signals"].items():
        if check_when(sig["when"], ctx):
            weight = policy["scoring"]["weights"][sig["eval"]]
            delta_raw += weight
            (drivers if weight > 0 else detractors).append(sig_name)

    delta = clamp(delta_raw, policy["scoring"]["clamp_range"])
    trend = classify_trend(delta, policy["scoring"]["trend_thresholds"])

    return {
        "trend": trend,
        "score": abs(delta),
        "confidence": min(1.0, len(drivers + detractors) / 4.0),
        "drivers": drivers[:4],
        "detractors": detractors[:4],
        "evidence_ref": f"luck_flow/{ctx['context']['year']}/{ctx['daewoon']['current']}/{ctx['sewoon']['current']}"
    }
```

---

## 11. 참고 문서

- **Policy**: `policy/luck_flow_policy_v1.json`
- **Schema**: `schema/luck_flow_policy.schema.json`, `schema/luck_flow_output.schema.json`
- **Spec**: `docs/engines/luck_flow.spec.json`
- **I/O**: `docs/engines/luck_flow.io.json`
- **Guards**: `guards/llm_guard_rules_luck_flow_v1.json`
- **Tests**: `tests/test_luck_flow_v1.py`

---

## 12. Changelog

### [2025-10-09] v1.0 (Policy Package)

- 정책 파일 (weights, signals, 4 examples)
- 스키마 (policy, output)
- 엔진 스펙 (I/O contract)
- LLM Guard 규칙 (4 rules)
- 테스트 (rising/stable/declining + clamping)
- 설계 문서 (2p summary)

---

**Document Status:** ✅ Complete (Policy Package)
**Next Step:** 런타임 엔진 구현 + Pipeline 통합
