# 원진(Yuanjin) 탐지기 — yuanjin v1.1

본 엔진은 4지지(연/월/일/시)에서 **원진 쌍(6세트)**의 충돌 여부를 O(1)로 판정하고,
결과를 결정적 정렬 규칙에 따라 반환합니다.

## 공개 API

### detect_yuanjin(branches: list[str]) -> list[list[str]]
입력된 4지지 중 원진에 해당하는 히트 쌍 목록을 반환합니다.
쌍 내부는 BRANCHES 인덱스 오름차순으로 정렬되며, 목록 또한 동일 기준으로 정렬됩니다.

```python
from app.core.yuanjin import detect_yuanjin
pairs = detect_yuanjin(["酉","戌","辰","卯"])
# [["卯","辰"], ["酉","戌"]]
```

### apply_yuanjin_flags(branches: list[str]) -> dict
4지지 각각에 대해 어느 원진쌍에라도 포함되면 True로 표기합니다.

```python
from app.core.yuanjin import apply_yuanjin_flags
out = apply_yuanjin_flags(["子","丑","寅","未"])
# {"flags":[True, False, False, True], "pairs":[["子","未"]]}
```

### explain_yuanjin(branches: list[str]) -> dict
정책 버전/시그니처와 함께 계산 근거(현재 4지지, 히트쌍, 개수)를 제공합니다.

```python
from app.core.yuanjin import explain_yuanjin
trace = explain_yuanjin(["子","丑","寅","未"])
# {
#   "policy_version": "yuanjin_v1.1.0",
#   "policy_signature": "<64-hex>",
#   "present_branches": ["子","丑","寅","未"],
#   "hits": [["子","未"]],
#   "pair_count": 1
# }
```

## 원진 쌍 (Default Policy)

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

## 정책 오버라이드
policies/yuanjin_policy_v1.json 파일이 존재하면 로드·유효성 검증 후 적용합니다.
형식은 배열의 배열이며, 각 항목은 12지지 2개로 구성됩니다(중복/역순은 1회로 정규화).

```json
[
  ["子","未"], ["丑","午"], ["寅","巳"],
  ["卯","辰"], ["申","亥"], ["酉","戌"]
]
```
형식 오류/누락 시 내장 정책으로 폴백합니다(경고 로그는 테스트 단순화를 위해 생략).
정책 시그니처는 RFC‑8785 근사 Canonical JSON → SHA‑256으로 계산합니다.

## 정렬/중복 규칙
- 쌍 내부 정렬: BRANCHES 인덱스 기준 오름차순
- 목록 정렬: 첫 요소 인덱스 → 둘째 요소 인덱스
- 동일 쌍은 1회만 보고(집합적 판정)

## 오류 사례
- 길이≠4, 전각 아님/ASCII 혼입, 미상 지지 문자가 포함된 경우 ValueError 발생

## 리포트 통합 포인트
- pairs를 배지로 노출하고, flags를 지지 칩에 반영하여 시각화합니다.
- policy_version/policy_signature는 Evidence 섹션에 함께 기록합니다.

## 버전
- 정책 버전: yuanjin_v1.1.0
- 위치: services/analysis-service/app/core/yuanjin.py
- 스키마: services/analysis-service/schemas/yuanjin_result.schema.json
- 테스트: services/analysis-service/tests/test_yuanjin.py
