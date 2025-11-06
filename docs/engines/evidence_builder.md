# Evidence Builder — v1.0

**Version:** v1.0.0
**Date:** 2025-10-08 KST
**Type:** Meta-Engine / Orchestration Layer

Stage-1 엔진들의 산출물을 수집하여 단일 Evidence 객체로 정규화/서명합니다.
모든 섹션은 동일한 created_at(UTC, 초단위) 타임스탬프를 공유하며, 결과는 결정적 정렬과 SHA-256 서명을 갖습니다.

---

## 개요

Evidence Builder는 3개의 Stage-1 엔진(void, yuanjin, wuxing_adjust)의 산출물을 수집하여:

- **섹션 단위 서명** - 각 엔진 출력의 무결성 검증
- **증거 단위 서명** - 전체 컬렉션의 무결성 검증
- **결정적 정렬** - 타입별 알파벳 순서 (void → wuxing_adjust → yuanjin)
- **공유 타임스탬프** - 모든 섹션이 동일 created_at 사용 (멱등성)
- **선택적 섹션** - 필요한 엔진만 포함 가능
- **타입 유일성** - 중복 섹션 타입 금지

**목적:** `/report` 생성 파이프라인에서 감사 가능하고 재현 가능한 증거 추적 제공

---

## 공개 API

### build_evidence(inputs: dict) -> dict

엔진 원시 출력 묶음을 받아 Evidence를 생성합니다.

**입력 예:**
```python
from app.core import evidence_builder as eb

inputs = {
    "void": {
        "policy_version": "void_calc_v1.1.0",
        "policy_signature": "<64-hex>",
        "day_index": 1,
        "xun_start": 0,
        "kong": ["戌", "亥"]
    },
    "yuanjin": {
        "policy_version": "yuanjin_v1.1.0",
        "policy_signature": "<64-hex>",
        "present_branches": ["子", "丑", "寅", "未"],
        "hits": [["子", "未"]],
        "pair_count": 1
    },
    "wuxing_adjust": {
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
}

ev = eb.build_evidence(inputs)
```

**출력 예:**
```json
{
  "evidence_version": "evidence_v1.0.0",
  "evidence_signature": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a",
  "sections": [
    {
      "type": "void",
      "engine_version": "void_calc_v1.1.0",
      "engine_signature": "...",
      "source": "services/analysis-service/app/core/void.py",
      "payload": {
        "kong": ["戌", "亥"],
        "day_index": 1,
        "xun_start": 0
      },
      "created_at": "2024-01-01T00:00:00Z",
      "section_signature": "..."
    },
    {
      "type": "wuxing_adjust",
      "engine_version": "combination_element_v1.2.0",
      "engine_signature": "...",
      "source": "services/analysis-service/app/core/combination_element.py",
      "payload": {
        "dist": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
        "trace": [...]
      },
      "created_at": "2024-01-01T00:00:00Z",
      "section_signature": "..."
    },
    {
      "type": "yuanjin",
      "engine_version": "yuanjin_v1.1.0",
      "engine_signature": "...",
      "source": "services/analysis-service/app/core/yuanjin.py",
      "payload": {
        "present_branches": ["子", "丑", "寅", "未"],
        "hits": [["子", "未"]],
        "pair_count": 1
      },
      "created_at": "2024-01-01T00:00:00Z",
      "section_signature": "..."
    }
  ]
}
```

---

### add_section(ev: dict, section: dict) -> dict

단일 섹션을 Evidence 객체에 추가합니다. type 중복은 금지되며, section_signature가 자동 부여됩니다.

**사용 예:**
```python
ev = {"evidence_version": "evidence_v1.0.0", "sections": []}

section = {
    "type": "void",
    "engine_version": "void_calc_v1.1.0",
    "engine_signature": "<64-hex>",
    "source": "services/analysis-service/app/core/void.py",
    "payload": {"kong": ["戌", "亥"], "day_index": 1, "xun_start": 0},
    "created_at": "2024-01-01T00:00:00Z"
}

ev = eb.add_section(ev, section)
# section_signature 자동 추가됨
```

**예외:**
- `ValueError`: 섹션 타입 중복 시
- `ValueError`: 필수 필드 누락 시
- `ValueError`: 형식 검증 실패 시

---

### finalize_evidence(ev: dict) -> dict

sections를 type 사전식으로 정렬하고 evidence_signature를 계산합니다.

**사용 예:**
```python
ev = {
    "evidence_version": "evidence_v1.0.0",
    "sections": [
        {"type": "yuanjin", ...},
        {"type": "void", ...}
    ]
}

ev = eb.finalize_evidence(ev)
# sections 정렬: ["void", "yuanjin"]
# evidence_signature 추가됨
```

**예외:**
- `ValueError`: sections가 비어 있을 시

---

## 통합 예제

### 단일 엔진 사용

**Void Calculator:**
```python
from app.core import void as vc
from app.core import evidence_builder as eb

# 공망 계산
day_pillar = "乙丑"
void_result = vc.explain_void(day_pillar)

# Evidence 생성
evidence = eb.build_evidence({"void": void_result})
```

**Yuanjin Detector:**
```python
from app.core import yuanjin as yj
from app.core import evidence_builder as eb

# 원진 탐지
branches = ["子", "丑", "寅", "未"]
yuanjin_result = yj.explain_yuanjin(branches)

# Evidence 생성
evidence = eb.build_evidence({"yuanjin": yuanjin_result})
```

**Combination Element:**
```python
from app.core import combination_element as ce
from app.core import evidence_builder as eb

# 합화오행 변환
relations = {...}
dist_raw = {...}
dist, trace = ce.transform_wuxing(relations, dist_raw)

wuxing_result = {
    "engine_version": ce.POLICY_VERSION,
    "engine_signature": ce.POLICY_SIGNATURE,
    "dist": dist,
    "trace": trace
}

# Evidence 생성
evidence = eb.build_evidence({"wuxing_adjust": wuxing_result})
```

---

### 다중 엔진 통합

```python
from app.core import void as vc
from app.core import yuanjin as yj
from app.core import combination_element as ce
from app.core import evidence_builder as eb

# 1. 각 엔진 실행
day_pillar = "乙丑"
void_result = vc.explain_void(day_pillar)

branches = ["子", "丑", "寅", "未"]
yuanjin_result = yj.explain_yuanjin(branches)

relations = {...}
dist_raw = {...}
dist, trace = ce.transform_wuxing(relations, dist_raw)
wuxing_result = {
    "engine_version": ce.POLICY_VERSION,
    "engine_signature": ce.POLICY_SIGNATURE,
    "dist": dist,
    "trace": trace
}

# 2. Evidence 통합
inputs = {
    "void": void_result,
    "yuanjin": yuanjin_result,
    "wuxing_adjust": wuxing_result
}
evidence = eb.build_evidence(inputs)

# 3. 결과 검증
assert len(evidence["sections"]) == 3
assert evidence["sections"][0]["type"] == "void"      # 정렬됨
assert evidence["sections"][1]["type"] == "wuxing_adjust"
assert evidence["sections"][2]["type"] == "yuanjin"
```

---

## 정책 / 서명

### 정책 스펙
```python
POLICY_SPEC = {
    "version": "evidence_v1.0.0",
    "allowed_types": ["void", "yuanjin", "wuxing_adjust", "shensha", "relation_hits", "strength"],
    "required_fields": ["type", "engine_version", "engine_signature", "source", "payload", "created_at"],
    "created_at_format": "YYYY-MM-DDTHH:MM:SSZ"
}
```

### 섹션 서명 계산
6개 필수 필드만 사용하여 캐노니컬 JSON 서명:
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

### Evidence 서명 계산
2개 필드만 사용하여 캐노니컬 JSON 서명:
```python
evidence_base = {
    "evidence_version": "evidence_v1.0.0",
    "sections": [...]  # section_signature 포함
}
evidence_signature = sha256(canonical_json(evidence_base))
```

---

## 결정성 보장

### 타임스탬프 공유
모든 섹션이 동일 타임스탬프 사용:
```python
created_at = "2024-01-01T00:00:00Z"  # 단일 호출
for section in sections:
    section["created_at"] = created_at
```

### 정렬
섹션을 타입별 알파벳 순서로 정렬:
```python
sections = sorted(sections, key=lambda s: s["type"])
# ["void", "wuxing_adjust", "yuanjin"]
```

### 캐노니컬 JSON
```python
json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

**결과:** 동일 입력 → 동일 서명 (멱등성)

---

## 스키마 구조

### Evidence Object
- `evidence_version` (string, required): 정책 버전
- `evidence_signature` (string, required): 64자 hex SHA-256
- `sections` (array, required): 섹션 배열

### Section Object
- `type` (enum, required): "void" | "yuanjin" | "wuxing_adjust" | "shensha" | "relation_hits" | "strength"
- `engine_version` (string, required): 엔진 버전
- `engine_signature` (string, required): 64자 hex SHA-256
- `source` (string, required): 엔진 파일 경로
- `payload` (object, required): 엔진별 데이터
- `created_at` (string, required): ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
- `section_signature` (string, required): 64자 hex SHA-256

---

## 에러 처리

### 입력 검증 에러
```python
# 필수 키 누락
inputs = {"void": {"policy_version": "v1.1.0"}}  # kong 누락
# → ValueError: "void 입력에 필수 키 누락: kong"
```

### 중복 타입 에러
```python
ev = build_evidence({"void": void_result})
add_section(ev, void_section_again)
# → ValueError: "섹션 타입 중복: void"
```

### 형식 검증 에러
```python
section = {
    "type": "void",
    "created_at": "2024-01-01 00:00:00Z"  # 공백 포함 (잘못된 형식)
    # ...
}
# → ValueError: "created_at은 UTC ISO8601(Z) 형식이어야 합니다."
```

### 빈 섹션 에러
```python
ev = {"evidence_version": "v1.0.0", "sections": []}
finalize_evidence(ev)
# → ValueError: "sections가 비어 있습니다."
```

---

## 확장성

### 미래 섹션 타입
현재 구현된 타입:
- `void` - 공망 계산
- `yuanjin` - 원진 탐지
- `wuxing_adjust` - 합화오행 변환

계획된 타입 (ALLOWED_TYPES에 포함):
- `shensha` - 신살 목록
- `relation_hits` - 관계 충돌/조화
- `strength` - 강약 평가

**추가 방법:**
1. `ALLOWED_TYPES` 배열에 타입 추가
2. `_normalize_inputs()` 함수에 정규화 로직 추가
3. 테스트 추가

---

## 테스트 커버리지

| 테스트 | 목적 | 결과 |
|--------|------|------|
| `test_build_evidence_with_three_sections_and_order` | 3개 섹션 통합 + 정렬 | ✅ PASS |
| `test_optional_single_section` | 단일 섹션 선택적 사용 | ✅ PASS |
| `test_duplicate_type_add_raises` | 중복 타입 검증 | ✅ PASS |
| `test_schema_presence_and_patterns` | 스키마 존재 + 패턴 | ✅ PASS |
| `test_deterministic_signature_same_inputs` | 멱등성 검증 | ✅ PASS |
| `test_finalize_error_on_empty_sections` | 빈 섹션 검증 | ✅ PASS |
| `test_invalid_created_at_in_add_section` | 타임스탬프 검증 | ✅ PASS |

**총 테스트:** 7/7 passing ✅

---

## 통합 포인트 (Phase 2)

### AnalysisEngine 통합 (예정)
```python
# services/analysis-service/app/core/engine.py

class AnalysisEngine:
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        # ... 기존 로직 ...

        # Evidence 수집
        from app.core import evidence_builder as eb

        evidence_inputs = {}

        if request.options.get("include_void", True):
            void_result = self._compute_void(pillars)
            evidence_inputs["void"] = void_result

        if request.options.get("include_yuanjin", True):
            yuanjin_result = self._detect_yuanjin(pillars)
            evidence_inputs["yuanjin"] = yuanjin_result

        if request.options.get("include_wuxing_adjust", True):
            wuxing_result = self._adjust_wuxing(relations, dist_raw)
            evidence_inputs["wuxing_adjust"] = wuxing_result

        # Evidence 생성
        evidence = eb.build_evidence(evidence_inputs)

        # 응답에 첨부
        response.evidence = evidence

        return response
```

---

## 파일 위치

| 파일 | 경로 | 크기 |
|------|------|------|
| 엔진 | `services/analysis-service/app/core/evidence_builder.py` | 262 lines |
| 스키마 | `services/analysis-service/schemas/evidence.schema.json` | 72 lines |
| 테스트 | `services/analysis-service/tests/test_evidence_builder.py` | 174 lines |
| 문서 | `docs/engines/evidence_builder.md` | This file |

---

## 버전 이력

- **v1.0.0** (2025-10-08): 초기 릴리스
  - void, yuanjin, wuxing_adjust 섹션 지원
  - 결정적 정렬 + 이중 서명
  - 7개 테스트 통과

---

## 참고 자료

- `void.py` - 공망 계산기
- `yuanjin.py` - 원진 탐지기
- `combination_element.py` - 합화오행 변환기
- `EVIDENCE_BUILDER_INTEGRATION_PLAN.md` - 통합 계획 문서
- `ENGINE_INTEGRATION_SESSION_REPORT.md` - 세션 보고서
