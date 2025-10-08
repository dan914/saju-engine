# 한국어 레이블 보강 제안: LLM 전달 레이어 방식

**작성일**: 2025-10-05
**제안**: 엔진 코드 수정 없이 LLM 전달 시점에 한국어 레이블 추가
**상태**: ✅ **실행 가능한 제안**

---

## 📋 핵심 아이디어

**기존 엔진은 그대로 두고**, `LLMGuard.prepare_payload()` 단계에서 **한국어 레이블을 동적으로 주입**하는 방식

### 장점

✅ **비침습적**: 기존 엔진 코드 수정 불필요
✅ **점진적**: LLM용 출력만 먼저 개선
✅ **빠른 구현**: 1-2일 내 완료 가능
✅ **안전성**: 엔진 로직에 영향 없음
✅ **유연성**: localization_ko_v1.json만 수정하면 전체 반영

### 단점

⚠️ **이중 관리**: API 응답과 LLM 페이로드 구조 차이 발생
⚠️ **일관성**: 향후 API도 한국어 지원 시 중복 로직 가능성
⚠️ **부분적**: LLM을 거치지 않는 응답은 여전히 영어/코드만

---

## 1. 현재 구조 분석

### 1.1 LLMGuard 현재 역할

**파일**: `services/analysis-service/app/core/llm_guard.py`

```python
class LLMGuard:
    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Convert response to plain dict before giving it to an LLM."""
        # 현재: Pydantic 검증만 수행
        AnalysisResponse.model_validate(response.model_dump())
        return response.model_dump()
```

**현재 동작**:
- AnalysisResponse → dict 변환만 수행
- 한국어 레이블 추가 없음

### 1.2 AnalysisResponse 구조

**파일**: `services/analysis-service/app/models/analysis.py`

```python
class AnalysisResponse(BaseModel):
    ten_gods: TenGodsResult
    relations: RelationsResult
    strength: StrengthResult
    structure: StructureResultModel  # primary: "정관" 또는 "ZHENGGUAN"?
    luck: LuckResult
    shensha: ShenshaResult
    recommendation: RecommendationResult
    trace: dict
```

**문제점**:
- `structure.primary`: 한글 또는 코드 혼재
- `strength.level`: "weak", "balanced", "strong" (영어)
- label_ko/label_en 구분 없음

---

## 2. 제안 방식: Korean Label Enricher

### 2.1 아키텍처

```
AnalysisEngine.analyze()
    ↓
AnalysisResponse (원본, 코드/영어 포함)
    ↓
LLMGuard.prepare_payload()
    ↓
KoreanLabelEnricher.enrich()  ← 새로 추가
    ↓
Enriched Payload (한국어 레이블 추가)
    ↓
LLM에게 전달
```

### 2.2 구현 클래스

**새 파일**: `services/analysis-service/app/core/korean_enricher.py`

```python
"""Korean label enrichment for LLM payload."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

LOCALIZATION_KO_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_batch_all_v2_6_signed"
    / "policies"
    / "localization_ko_v1.json"
)

@dataclass(slots=True)
class KoreanLabelEnricher:
    """Enrich analysis payload with Korean labels for LLM consumption."""

    ten_gods_ko: Dict[str, str]
    role_ko: Dict[str, str]
    relation_ko: Dict[str, str]
    strength_ko: Dict[str, str]  # 추가 필요
    structure_ko: Dict[str, str]  # 추가 필요
    shensha_ko: Dict[str, str]  # 추가 필요

    @classmethod
    def from_file(cls, path: Path | None = None) -> "KoreanLabelEnricher":
        """Load Korean localization mappings."""
        loc_path = path or LOCALIZATION_KO_PATH
        with loc_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Load additional mappings from other policies if needed
        strength_ko = cls._load_strength_labels()
        structure_ko = cls._load_structure_labels()
        shensha_ko = cls._load_shensha_labels()

        return cls(
            ten_gods_ko=data.get("ten_gods_ko", {}),
            role_ko=data.get("role_ko", {}),
            relation_ko=data.get("relation_ko", {}),
            strength_ko=strength_ko,
            structure_ko=structure_ko,
            shensha_ko=shensha_ko,
        )

    @staticmethod
    def _load_strength_labels() -> Dict[str, str]:
        """Load strength labels (weak/balanced/strong -> 약/중화/강)."""
        # TODO: strength_policy_v2.json에 추가 후 로드
        return {
            "weak": "약",
            "balanced": "중화",
            "strong": "강",
        }

    @staticmethod
    def _load_structure_labels() -> Dict[str, str]:
        """Load gyeokguk structure labels."""
        # gyeokguk_policy.json에서 로드
        policy_path = (
            Path(__file__).resolve().parents[4]
            / "saju_codex_batch_all_v2_6_signed"
            / "policies"
            / "gyeokguk_policy.json"
        )
        with policy_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for pattern in data.get("patterns", []):
            code = pattern.get("code")
            label_ko = pattern.get("label_ko")
            if code and label_ko:
                mapping[code] = label_ko
                # Also map Korean to Korean (이미 한글인 경우 pass-through)
                mapping[label_ko] = label_ko

        return mapping

    @staticmethod
    def _load_shensha_labels() -> Dict[str, str]:
        """Load shensha labels from labels.ko structure."""
        policy_path = (
            Path(__file__).resolve().parents[4]
            / "saju_codex_batch_all_v2_6_signed"
            / "policies"
            / "shensha_v2_policy.json"
        )
        with policy_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for item in data.get("shensha_catalog", []):
            key = item.get("key")
            label_ko = item.get("labels", {}).get("ko")
            if key and label_ko:
                mapping[key] = label_ko

        return mapping

    def enrich(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add Korean labels to payload for LLM consumption."""
        enriched = payload.copy()

        # 1. Enrich structure
        if "structure" in enriched and enriched["structure"].get("primary"):
            primary = enriched["structure"]["primary"]
            enriched["structure"]["primary_ko"] = self.structure_ko.get(primary, primary)

            # Enrich candidates
            if "candidates" in enriched["structure"]:
                for cand in enriched["structure"]["candidates"]:
                    cand_type = cand.get("type")
                    if cand_type:
                        cand["type_ko"] = self.structure_ko.get(cand_type, cand_type)

        # 2. Enrich strength
        if "strength" in enriched and enriched["strength"].get("level"):
            level = enriched["strength"]["level"]
            enriched["strength"]["level_ko"] = self.strength_ko.get(level, level)

        # 3. Enrich ten_gods
        if "ten_gods" in enriched and "summary" in enriched["ten_gods"]:
            summary_ko = {}
            for key, value in enriched["ten_gods"]["summary"].items():
                summary_ko[key] = self.ten_gods_ko.get(value, value)
            enriched["ten_gods"]["summary_ko"] = summary_ko

        # 4. Enrich shensha
        if "shensha" in enriched and "list" in enriched["shensha"]:
            for item in enriched["shensha"]["list"]:
                if "key" in item:
                    item["label_ko"] = self.shensha_ko.get(item["key"], item["key"])

        # 5. Add metadata
        enriched["_enrichment"] = {
            "korean_labels_added": True,
            "locale": "ko-KR",
            "enricher_version": "1.0.0",
        }

        return enriched
```

### 2.3 LLMGuard 수정

**파일**: `services/analysis-service/app/core/llm_guard.py`

```python
from .korean_enricher import KoreanLabelEnricher

@dataclass(slots=True)
class LLMGuard:
    text_guard: TextGuard
    recommendation_guard: RecommendationGuard
    korean_enricher: KoreanLabelEnricher  # 추가

    @classmethod
    def default(cls) -> "LLMGuard":
        return cls(
            text_guard=TextGuard.from_file(),
            recommendation_guard=RecommendationGuard.from_file(),
            korean_enricher=KoreanLabelEnricher.from_file(),  # 추가
        )

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Convert response to dict and enrich with Korean labels."""
        AnalysisResponse.model_validate(response.model_dump())

        # 원본 페이로드
        payload = response.model_dump()

        # 한국어 레이블 추가
        enriched = self.korean_enricher.enrich(payload)

        return enriched
```

---

## 3. Localization 정책 보완

### 3.1 strength_policy_v2.json 보완

**현재**:
```json
{
  "grading_tiers": [
    { "code": "very_weak", "range": [0, 20] },
    { "code": "weak", "range": [21, 40] },
    { "code": "balanced", "range": [41, 60] },
    { "code": "strong", "range": [61, 80] },
    { "code": "very_strong", "range": [81, 100] }
  ]
}
```

**추가 필요**:
```json
{
  "grading_tiers": [
    {
      "code": "very_weak",
      "range": [0, 20],
      "label_ko": "극약",
      "label_en": "Very Weak"
    },
    {
      "code": "weak",
      "range": [21, 40],
      "label_ko": "약",
      "label_en": "Weak"
    },
    {
      "code": "balanced",
      "range": [41, 60],
      "label_ko": "중화",
      "label_en": "Balanced"
    },
    {
      "code": "strong",
      "range": [61, 80],
      "label_ko": "강",
      "label_en": "Strong"
    },
    {
      "code": "very_strong",
      "range": [81, 100],
      "label_ko": "극강",
      "label_en": "Very Strong"
    }
  ]
}
```

### 3.2 localization_ko_v1.json 확장

**추가 필요**:
```json
{
  "strength_ko": {
    "very_weak": "극약",
    "weak": "약",
    "balanced": "중화",
    "strong": "강",
    "very_strong": "극강"
  },
  "relations_ko": {
    "he6": "육합",
    "sanhe": "삼합",
    "banhe": "반합",
    "chong": "충",
    "xing": "형",
    "po": "파",
    "hai": "해"
  }
}
```

---

## 4. 출력 예시

### 4.1 원본 페이로드 (Before Enrichment)

```json
{
  "structure": {
    "primary": "ZHENGGUAN",
    "confidence": "high",
    "candidates": [
      { "type": "ZHENGGUAN", "score": 87 }
    ]
  },
  "strength": {
    "level": "weak",
    "basis": { "month_state": "囚" }
  },
  "ten_gods": {
    "summary": {
      "year_stem": "正官",
      "month_stem": "偏財"
    }
  },
  "shensha": {
    "enabled": true,
    "list": [
      { "key": "TIAN_E_GUIREN", "pillar": "year" }
    ]
  }
}
```

### 4.2 보강된 페이로드 (After Enrichment)

```json
{
  "structure": {
    "primary": "ZHENGGUAN",
    "primary_ko": "정관격",  // 추가
    "confidence": "high",
    "candidates": [
      {
        "type": "ZHENGGUAN",
        "type_ko": "정관격",  // 추가
        "score": 87
      }
    ]
  },
  "strength": {
    "level": "weak",
    "level_ko": "약",  // 추가
    "basis": { "month_state": "囚" }
  },
  "ten_gods": {
    "summary": {
      "year_stem": "正官",
      "month_stem": "偏財"
    },
    "summary_ko": {  // 추가
      "year_stem": "정관",
      "month_stem": "편재"
    }
  },
  "shensha": {
    "enabled": true,
    "list": [
      {
        "key": "TIAN_E_GUIREN",
        "label_ko": "천을귀인",  // 추가
        "pillar": "year"
      }
    ]
  },
  "_enrichment": {  // 메타데이터 추가
    "korean_labels_added": true,
    "locale": "ko-KR",
    "enricher_version": "1.0.0"
  }
}
```

---

## 5. LLM 프롬프트 예시

### 5.1 Before (현재)

```
당신은 사주 전문가입니다. 다음 분석 결과를 해석해주세요:

Structure: ZHENGGUAN (confidence: high)
Strength: weak
Ten Gods: year_stem=正官, month_stem=偏財
Shensha: TIAN_E_GUIREN at year pillar
```

→ LLM이 한자/코드를 모를 가능성

### 5.2 After (보강 후)

```
당신은 사주 전문가입니다. 다음 분석 결과를 해석해주세요:

격국: 정관격 (ZHENGGUAN, confidence: high)
강약: 약 (weak)
십신: 년간=정관, 월간=편재
신살: 천을귀인 (년주)

원본 데이터:
{
  "structure": { "primary_ko": "정관격", ... },
  "strength": { "level_ko": "약", ... },
  ...
}
```

→ LLM이 한글로 직접 이해 가능

---

## 6. 구현 체크리스트

### Phase 1: 기본 구현 (1일)

- [ ] `korean_enricher.py` 생성 (150-200줄)
  - [ ] `KoreanLabelEnricher` 클래스
  - [ ] `from_file()` 로더
  - [ ] `enrich()` 메서드 (structure, strength, ten_gods, shensha)
- [ ] `llm_guard.py` 수정 (10줄 추가)
  - [ ] `KoreanLabelEnricher` 통합
  - [ ] `prepare_payload()` 수정
- [ ] `localization_ko_v1.json` 확장 (30줄 추가)
  - [ ] strength_ko 매핑
  - [ ] relations_ko 매핑

### Phase 2: 정책 보완 (0.5일)

- [ ] `strength_policy_v2.json` label_ko 추가
- [ ] gyeokguk, shensha 로더 구현
- [ ] 예외 처리 (매핑 없는 경우 원본 반환)

### Phase 3: 테스트 (0.5일)

- [ ] `test_korean_enricher.py` 생성
  - [ ] structure 보강 테스트
  - [ ] strength 보강 테스트
  - [ ] ten_gods 보강 테스트
  - [ ] shensha 보강 테스트
  - [ ] 메타데이터 검증
- [ ] `test_llm_guard.py` 업데이트
  - [ ] prepare_payload() 보강 검증

**총 예상 기간**: 2일

---

## 7. 장단점 비교

### 7.1 이 방식 (LLM 레이어 보강)

| 장점 | 단점 |
|------|------|
| ✅ 엔진 코드 수정 불필요 | ⚠️ API 응답은 여전히 영어/코드 |
| ✅ 2일 내 완료 가능 | ⚠️ LLM 거치지 않으면 한글 없음 |
| ✅ 안전성 높음 (엔진 로직 불변) | ⚠️ 이중 관리 가능성 |
| ✅ localization 파일만 수정 | ⚠️ 향후 API도 수정 시 중복 |

### 7.2 대안: 엔진 직접 수정

| 장점 | 단점 |
|------|------|
| ✅ API와 LLM 모두 한글 | ❌ 엔진 코드 대대적 수정 |
| ✅ 일관된 출력 | ❌ 5-7일 소요 |
| ✅ 장기적으로 깔끔 | ❌ 리스크 높음 (47개 테스트 영향) |

---

## 8. 권장 전략: 2단계 접근

### 8.1 단기 (즉시): LLM 레이어 보강

**목표**: LLM에게 한글로 전달 (2일)
**방법**: 이 제안서 내용 구현
**효과**: LLM 응답 품질 즉시 개선

### 8.2 중기 (3-6개월 후): 엔진 통합

**목표**: API 응답도 한글 구조화
**방법**: AnalysisResponse 모델 수정, 엔진별 label_ko 추가
**효과**: 완전한 다국어 지원

**마이그레이션**:
1. LLM 레이어 보강으로 localization 매핑 검증
2. 검증된 매핑을 엔진에 점진적 통합
3. KoreanLabelEnricher 제거 (엔진이 직접 제공)

---

## 9. 예상 효과

### 9.1 LLM 응답 품질 향상

**Before**:
> "Your chart shows ZHENGGUAN structure with weak strength..."

**After**:
> "귀하의 사주는 정관격으로, 일간이 약한 편입니다..."

### 9.2 개발자 경험 개선

```python
# LLM에게 전달 시
payload = llm_guard.prepare_payload(response)

# 자동으로 한글 레이블 추가됨
assert payload["structure"]["primary_ko"] == "정관격"
assert payload["strength"]["level_ko"] == "약"
```

### 9.3 프롬프트 작성 용이

```python
prompt = f"""
사주 분석 결과:
- 격국: {payload['structure']['primary_ko']}
- 강약: {payload['strength']['level_ko']}
- 년간십신: {payload['ten_gods']['summary_ko']['year_stem']}

위 정보를 바탕으로 종합 해석을 제공하세요.
"""
```

---

## 10. 결론

### 10.1 즉시 실행 가능

✅ **이 제안은 실용적이고 안전합니다**:
- 엔진 코드 불변 (47개 테스트 영향 없음)
- 2일 내 구현 완료
- LLM 응답 품질 즉시 개선

### 10.2 권장 조치

1. **지금 당장**: LLM 레이어 보강 구현 (이 문서 내용)
2. **3개월 후**: 효과 검증 후 엔진 통합 여부 결정
3. **6개월 후**: API 다국어화 완성

### 10.3 다음 단계

**즉시 시작 가능한 작업**:
```bash
# 1. korean_enricher.py 생성
# 2. localization_ko_v1.json 확장 (strength_ko, relations_ko 추가)
# 3. llm_guard.py에 통합
# 4. 테스트 작성
# 5. 2일 후 배포
```

---

**제안서 버전**: 1.0.0
**작성자**: Saju Engine Development Team
**승인 대기**: Product Owner
