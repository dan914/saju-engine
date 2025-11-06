# 합화오행 트랜스포머 — combination_element v1.2

관계 분석 결과(relations)를 바탕으로 오행 분포(dist_raw)를 가중 이동하여 정규화합니다.
삼합(局成), 육합, 천간합은 증가(+), 충은 **감소(−)**로 적용하며, 우선순위에 따라 한 번씩만 실행합니다.

## 공개 API

### transform_wuxing(relations: dict, dist_raw: dict, policy: dict|None=None) -> (dict, list[dict])
입력 분포를 정규화 후, 정책에 따라 이동을 적용하여 (새 분포, trace)를 반환합니다.

```python
from app.core.combination_element import transform_wuxing

relations = {"earth":{"sanhe":[{"formed":True,"element":"water"}]}}
dist0 = {"wood":0.2,"fire":0.2,"earth":0.2,"metal":0.2,"water":0.2}
dist, trace = transform_wuxing(relations, dist0)
# dist["water"] ≈ 0.4
# trace[0] = {
#   "reason":"sanhe","target":"water","moved_ratio":0.20,
#   "weight":0.20,"order":1,"policy_signature":"<64-hex>"
# }
```

### normalize_distribution(dist: dict) -> dict
오행 분포를 정규화하여 합이 1.0이 되도록 조정합니다.

```python
from app.core.combination_element import normalize_distribution

dist = normalize_distribution({"wood":0.3,"fire":0.3,"earth":0.2,"metal":0.1,"water":0.1})
# Returns normalized distribution with sum=1.0
```

## Trace 구조
각 이동 단계는 아래 필드를 갖습니다.

- **reason**: "sanhe" | "liuhe" | "stem_combo" | "clash"
- **target**: "wood" | "fire" | "earth" | "metal" | "water"
- **moved_ratio**: 이동 총량(타 요소→대상은 +, 대상→타 요소는 −)
- **weight**: 정책 비율(입력 정책 사용 시 해당 값)
- **order**: 적용 우선순위(작을수록 먼저)
- **policy_signature**: 정책 서명( RFC‑8785 근사 canonical → SHA‑256 )

스키마는 `services/analysis-service/schemas/combination_trace.schema.json`을 참조합니다.

## 정책 오버라이드

### 기본 정책

| key | ratio | order | 설명 |
|---|---:|---:|---|
| sanhe | 0.20 | 1 | 삼합 局成 (가장 강력) |
| liuhe | 0.10 | 2 | 육합 |
| stem_combo | 0.08 | 3 | 천간합 |
| clash | -0.10 | 4 | 충 (감소) |

### 파일 오버라이드
`policies/combination_policy_v1.json` 또는 `saju_codex_batch_all_v2_6_signed/policies/combination_policy_v1.json`

```json
{
  "sanhe": { "ratio": 0.15, "order": 1 },
  "liuhe": { "ratio": 0.10, "order": 2 }
}
```

### 함수 인자 오버라이드
함수 인자 `policy`가 제공되면 파일/기본 정책보다 우선합니다.

```python
override = {"sanhe": {"ratio": 0.10, "order": 1}}
dist, trace = transform_wuxing(relations, dist0, policy=override)
```

## 변환 규칙

### 1. 삼합(局成)
- `formed=true` 항목만 적용
- 타 요소에서 총 ratio만큼 비례 차감 → 대상 가산

### 2. 육합/천간합
- 동일 방식으로 가산
- `relations.earth.liuhe` 또는 `relations.heavenly.stem_combos`

### 3. 충(Clash)
- 대상에서 총 `|ratio|`만큼 차감 → 타 요소에 비례 가산
- 음수 ratio 사용

### 4. 우선순위(Order)
- 낮은 숫자부터 적용
- 동일 order 내 첫 등장만 적용

### 5. 정규화
- 이동 후 항상 정규화(합 1.0 ± 1e-9)
- 공정성 강화: 잔차를 비례 분산하여 편향 방지

## 이동 알고리즘

### 증가 이동 (ratio > 0)
```
1. 타 요소들의 합계 계산
2. 각 요소에서 비례 차감 (요소 비율 × ratio)
3. 차감한 총량을 대상 요소에 가산
4. 정규화
```

### 감소 이동 (ratio < 0)
```
1. 대상 요소에서 |ratio| 차감
2. 차감한 양을 타 요소들에 비례 분배
3. 정규화
```

## 공정성 강화 정규화

기존 방식(최대값에 잔차 전체 추가)의 문제:
- 이미 큰 요소가 더 커짐
- 분포 편향 증가

**개선된 방식:**
1. 1차 정규화 (vals / sum)
2. 잔차를 현재 비중에 **비례 분산**
3. 음수 방지 (0 클램프)
4. 미세 잔차만 최대값에 최종 보정

결과: 공정한 분포 유지

## 오류 사례

- 알 수 없는 element/잘못된 비율·우선순위가 정책에 포함 → `ValueError`
- relations 구조가 올바르지 않거나 element가 5오행이 아닌 경우 → `ValueError`

## 통합 포인트

- trace를 리포트 카드의 **이동 근거(Evidence)**로 표기
- 조정된 dist는 이후 점수화/시각화(레이더 차트 등)에 입력
- policy_signature는 Evidence 섹션에 기록하여 재현성 보장

## 예제

### 예제 1: 삼합 局成
```python
relations = {
    "earth": {
        "sanhe": [{"formed": True, "element": "water"}]
    }
}
dist0 = {"wood":0.2, "fire":0.2, "earth":0.2, "metal":0.2, "water":0.2}
dist, trace = transform_wuxing(relations, dist0)

# Result:
# dist["water"] ≈ 0.4 (0.2 → 0.4, +0.2 from others)
# trace[0] = {
#   "reason": "sanhe",
#   "target": "water",
#   "moved_ratio": 0.20,
#   "weight": 0.20,
#   "order": 1,
#   "policy_signature": "<64-hex>"
# }
```

### 예제 2: 충 감소
```python
relations = {
    "earth": {
        "clash": [{"element": "fire"}]
    }
}
dist0 = {"wood":0.2, "fire":0.2, "earth":0.2, "metal":0.2, "water":0.2}
dist, trace = transform_wuxing(relations, dist0)

# Result:
# dist["fire"] ≈ 0.1 (0.2 → 0.1, -0.1 to others)
# Others each increase by ~0.025
```

### 예제 3: 다중 규칙
```python
relations = {
    "earth": {
        "sanhe": [{"formed": True, "element": "water"}],
        "liuhe": [{"element": "metal"}]
    },
    "heavenly": {
        "stem_combos": [{"element": "fire"}]
    }
}
dist0 = {"wood":0.2, "fire":0.2, "earth":0.2, "metal":0.2, "water":0.2}
dist, trace = transform_wuxing(relations, dist0)

# Applies in order:
# 1. sanhe → water +0.20
# 2. liuhe → metal +0.10
# 3. stem_combo → fire +0.08
# trace has 3 entries
```

## 버전
- 정책 버전: combination_element_v1.2.0
- 위치: services/analysis-service/app/core/combination_element.py
- 스키마: services/analysis-service/schemas/combination_trace.schema.json
- 테스트: services/analysis-service/tests/test_combination_element.py
