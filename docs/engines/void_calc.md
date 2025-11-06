# 공망(旬空) 계산기 — void_calc v1.1

본 엔진은 일주(60갑자) 기준으로 旬(10일) 구간을 계산하고, 해당 旬의 공망 지지 2개를 O(1)로 반환합니다.
정책은 내장 기본값을 사용하며, 선택적으로 policies/void_policy_v1.json을 통해 오버라이드할 수 있습니다.

## 공개 API

### compute_void(day_pillar: str) -> list[str]
입력된 일주(예: 乙亥, 庚辰)에 해당하는 공망 지지 2개를 반환합니다.
전각 한자 2글자만 허용하며, 공백/ASCII/혼입 입력은 오류입니다.

```python
from app.core.void import compute_void
kong = compute_void("乙丑")  # ["戌","亥"]
```

### apply_void_flags(branches: list[str], kong: list[str]) -> dict
4지지(연/월/일/시)에 공망 여부 플래그를 부여합니다.

```python
from app.core.void import apply_void_flags
res = apply_void_flags(["戌","亥","寅","卯"], ["戌","亥"])
# {"flags":[True, True, False, False], "hit_branches":["戌","亥"]}
```

### explain_void(day_pillar: str) -> dict
계산 근거(60갑자 인덱스, 旬 시작), 정책 버전/시그니처를 포함한 트레이스를 제공합니다.

```python
from app.core.void import explain_void
trace = explain_void("乙丑")
# {
#   "policy_version": "void_calc_v1.1.0",
#   "policy_signature": "<64-hex>",
#   "day_index": 1,
#   "xun_start": 0,
#   "kong": ["戌","亥"]
# }
```

## 정책 오버라이드
policies/void_policy_v1.json 파일이 존재하면 로드하여 내장 정책을 대체합니다.
형식은 다음과 같습니다(키는 0/10/20/30/40/50 여섯 개, 값은 12지지 2개):

```json
{
  "0": ["戌","亥"],
  "10": ["申","酉"],
  "20": ["午","未"],
  "30": ["辰","巳"],
  "40": ["寅","卯"],
  "50": ["子","丑"]
}
```
형식 오류/누락 시 내장 정책으로 폴백합니다(경고 로그는 테스트 단순화를 위해 생략).
정책 시그니처는 RFC‑8785 근사 Canonical JSON → SHA‑256으로 계산됩니다.

## 통합 포인트
- 분석 파이프라인에서 **일주(일간/일지)**가 결정된 후 호출합니다.
- void.explain_void()의 kong을 이용해 리포트/카드에 공망 배지를 표기하고, apply_void_flags()로 4지지 히트 여부를 annotate 합니다.

## 오류 사례
- "甲" / "甲子子": 길이 오류
- "甲 子" / "甲子 ": 공백 포함
- "AB" / "甲甲": 60갑자 미상/ASCII 혼입

## 버전
- 정책 버전: void_calc_v1.1.0
- 위치: services/analysis-service/app/core/void.py
- 스키마: services/analysis-service/schemas/void_result.schema.json
- 테스트: services/analysis-service/tests/test_void.py
