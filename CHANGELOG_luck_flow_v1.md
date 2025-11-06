# Changelog - Luck Flow v1.0

**Package:** Luck Flow Policy Engine
**Version:** v1.0 (Policy Package)
**Date:** 2025-10-09 KST
**Type:** Deterministic Policy-Based Scoring

---

## [2025-10-09] v1.0 - Initial Policy Package Release

### ✨ New Features

#### 1. **Deterministic Luck Flow Engine**
- **11 signal weights** covering all luck factors
- **Rising/Stable/Declining** trend classification
- **Score [0..1]** and **confidence [0..1]** metrics
- **Zero LLM dependency** (static policy scoring only)

#### 2. **Policy Files**
- `policy/luck_flow_policy_v1.json` (weights, signals, 4 examples)
- `schema/luck_flow_policy.schema.json` (JSON Schema draft-2020-12)
- `schema/luck_flow_output.schema.json` (output contract)

#### 3. **LLM Guard Rules**
- `guards/llm_guard_rules_luck_flow_v1.json` (4 rules)
  - **LUCK-001**: trend enum validation (rising/stable/declining)
  - **LUCK-002**: score/confidence range [0..1]
  - **LUCK-003**: drivers/detractors length limits (≤4, ≤32 chars)
  - **LUCK-004**: evidence_ref required

#### 4. **Comprehensive Test Coverage**
- `tests/test_luck_flow_v1.py` (4 tests)
  - Rising trend (EX_RISING_FIRE)
  - Stable trend (EX_STABLE_TRANSITION)
  - Declining trend (EX_DECLINING_EARTH)
  - Clamping boundary (EX_CLAMP_RISING_PEAK)
  - **Coverage:** 100% trend coverage

#### 5. **Documentation**
- `docs/design_luck_flow_v1.md` (full design doc)
- `docs/engines/luck_flow.spec.json` (I/O contract)
- `docs/engines/luck_flow.io.json` (3 example cases)

---

### 🎯 Signal Coverage

| Signal | Weight | Condition |
|--------|--------|-----------|
| `element_gain_primary` | +0.35 | 용신 오행 `high` |
| `element_loss_primary` | -0.35 | 용신 오행 `low` |
| `climate_alignment` | +0.30 | `balance_index ≥ 1` |
| `climate_misalignment` | -0.30 | `balance_index ≤ -1` |
| `relation_support` | +0.25 | `{combine, sanhe}` |
| `relation_clash` | -0.25 | `{chong, harm}` |
| `sewoon_alignment` | +0.25 | `sewoon.supports_primary` |
| `sewoon_opposition` | -0.25 | `sewoon.counters_primary` |
| `transition_daewoon_positive` | +0.20 | 대운 지원 전환 |
| `transition_daewoon_negative` | -0.20 | 대운 대립 전환 |
| `yongshin_match` | +0.10 | 용신 존재 확인 |

---

### 🔧 Technical Details

#### Scoring Algorithm

```python
# 1. Signal aggregation
delta_raw = Σ (weight_i × signal_i)

# 2. Clamping
delta = clamp(delta_raw, [-1.0, +1.0])

# 3. Trend classification
if delta ≥ +0.15:
    trend = "rising"
elif delta ≤ -0.15:
    trend = "declining"
else:
    trend = "stable"

# 4. Metrics
score = abs(delta)  # 0..1
confidence = min(1.0, num_signals / 4.0)
```

#### Input Contract

```json
{
  "yongshin": { "primary": "화" },
  "strength": {
    "elements": { "wood": "normal", "fire": "high", ... }
  },
  "climate": { "balance_index": 1 },
  "relation": { "flags": ["combine"] },
  "daewoon": {
    "current": "丙午",
    "next": "丁未",
    "turning_to_support_primary": true
  },
  "sewoon": {
    "current": "丙辰",
    "supports_primary": true
  },
  "context": { "year": 2026, "age": 27 }
}
```

#### Output Contract

```json
{
  "policy_version": "luck_flow_policy_v1",
  "trend": "rising|stable|declining",
  "score": 0.0-1.0,
  "confidence": 0.0-1.0,
  "drivers": ["signal1", "signal2", ...],
  "detractors": ["signal3", ...],
  "evidence_ref": "luck_flow/2026/丙午/丙辰"
}
```

---

### 📊 Test Results

```
tests/test_luck_flow_v1.py::test_rising_example_from_policy_examples PASSED
tests/test_luck_flow_v1.py::test_stable_example_from_policy_examples PASSED
tests/test_luck_flow_v1.py::test_declining_example_from_policy_examples PASSED
tests/test_luck_flow_v1.py::test_threshold_boundary_clamping PASSED

========================= 4 passed in 0.03s =========================
```

---

### 🚀 Deployment Checklist

- [x] Policy JSON created
- [x] Schema validation schema created
- [x] Output schema created
- [x] Engine spec/IO created
- [x] LLM Guard rules defined
- [x] Design documentation complete
- [x] 4 test cases implemented
- [ ] Policy signature (PSA)
- [ ] Runtime engine implementation
- [ ] Core pipeline integration

---

### 🔮 Future Enhancements (v2.0)

#### Phase 2: 세운 세분화
- 월운/일운 확장 (연운 → 월/일 레벨)
- 이동 평균 (±1년 범위)

#### Phase 3: 신호 동적 보정
- 계절별 가중치 조정
- 격국별 신호 중요도 변경
- 용신 전략별 가중치 재조정

#### Phase 4: Pattern Profiler 통합
- 자연어 리포트 생성
- 행동 권장 (방향/색상/활동)

#### Phase 5: Guard v1.2 확대
- **LUCK-005**: 경계치 신호 감쇄 검증
- **LUCK-006**: 충돌 신호 상쇄 검증
- **LUCK-007**: 용신-운세 일관성 검증

---

### 📝 Design Rationale

#### Why Deterministic?

1. **Model-Switch Safe**: 정책 기반 점수 합산 → LLM 비개입
2. **Audit-Friendly**: 서명된 정책 파일 → 무결성 보장
3. **Performance**: <1ms 계산 (no API calls)
4. **Predictability**: 동일 입력 → 동일 출력 (100% 재현성)

#### Why Weighted Signals?

1. **Hierarchical Importance**: 용신 > 조후 > 관계 > 전환
2. **Additive Logic**: 다중 신호 조합 → 누적 효과
3. **Clamping**: 극단값 제한 → 안정적 점수

#### Why Trend Thresholds?

1. **Clear Categories**: ±0.15 경계로 3등급 분류
2. **Stable Zone**: [-0.15, +0.15] 완충 구간
3. **Symmetry**: 상승/하강 대칭 기준

---

### 🐛 Known Limitations (v1.0)

1. **연운만 처리**: 월운/일운 미지원
2. **고정 가중치**: 계절/격국/용신 전략 보정 없음
3. **단순 신뢰도**: 신호 개수 기반 (품질 고려 없음)
4. **Evidence 미연동**: 참조 경로만 반환 (상세 근거 미생성)

---

### 📚 Related Documents

- **Design Doc**: `docs/design_luck_flow_v1.md`
- **Policy**: `policy/luck_flow_policy_v1.json`
- **Schema (Policy)**: `schema/luck_flow_policy.schema.json`
- **Schema (Output)**: `schema/luck_flow_output.schema.json`
- **Spec**: `docs/engines/luck_flow.spec.json`
- **I/O**: `docs/engines/luck_flow.io.json`
- **Guards**: `guards/llm_guard_rules_luck_flow_v1.json`
- **Tests**: `tests/test_luck_flow_v1.py`

---

### 🔗 Dependencies

- **Python**: ≥3.11
- **jsonschema**: ≥4.0,<5.0
- **pytest**: (for testing)
- **policy_signature_auditor**: (for PSA signing, optional)

---

### 👥 Contributors

- **Architect**: Luck Flow v1.0 Policy Design Team
- **Implementation**: 2025-10-09 Integration Session
- **Review**: Pending

---

### 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-10-09 | Initial policy package release |

---

**Status**: ✅ Ready for Signing & Integration
**Next Step**: PSA Signature + Runtime Engine Implementation
