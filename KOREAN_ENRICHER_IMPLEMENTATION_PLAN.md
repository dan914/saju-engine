# KoreanLabelEnricher 구현 계획서

**작성일**: 2025-10-05
**목표**: LLM 전달 시 한국어 레이블 자동 보강
**예상 기간**: 2-3일
**상태**: 📋 구현 대기

---

## 📋 Executive Summary

사주 엔진의 영문/코드 출력을 **LLM 전달 직전에 한국어로 보강**하는 KoreanLabelEnricher 클래스를 구현합니다. 엔진 코드 수정 없이 **LLMGuard 레이어에서 동적 매핑**을 수행합니다.

### 핵심 목표

✅ 141개 용어 전체 매핑 (localization_ko_v1.json 활용)
✅ 엔진 코드 수정 없음 (비침습적)
✅ LLM 페이로드에만 한글 추가
✅ 2-3일 내 구현 완료

---

## 1. 아키텍처 설계

### 1.1 데이터 흐름

```
AnalysisEngine.analyze()
    ↓
AnalysisResponse (원본: 영문/코드)
    ↓
LLMGuard.prepare_payload()
    ↓
KoreanLabelEnricher.enrich()  ← 새로 구현
    ↓
Enriched Payload (한글 레이블 추가)
    ↓
LLM에게 전달
```

### 1.2 파일 구조

```
services/analysis-service/
├── app/
│   ├── core/
│   │   ├── korean_enricher.py          # 신규 (200-250줄)
│   │   └── llm_guard.py                # 수정 (10줄 추가)
│   └── models/
│       └── analysis.py                 # 수정 (structure_validity 추가)
└── tests/
    └── test_korean_enricher.py         # 신규 (200-250줄)
```

---

## 2. 구현 단계별 계획

### Phase 1: KoreanLabelEnricher 클래스 구현 (1일)

#### 1.1 기본 구조 작성

**파일**: `services/analysis-service/app/core/korean_enricher.py`

```python
"""Korean label enrichment for LLM payload."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

# 정책 파일 경로
POLICY_BASE = Path(__file__).resolve().parents[4]
LOCALIZATION_KO_PATH = (
    POLICY_BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "localization_ko_v1.json"
)
GYEOKGUK_POLICY_PATH = (
    POLICY_BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "gyeokguk_policy.json"
)
SHENSHA_POLICY_PATH = (
    POLICY_BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "shensha_v2_policy.json"
)
SIXTY_JIAZI_PATH = (
    POLICY_BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "sixty_jiazi.json"
)


@dataclass(slots=True)
class KoreanLabelEnricher:
    """Enrich analysis payload with Korean labels for LLM consumption."""

    # localization_ko_v1.json 매핑
    ten_gods_ko: Dict[str, str]
    role_ko: Dict[str, str]
    relation_ko: Dict[str, str]
    strength_ko: Dict[str, str]
    luck_direction_ko: Dict[str, str]
    confidence_ko: Dict[str, str]
    validity_ko: Dict[str, str]
    pillar_ko: Dict[str, str]
    month_state_ko: Dict[str, str]
    relation_types_ko: Dict[str, str]
    recommendation_ko: Dict[str, str]

    # 정책 파일 매핑
    gyeokguk_ko: Dict[str, str]
    shensha_ko: Dict[str, str]
    jiazi_ko: Dict[str, str]

    @classmethod
    def from_files(cls) -> "KoreanLabelEnricher":
        """Load all Korean mappings from policy files."""
        # 1. localization_ko_v1.json 로드
        with LOCALIZATION_KO_PATH.open("r", encoding="utf-8") as f:
            loc_data = json.load(f)

        # 2. gyeokguk_policy.json 로드
        gyeokguk_ko = cls._load_gyeokguk_labels()

        # 3. shensha_v2_policy.json 로드
        shensha_ko = cls._load_shensha_labels()

        # 4. sixty_jiazi.json 로드
        jiazi_ko = cls._load_jiazi_labels()

        return cls(
            ten_gods_ko=loc_data.get("ten_gods_ko", {}),
            role_ko=loc_data.get("role_ko", {}),
            relation_ko=loc_data.get("relation_ko", {}),
            strength_ko=loc_data.get("strength_ko", {}),
            luck_direction_ko=loc_data.get("luck_direction_ko", {}),
            confidence_ko=loc_data.get("confidence_ko", {}),
            validity_ko=loc_data.get("structure_validity_ko", {}),
            pillar_ko=loc_data.get("pillar_ko", {}),
            month_state_ko=loc_data.get("month_state_ko", {}),
            relation_types_ko=loc_data.get("relation_types_ko", {}),
            recommendation_ko=loc_data.get("recommendation_action_ko", {}),
            gyeokguk_ko=gyeokguk_ko,
            shensha_ko=shensha_ko,
            jiazi_ko=jiazi_ko,
        )

    @staticmethod
    def _load_gyeokguk_labels() -> Dict[str, str]:
        """Load gyeokguk labels from policy file."""
        with GYEOKGUK_POLICY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for pattern in data.get("patterns", []):
            code = pattern.get("code")
            label_ko = pattern.get("label_ko")
            if code and label_ko:
                mapping[code] = label_ko
                # 한글→한글 pass-through
                mapping[label_ko] = label_ko

        return mapping

    @staticmethod
    def _load_shensha_labels() -> Dict[str, str]:
        """Load shensha labels from policy file."""
        with SHENSHA_POLICY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for item in data.get("shensha_catalog", []):
            key = item.get("key")
            labels = item.get("labels", {})
            label_ko = labels.get("ko")
            if key and label_ko:
                mapping[key] = label_ko

        return mapping

    @staticmethod
    def _load_jiazi_labels() -> Dict[str, str]:
        """Load sixty jiazi labels from policy file."""
        with SIXTY_JIAZI_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        mapping = {}
        for record in data.get("records", []):
            stem = record.get("stem")
            branch = record.get("branch")
            label_ko = record.get("label_ko")
            if stem and branch and label_ko:
                key = f"{stem}{branch}"
                mapping[key] = label_ko

        return mapping

    def enrich(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add Korean labels to payload for LLM consumption."""
        enriched = payload.copy()

        # 1. Ten Gods
        self._enrich_ten_gods(enriched)

        # 2. Structure (Gyeokguk)
        self._enrich_structure(enriched)

        # 3. Strength
        self._enrich_strength(enriched)

        # 4. Luck Direction
        self._enrich_luck_direction(enriched)

        # 5. Shensha
        self._enrich_shensha(enriched)

        # 6. Relations
        self._enrich_relations(enriched)

        # 7. Recommendation
        self._enrich_recommendation(enriched)

        # 8. Add enrichment metadata
        enriched["_enrichment"] = {
            "korean_labels_added": True,
            "locale": "ko-KR",
            "enricher_version": "1.0.0",
            "mappings_count": self._count_mappings(),
        }

        return enriched

    def _enrich_ten_gods(self, payload: Dict[str, Any]) -> None:
        """Enrich ten_gods with Korean labels."""
        if "ten_gods" not in payload:
            return

        summary = payload["ten_gods"].get("summary", {})
        if summary:
            summary_ko = {}
            for key, value in summary.items():
                # 한자 → 한글 변환
                summary_ko[key] = self.ten_gods_ko.get(value, value)
            payload["ten_gods"]["summary_ko"] = summary_ko

    def _enrich_structure(self, payload: Dict[str, Any]) -> None:
        """Enrich structure with Korean labels."""
        if "structure" not in payload:
            return

        structure = payload["structure"]

        # Primary gyeokguk
        if "primary" in structure and structure["primary"]:
            primary = structure["primary"]
            structure["primary_ko"] = self.gyeokguk_ko.get(primary, primary)

        # Confidence
        if "confidence" in structure:
            confidence = structure["confidence"]
            structure["confidence_ko"] = self.confidence_ko.get(confidence, confidence)

        # Candidates
        if "candidates" in structure:
            for candidate in structure["candidates"]:
                cand_type = candidate.get("type")
                if cand_type:
                    candidate["type_ko"] = self.gyeokguk_ko.get(cand_type, cand_type)

    def _enrich_strength(self, payload: Dict[str, Any]) -> None:
        """Enrich strength with Korean labels."""
        if "strength" not in payload:
            return

        strength = payload["strength"]

        # Level
        if "level" in strength:
            level = strength["level"]
            strength["level_ko"] = self.strength_ko.get(level, level)

        # Basis - month_state
        if "basis" in strength and isinstance(strength["basis"], dict):
            basis = strength["basis"]
            if "month_state" in basis:
                month_state = basis["month_state"]
                basis["month_state_ko"] = self.month_state_ko.get(month_state, month_state)

    def _enrich_luck_direction(self, payload: Dict[str, Any]) -> None:
        """Enrich luck_direction with Korean labels."""
        if "luck_direction" not in payload:
            return

        luck_direction = payload["luck_direction"]

        if "direction" in luck_direction and luck_direction["direction"]:
            direction = luck_direction["direction"]
            luck_direction["direction_ko"] = self.luck_direction_ko.get(direction, direction)

    def _enrich_shensha(self, payload: Dict[str, Any]) -> None:
        """Enrich shensha with Korean labels."""
        if "shensha" not in payload:
            return

        shensha = payload["shensha"]

        if "list" in shensha and isinstance(shensha["list"], list):
            for item in shensha["list"]:
                # Key → label_ko
                if "key" in item:
                    key = item["key"]
                    item["label_ko"] = self.shensha_ko.get(key, key)

                # Pillar → pillar_ko
                if "pillar" in item:
                    pillar = item["pillar"]
                    item["pillar_ko"] = self.pillar_ko.get(pillar, pillar)

    def _enrich_relations(self, payload: Dict[str, Any]) -> None:
        """Enrich relations with Korean type labels."""
        if "relations" not in payload:
            return

        # Add relation type labels
        relations = payload["relations"]
        type_labels_ko = {}

        for rel_type in ["he6", "sanhe", "banhe", "chong", "xing", "po", "hai"]:
            if rel_type in relations:
                type_labels_ko[rel_type] = self.relation_types_ko.get(rel_type, rel_type)

        if type_labels_ko:
            payload["relations"]["_type_labels_ko"] = type_labels_ko

    def _enrich_recommendation(self, payload: Dict[str, Any]) -> None:
        """Enrich recommendation with Korean labels."""
        if "recommendation" not in payload:
            return

        recommendation = payload["recommendation"]

        if "action" in recommendation:
            action = recommendation["action"]
            recommendation["action_ko"] = self.recommendation_ko.get(action, action)

    def _count_mappings(self) -> int:
        """Count total number of mappings available."""
        return (
            len(self.ten_gods_ko) +
            len(self.strength_ko) +
            len(self.luck_direction_ko) +
            len(self.confidence_ko) +
            len(self.validity_ko) +
            len(self.pillar_ko) +
            len(self.month_state_ko) +
            len(self.relation_types_ko) +
            len(self.recommendation_ko) +
            len(self.gyeokguk_ko) +
            len(self.shensha_ko) +
            len(self.jiazi_ko)
        )
```

**예상 줄 수**: 200-250줄

---

### Phase 2: LLMGuard 통합 (0.5일)

#### 2.1 LLMGuard 수정

**파일**: `services/analysis-service/app/core/llm_guard.py`

```python
"""LLM validation and guard utilities for analysis responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import AnalysisResponse
from .recommendation import RecommendationGuard
from .text_guard import TextGuard
from .korean_enricher import KoreanLabelEnricher  # 추가


@dataclass(slots=True)
class LLMGuard:
    """Provide JSON validation and post-processing for LLM workflow."""

    text_guard: TextGuard
    recommendation_guard: RecommendationGuard
    korean_enricher: KoreanLabelEnricher  # 추가

    @classmethod
    def default(cls) -> "LLMGuard":
        return cls(
            text_guard=TextGuard.from_file(),
            recommendation_guard=RecommendationGuard.from_file(),
            korean_enricher=KoreanLabelEnricher.from_files(),  # 추가
        )

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Convert response to plain dict and enrich with Korean labels."""
        # Pydantic 검증
        AnalysisResponse.model_validate(response.model_dump())

        # 원본 페이로드
        payload = response.model_dump()

        # 한국어 레이블 보강
        enriched = self.korean_enricher.enrich(payload)

        return enriched

    # ... 나머지 메서드는 동일
```

**수정 줄 수**: 10줄

---

### Phase 3: 테스트 작성 (1일)

#### 3.1 Unit 테스트

**파일**: `services/analysis-service/tests/test_korean_enricher.py`

```python
"""Tests for KoreanLabelEnricher."""

import pytest
from app.core.korean_enricher import KoreanLabelEnricher


class TestKoreanLabelEnricher:
    """Test suite for Korean label enrichment."""

    @pytest.fixture
    def enricher(self):
        """Create enricher instance."""
        return KoreanLabelEnricher.from_files()

    def test_load_all_mappings(self, enricher):
        """Test that all mappings are loaded correctly."""
        # localization_ko_v1.json
        assert len(enricher.ten_gods_ko) == 10
        assert enricher.ten_gods_ko["BI"] == "비견"
        assert enricher.ten_gods_ko["JG"] == "정관"

        assert len(enricher.strength_ko) == 5
        assert enricher.strength_ko["weak"] == "신약"
        assert enricher.strength_ko["balanced"] == "중화"

        assert len(enricher.luck_direction_ko) == 2
        assert enricher.luck_direction_ko["forward"] == "순행"

        assert len(enricher.pillar_ko) == 4
        assert enricher.pillar_ko["year"] == "연주"

        # gyeokguk_policy.json
        assert len(enricher.gyeokguk_ko) >= 14
        assert enricher.gyeokguk_ko["ZHENGGUAN"] == "정관격"

        # shensha_v2_policy.json
        assert len(enricher.shensha_ko) == 20
        assert enricher.shensha_ko["TIAN_E_GUIREN"] == "천을귀인"

        # sixty_jiazi.json
        assert len(enricher.jiazi_ko) == 60
        assert enricher.jiazi_ko["甲子"] == "갑자"

    def test_enrich_ten_gods(self, enricher):
        """Test ten_gods enrichment."""
        payload = {
            "ten_gods": {
                "summary": {
                    "year_stem": "正官",
                    "month_stem": "偏財"
                }
            }
        }

        enriched = enricher.enrich(payload)

        assert "summary_ko" in enriched["ten_gods"]
        assert enriched["ten_gods"]["summary_ko"]["year_stem"] == "정관"
        assert enriched["ten_gods"]["summary_ko"]["month_stem"] == "편재"

    def test_enrich_structure(self, enricher):
        """Test structure enrichment."""
        payload = {
            "structure": {
                "primary": "ZHENGGUAN",
                "confidence": "high",
                "candidates": [
                    {"type": "ZHENGGUAN", "score": 87},
                    {"type": "ZHENGCAI", "score": 45}
                ]
            }
        }

        enriched = enricher.enrich(payload)

        assert enriched["structure"]["primary_ko"] == "정관격"
        assert enriched["structure"]["confidence_ko"] == "높음"
        assert enriched["structure"]["candidates"][0]["type_ko"] == "정관격"
        assert enriched["structure"]["candidates"][1]["type_ko"] == "정재격"

    def test_enrich_strength(self, enricher):
        """Test strength enrichment."""
        payload = {
            "strength": {
                "level": "weak",
                "basis": {
                    "month_state": "囚"
                }
            }
        }

        enriched = enricher.enrich(payload)

        assert enriched["strength"]["level_ko"] == "신약"
        assert enriched["strength"]["basis"]["month_state_ko"] == "수"

    def test_enrich_luck_direction(self, enricher):
        """Test luck_direction enrichment."""
        payload = {
            "luck_direction": {
                "direction": "forward",
                "method": "some_method"
            }
        }

        enriched = enricher.enrich(payload)

        assert enriched["luck_direction"]["direction_ko"] == "순행"

    def test_enrich_shensha(self, enricher):
        """Test shensha enrichment."""
        payload = {
            "shensha": {
                "enabled": True,
                "list": [
                    {"key": "TIAN_E_GUIREN", "pillar": "year"},
                    {"key": "YUE_DE", "pillar": "month"}
                ]
            }
        }

        enriched = enricher.enrich(payload)

        assert enriched["shensha"]["list"][0]["label_ko"] == "천을귀인"
        assert enriched["shensha"]["list"][0]["pillar_ko"] == "연주"
        assert enriched["shensha"]["list"][1]["label_ko"] == "월덕"
        assert enriched["shensha"]["list"][1]["pillar_ko"] == "월주"

    def test_enrich_relations(self, enricher):
        """Test relations type labels enrichment."""
        payload = {
            "relations": {
                "he6": [["子", "丑"]],
                "sanhe": [["申", "子", "辰"]],
                "chong": [["子", "午"]]
            }
        }

        enriched = enricher.enrich(payload)

        assert "_type_labels_ko" in enriched["relations"]
        assert enriched["relations"]["_type_labels_ko"]["he6"] == "육합"
        assert enriched["relations"]["_type_labels_ko"]["sanhe"] == "삼합"
        assert enriched["relations"]["_type_labels_ko"]["chong"] == "충"

    def test_enrich_recommendation(self, enricher):
        """Test recommendation enrichment."""
        payload = {
            "recommendation": {
                "enabled": True,
                "action": "allow"
            }
        }

        enriched = enricher.enrich(payload)

        assert enriched["recommendation"]["action_ko"] == "표시"

    def test_missing_values_passthrough(self, enricher):
        """Test that missing values pass through unchanged."""
        payload = {
            "strength": {
                "level": "unknown_level"
            }
        }

        enriched = enricher.enrich(payload)

        # 매핑 없으면 원본 반환
        assert enriched["strength"]["level_ko"] == "unknown_level"

    def test_empty_payload(self, enricher):
        """Test enrichment of empty payload."""
        payload = {}

        enriched = enricher.enrich(payload)

        # 메타데이터만 추가
        assert "_enrichment" in enriched
        assert enriched["_enrichment"]["korean_labels_added"] is True

    def test_enrichment_metadata(self, enricher):
        """Test enrichment metadata."""
        payload = {"ten_gods": {"summary": {}}}

        enriched = enricher.enrich(payload)

        assert "_enrichment" in enriched
        assert enriched["_enrichment"]["locale"] == "ko-KR"
        assert enriched["_enrichment"]["enricher_version"] == "1.0.0"
        assert enriched["_enrichment"]["mappings_count"] > 100

    def test_integration_with_llm_guard(self):
        """Test integration with LLMGuard."""
        from app.core.llm_guard import LLMGuard
        from app.models.analysis import AnalysisResponse, TenGodsResult

        # Mock response
        response = AnalysisResponse(
            ten_gods=TenGodsResult(summary={"year_stem": "正官"}),
            # ... other required fields
        )

        guard = LLMGuard.default()
        payload = guard.prepare_payload(response)

        assert "ten_gods" in payload
        assert "summary_ko" in payload["ten_gods"]
        assert payload["ten_gods"]["summary_ko"]["year_stem"] == "정관"
```

**예상 줄 수**: 200-250줄

---

### Phase 4: 통합 테스트 및 검증 (0.5일)

#### 4.1 전체 흐름 테스트

```python
def test_end_to_end_enrichment():
    """Test complete enrichment flow."""
    # 1. AnalysisEngine 호출
    from app.core.engine import AnalysisEngine
    from app.models.analysis import AnalysisRequest, PillarInput

    engine = AnalysisEngine()
    request = AnalysisRequest(
        pillars={
            "year": PillarInput(pillar="壬申"),
            "month": PillarInput(pillar="辛未"),
            "day": PillarInput(pillar="丁丑"),
            "hour": PillarInput(pillar="庚子"),
        }
    )

    response = engine.analyze(request)

    # 2. LLMGuard로 보강
    from app.core.llm_guard import LLMGuard

    guard = LLMGuard.default()
    enriched_payload = guard.prepare_payload(response)

    # 3. 검증
    assert "_enrichment" in enriched_payload
    assert enriched_payload["_enrichment"]["korean_labels_added"] is True

    # 모든 한글 필드 존재 확인
    if "structure" in enriched_payload and enriched_payload["structure"].get("primary"):
        assert "primary_ko" in enriched_payload["structure"]

    if "strength" in enriched_payload:
        assert "level_ko" in enriched_payload["strength"]
```

---

## 3. 타임라인

### Day 1: Core 구현
- [ ] 08:00-10:00: KoreanLabelEnricher 기본 구조 작성
- [ ] 10:00-12:00: 로더 메서드 구현 (_load_gyeokguk, _load_shensha 등)
- [ ] 13:00-15:00: enrich 메서드 구현 (ten_gods, structure, strength)
- [ ] 15:00-17:00: enrich 메서드 구현 (shensha, relations, recommendation)
- [ ] 17:00-18:00: 코드 리뷰 및 리팩토링

### Day 2: 통합 및 테스트
- [ ] 08:00-09:00: LLMGuard 통합
- [ ] 09:00-12:00: Unit 테스트 작성 (10개 테스트)
- [ ] 13:00-15:00: 통합 테스트 작성
- [ ] 15:00-17:00: Edge case 테스트 (누락 값, 빈 페이로드 등)
- [ ] 17:00-18:00: 테스트 실행 및 버그 수정

### Day 3: 검증 및 문서화
- [ ] 08:00-10:00: 전체 테스트 스위트 실행
- [ ] 10:00-12:00: 실제 데이터로 검증
- [ ] 13:00-15:00: 문서 작성 (README, API docs)
- [ ] 15:00-17:00: 코드 리뷰 및 최종 수정
- [ ] 17:00-18:00: PR 생성 및 배포 준비

---

## 4. 체크리스트

### Phase 1: Core 구현 ✅

- [ ] `korean_enricher.py` 파일 생성
- [ ] `KoreanLabelEnricher` 클래스 정의
- [ ] `from_files()` 클래스 메서드 구현
- [ ] `_load_gyeokguk_labels()` 구현
- [ ] `_load_shensha_labels()` 구현
- [ ] `_load_jiazi_labels()` 구현
- [ ] `enrich()` 메인 메서드 구현
- [ ] `_enrich_ten_gods()` 구현
- [ ] `_enrich_structure()` 구현
- [ ] `_enrich_strength()` 구현
- [ ] `_enrich_luck_direction()` 구현
- [ ] `_enrich_shensha()` 구현
- [ ] `_enrich_relations()` 구현
- [ ] `_enrich_recommendation()` 구현
- [ ] `_count_mappings()` 유틸리티 구현

### Phase 2: LLMGuard 통합 ✅

- [ ] `llm_guard.py` import 추가
- [ ] `LLMGuard.__init__` korean_enricher 추가
- [ ] `LLMGuard.default()` 수정
- [ ] `prepare_payload()` 메서드 수정

### Phase 3: 테스트 작성 ✅

- [ ] `test_korean_enricher.py` 파일 생성
- [ ] `test_load_all_mappings()` 작성
- [ ] `test_enrich_ten_gods()` 작성
- [ ] `test_enrich_structure()` 작성
- [ ] `test_enrich_strength()` 작성
- [ ] `test_enrich_luck_direction()` 작성
- [ ] `test_enrich_shensha()` 작성
- [ ] `test_enrich_relations()` 작성
- [ ] `test_enrich_recommendation()` 작성
- [ ] `test_missing_values_passthrough()` 작성
- [ ] `test_empty_payload()` 작성
- [ ] `test_enrichment_metadata()` 작성
- [ ] `test_integration_with_llm_guard()` 작성

### Phase 4: 검증 및 배포 ✅

- [ ] 모든 테스트 통과 확인
- [ ] 실제 AnalysisResponse로 검증
- [ ] LLM 페이로드 샘플 생성
- [ ] 문서 작성
- [ ] 코드 리뷰 요청
- [ ] PR 생성

---

## 5. 예상 결과물

### 5.1 Before (현재)

```json
{
  "structure": { "primary": "ZHENGGUAN", "confidence": "high" },
  "strength": { "level": "weak" },
  "luck_direction": { "direction": "forward" },
  "shensha": { "list": [{ "key": "TIAN_E_GUIREN", "pillar": "year" }] }
}
```

### 5.2 After (구현 후)

```json
{
  "structure": {
    "primary": "ZHENGGUAN",
    "primary_ko": "정관격",
    "confidence": "high",
    "confidence_ko": "높음"
  },
  "strength": {
    "level": "weak",
    "level_ko": "신약"
  },
  "luck_direction": {
    "direction": "forward",
    "direction_ko": "순행"
  },
  "shensha": {
    "list": [
      {
        "key": "TIAN_E_GUIREN",
        "label_ko": "천을귀인",
        "pillar": "year",
        "pillar_ko": "연주"
      }
    ]
  },
  "_enrichment": {
    "korean_labels_added": true,
    "locale": "ko-KR",
    "enricher_version": "1.0.0",
    "mappings_count": 141
  }
}
```

---

## 6. 위험 요소 및 대응

| 위험 | 확률 | 영향 | 대응 방안 |
|------|------|------|----------|
| 정책 파일 경로 오류 | 중간 | 높음 | 상대 경로 검증, 파일 존재 확인 |
| 누락된 매핑 | 낮음 | 중간 | 원본 값 반환 (graceful degradation) |
| 성능 저하 | 낮음 | 낮음 | 매핑 딕셔너리 O(1) 조회 |
| 한글 인코딩 문제 | 낮음 | 중간 | UTF-8 명시, 테스트 강화 |

---

## 7. 성공 기준

✅ **기능 요구사항**
- 141개 전체 매핑 동작
- LLMGuard 통합 완료
- 모든 테스트 통과

✅ **성능 요구사항**
- enrich() 실행 시간 < 10ms
- 메모리 증가 < 1MB

✅ **품질 요구사항**
- 테스트 커버리지 > 90%
- 타입 힌트 100%
- 문서화 완료

---

## 8. 다음 단계 (구현 완료 후)

1. **프로덕션 배포** (0.5일)
   - CI/CD 파이프라인 테스트
   - Staging 환경 검증
   - Production 배포

2. **모니터링** (지속)
   - LLM 응답 품질 측정
   - 매핑 누락 항목 모니터링
   - 사용자 피드백 수집

3. **확장** (향후)
   - 영어 레이블 추가 (label_en)
   - 중국어 레이블 추가 (label_zh)
   - 다국어 전환 API 파라미터 (`?locale=ko-KR`)

---

**문서 버전**: 1.0.0
**작성자**: Saju Engine Development Team
**예상 완료일**: 2025-10-08 (3일 후)
**상태**: 📋 구현 대기
