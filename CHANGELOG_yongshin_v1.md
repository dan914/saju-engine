# Yongshin Selector — CHANGELOG

## v1.0.0 (2025-10-09)

### 초기 릴리스

**핵심 기능:**
- Strength/Relation/Climate/Distribution 기반 용신 자동 산출
- 5개 오행에 대한 점수화 및 우선순위 결정
- 용신(yongshin), 보조신(bojosin), 기신(gisin) 자동 분류

**정책 구성:**
- `strength_binning`: weak [0.0~0.4], balanced [0.4~0.6], strong [0.6~1.0]
- `base_preferences`: 강약별 기본 선호 오행 축
- `relation_bias_rules`: 6개 관계 타입별 가중치 조정
- `climate_bias`: 계절 오행 상생/상극 반영
- `distribution_bias`: 오행 과부족 편차 보정
- `confidence_model`: 신뢰도 계산 (0.40~0.98)

**의존성:**
- strength_policy_v2.json
- relation_weight_v1.0.0.json
- climate_policy_v1.json
- shensha_v2.json

**테스트:**
- 12개 JSONL 테스트 케이스 (신약/신강/중화 시나리오)
- 각 케이스별 최소 신뢰도 기대치 검증

**정책 서명:**
- 초기 상태: **UNSIGNED**
- Policy Signature Auditor v1.0으로 서명 예정

---

## 다음 버전 계획 (v1.1.0)

- [ ] 십신(Ten Gods) 가중치 추가
- [ ] 대운(Luck Pillars) 고려 확장
- [ ] 신살(Shensha) 특수 조건 반영
- [ ] 조후(Climate) 세부 전략 통합
- [ ] 전문가 검증 후 계수 미세 조정

---

## 릴리스 노트

**v1.0.0 주요 특징:**

1. **정책 기반 결정론적 산출**: LLM 개입 없이 용신 확정
2. **투명한 근거**: `rules_fired`, `rationale` 배열로 설명 가능
3. **LLM Guard 연동**: `EVIDENCE_BOUND` 규칙에서 `yongshin` 배열 참조
4. **확장 가능 구조**: 추가 바이어스 규칙 쉽게 삽입 가능

**알려진 제약:**
- 복잡한 종격(從格)/화격(化格) 미지원 (v1.1 계획)
- 대운·년운 동적 변화 미반영 (별도 엔진 필요)
- 조후 전략 단순화 (계절 오행만 고려)

**호환성:**
- JSON Schema Draft 2020-12
- Python 3.9+
- RFC-8785 canonical JSON 서명 준비

---

**작성자**: Saju Engine Team
**최종 갱신**: 2025-10-09 KST
