# Changelog - Climate Advice MVP v1.0

**Package:** Climate Advice Mapping MVP
**Version:** v1.0
**Date:** 2025-10-09 KST
**Type:** Deterministic Policy Engine

---

## [2025-10-09] v1.0 - Initial Release (Model-Switch Safe)

### ✨ New Features

#### 1. **Deterministic Climate Advice Engine**
- **8 rules** covering all seasons: 봄/여름/장하/가을/겨울
- **Single-line advice** with 80-char limit (mobile-friendly)
- **First-match priority** (top-down rule ordering)
- **Zero LLM dependency** (static policy matching only)

#### 2. **Policy Files**
- `policy/climate_advice_policy_v1.json` (8 rules + fallback)
- `schema/climate_advice_policy.schema.json` (JSON Schema draft-2020-12)
- `schema/engine_summaries.v1.1.extension.climate.schema.json` (context extension)

#### 3. **LLM Guard Rules**
- `guards/llm_guard_rules_climate_mvp_v1.json` (3 rules)
  - **CLIMATE-ADVICE-001**: advice 있을 때 policy_id 필수
  - **CLIMATE-ADVICE-002**: 한 줄 제한
  - **CLIMATE-ADVICE-003**: 80자 제한

#### 4. **Comprehensive Test Coverage**
- `tests/test_climate_advice_mvp.py` (9 tests)
  - 8 golden path scenarios (all seasons)
  - 1 fallback scenario (balanced, no match)
  - **Coverage:** 100% rule coverage

#### 5. **Documentation**
- `docs/design_climate_balancer_v1.md` (full design doc)
- `docs/engines/climate_balancer_mvp.spec.json` (I/O contract)
- `docs/engines/climate_balancer_mvp.io.json` (example I/O)

#### 6. **CI/CD Integration**
- `.github/workflows/placeholder_guard.yml`
  - Schema validation
  - Pytest execution
  - PSA signature verification (optional)
  - Placeholder marker guard (CRITICAL: 0, MEDIUM: ≤5)

---

### 🎯 Rule Coverage

| Season | Rule IDs | Count |
|--------|----------|-------|
| 봄 (Spring) | WOOD_OVER_FIRE_WEAK | 1 |
| 여름 (Summer) | FIRE_OVER_WATER_WEAK, EARTH_EXCESS_DRYNESS | 2 |
| 장하 (Late Summer) | EARTH_EXCESS_DRYNESS, EARTH_EXCESS_HUMIDITY | 2 |
| 가을 (Autumn) | METAL_OVER_WOOD_WEAK, METAL_DRYNESS_RELIEF | 2 |
| 겨울 (Winter) | WATER_DEFICIT_IN_WINTER, WATER_OVER_FIRE_WEAK | 2 |
| **Total** | | **8** |

---

### 🔧 Technical Details

#### Policy Matching Algorithm

```python
for rule in policy["advice_table"]:
    # AND condition matching
    if match_season(rule, ctx) and \
       match_phase(rule, ctx) and \
       match_balance(rule, ctx) and \
       match_flags(rule, ctx):
        return rule["id"], rule["advice"]

# No match
return None, fallback_advice
```

#### Input Contract Extensions

```json
{
  "climate": {
    "flags": ["earth_excess", "dryness", "humidity", "coldness"]
  },
  "context": {
    "season": "봄|여름|장하|가을|겨울",
    "month_branch": "string"
  }
}
```

#### Output Contract

```json
{
  "advice": "string (1 line, ≤80 chars)",
  "matched_policy_id": "string | null",
  "evidence_ref": "string"
}
```

---

### 📊 Test Results

```
tests/test_climate_advice_mvp.py::test_spring_wood_over_fire_weak PASSED
tests/test_climate_advice_mvp.py::test_summer_fire_over_water_weak PASSED
tests/test_climate_advice_mvp.py::test_summer_earth_excess_dryness PASSED
tests/test_climate_advice_mvp.py::test_late_summer_earth_excess_humidity PASSED
tests/test_climate_advice_mvp.py::test_autumn_metal_over_wood_weak PASSED
tests/test_climate_advice_mvp.py::test_autumn_metal_dryness_relief PASSED
tests/test_climate_advice_mvp.py::test_winter_water_deficit PASSED
tests/test_climate_advice_mvp.py::test_winter_water_over_fire_weak_with_coldness PASSED
tests/test_climate_advice_mvp.py::test_balanced_fallback PASSED

========================= 9 passed in 0.05s =========================
```

---

### 🚀 Deployment Checklist

- [x] Policy JSON created
- [x] Schema validation passed
- [x] 9/9 tests passing
- [x] LLM Guard rules defined
- [x] Design documentation complete
- [x] CI workflow configured
- [ ] Policy signature (PSA)
- [ ] Core pipeline integration
- [ ] Evidence bundle integration

---

### 🔮 Future Enhancements (Post-MVP)

#### Phase 2: Multi-Match Weighted Ranking
- Collect all matching rules
- Rank by severity + proximity score
- Return top N matches (configurable)

#### Phase 3: Pattern Profiler Integration
- Add natural language context from Pattern Profiler
- Recommended actions (방향/색상/활동)
- Seasonal compatibility scores

#### Phase 4: Extended Guard Rules (v1.2)
- **CLIMATE-ADVICE-004**: Severity ↔ balance consistency
- **CLIMATE-ADVICE-005**: Yongshin strategy ↔ climate advice conflict detection
- **CLIMATE-ADVICE-006**: Multi-match redundancy/contradiction check

---

### 📝 Design Rationale

#### Why Deterministic?

1. **Model-Switch Safe**: No LLM generation → 모델 교체 시 편차 없음
2. **Audit-Friendly**: 정책 파일만 검증 → 서명으로 무결성 보장
3. **Performance**: <1ms matching (no API calls)
4. **Predictability**: 동일 입력 → 동일 출력 (100% 재현성)

#### Why Single-Line?

1. **Mobile UI**: 간결한 조언 → 카드 형식 적합
2. **Guard Simplicity**: 한 줄 제한 → LLM 생성 검증 불필요
3. **User Experience**: 핵심만 전달 → 인지 부담 최소화

#### Why Top-Down Matching?

1. **Priority Control**: 순서 = 우선순위 → 명확한 정책 의도
2. **Specificity First**: 구체적 규칙 위에 배치 → 일반 규칙 조기 매칭 방지
3. **Maintenance**: 새 규칙 추가 시 위치만 조정 → 간단한 우선순위 관리

---

### 🐛 Known Limitations (MVP)

1. **Single Match Only**: 복합 불균형 시 첫 번째 매칭만 반환
2. **No Severity Weighting**: 모든 규칙 동등 우선순위 (순서만)
3. **No Context Enrichment**: 자연어 설명 없음 (정책 문장만)
4. **No Evidence Bundle**: matched_policy_id만 반환 (상세 근거 미연동)

---

### 📚 Related Documents

- **Design Doc**: `docs/design_climate_balancer_v1.md`
- **Policy**: `policy/climate_advice_policy_v1.json`
- **Schema**: `schema/climate_advice_policy.schema.json`
- **Tests**: `tests/test_climate_advice_mvp.py`
- **Guards**: `guards/llm_guard_rules_climate_mvp_v1.json`

---

### 🔗 Dependencies

- **Python**: ≥3.11
- **jsonschema**: ≥4.0,<5.0
- **pytest**: (for testing)
- **policy_signature_auditor**: (for PSA signing, optional)

---

### 👥 Contributors

- **Architect**: Climate Balancer MVP Design Team
- **Implementation**: 2025-10-09 Integration Session
- **Review**: Pending

---

### 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-10-09 | Initial deterministic MVP release |

---

**Status**: ✅ Ready for Integration
**Next Step**: PSA Signature + Core Pipeline Integration
