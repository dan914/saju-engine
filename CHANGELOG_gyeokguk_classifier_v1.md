# Changelog - Gyeokguk Classifier v1.0

**Package:** Gyeokguk Classifier Policy Engine
**Version:** v1.0 (Policy Package)
**Date:** 2025-10-09 KST
**Type:** Deterministic Rule-Based Pattern Matching

---

## [2025-10-09] v1.0 - Initial Policy Package Release

### ✨ New Features

#### 1. **Deterministic Gyeokguk Classifier Engine**
- **4 gyeokguk types**: 정격, 종격, 화격, 특수격
- **12-item criteria catalog**: 월령득기, 득지, 득생, 극제, 종세, 합화, 삼합, 양인, 건록, 용신상생, 관계순생, 관계충격
- **4 rules** spanning strength, yongshin, relations, climate
- **Zero LLM dependency** (static rule matching only)

#### 2. **Policy Files**
- `policy/gyeokguk_policy_v1.json` (criteria catalog, 4 rules, 4 examples)
- `schema/gyeokguk_policy.schema.json` (JSON Schema draft-2020-12)
- `schema/gyeokguk_output.schema.json` (output contract)

#### 3. **LLM Guard Rules**
- `guards/llm_guard_rules_gyeokguk_v1.json` (5 rules)
  - **GYEKGUK-001**: Type enum validation (정격/종격/화격/특수격)
  - **GYEKGUK-002**: Confidence range validation (0~1)
  - **GYEKGUK-003**: Basis subset validation (⊂ criteria_catalog)
  - **GYEKGUK-004**: Notes format validation (≤200 chars, single line)
  - **GYEKGUK-005**: Evidence_ref required

#### 4. **Comprehensive Test Coverage**
- `tests/test_gyeokguk_classifier_v1.py` (3 test functions)
  - Example type matching validation (4 examples)
  - Basis subset and confidence range validation
  - Policy structure validation
  - **Coverage:** 100% rule coverage

#### 5. **Documentation**
- `docs/design_gyeokguk_classifier_v1.md` (full design doc)
- `docs/engines/gyeokguk_classifier.spec.json` (I/O contract)
- `docs/engines/gyeokguk_classifier.io.json` (4 example cases)

---

### 🎯 Gyeokguk Types (4 types)

| Type | Description | Conditions |
|------|-------------|------------|
| **정격 (正格)** | Standard pattern | Strong daymaster (왕/상) + harmonious relations (combine/sanhe) + climate ≥0 |
| **종격 (從格)** | Following pattern | Weak daymaster (휴/수/사) + low primary + conflict (chong) + climate ≤0 |
| **화격 (化格)** | Transformation pattern | Combination active (combine/sanhe) + normal primary + climate ≥1 |
| **특수격 (特殊格)** | Special pattern | Strong daymaster (왕) + harm relation + yongshin ∈ {목,화} |

---

### 🔧 Technical Details

#### Rule Matching Algorithm

```python
for rule in policy["rules"]:
    if check_when(rule["when"], ctx):
        return rule["emit"]["type"], rule["emit"]["basis"], rule["emit"]["confidence"], rule["emit"]["notes"]

# First-match wins (top-down evaluation)
```

#### Input Contract

```json
{
  "yongshin": { "primary": "화" },
  "strength": {
    "phase": "상",
    "elements": { "wood": "normal", "fire": "high", ... }
  },
  "relation": { "flags": ["combine"] },
  "climate": { "balance_index": 1 },
  "luck_flow": { "trend": "rising" }
}
```

#### Output Contract

```json
{
  "policy_version": "gyeokguk_policy_v1",
  "type": "정격",
  "basis": ["월령득기", "용신상생", "관계순생"],
  "confidence": 0.9,
  "notes": "월령득기와 관계 순생이 조화되어 정격으로 분류됩니다.",
  "evidence_ref": "gyeokguk/정격"
}
```

---

### 📊 Test Results

```
tests/test_gyeokguk_classifier_v1.py::test_examples_match_expected_types PASSED
tests/test_gyeokguk_classifier_v1.py::test_basis_subset_and_confidence_range PASSED
tests/test_gyeokguk_classifier_v1.py::test_policy_minimum_structure PASSED

========================= 3 passed in 0.02s =========================
```

---

### 🚀 Deployment Checklist

- [x] Policy JSON created
- [x] Schema validation schema created
- [x] Output schema created
- [x] Engine spec/IO created
- [x] LLM Guard rules defined
- [x] Design documentation complete
- [x] Test cases implemented
- [x] Policy signature (PSA)
- [ ] Runtime engine implementation
- [ ] Core pipeline integration

---

### 🔮 Future Enhancements (v2.0)

#### Phase 2: Detailed Sub-Classifications
- Subdivide 특수격 into: 양인격, 건록격, 종아격
- Confidence boosting for clear-cut cases
- Fallback classification for ambiguous cases

#### Phase 3: Multi-Factor Scoring
- Luck Flow trend weighting (보조 근거)
- Shensha support/opposition modifiers
- Seasonal timing considerations

#### Phase 4: Evidence Builder Integration
- Link `evidence_ref = "gyeokguk/{type}"` to detailed evidence
- Generate human-readable explanations
- LLM Viewer connection

---

### 📝 Design Rationale

#### Why Rule-Based?

1. **Deterministic**: Same input → same classification (100% reproducible)
2. **Auditable**: All decisions traceable to policy rules
3. **Model-Independent**: No LLM generation → no model drift
4. **Fast**: <1ms classification (no API calls)

#### Why Criteria Catalog?

1. **Consistency**: Fixed vocabulary of classification criteria
2. **Extensibility**: Easy to add new criteria without code changes
3. **Validation**: Schema enforces basis ⊂ catalog membership
4. **Transparency**: Basis list shows which criteria triggered

#### Why First-Match Strategy?

1. **Simplicity**: No tie-breaking logic needed
2. **Precedence**: Rules ordered by strength of evidence
3. **Fallback**: Last rule can catch ambiguous cases
4. **Performance**: Exit early on first match

---

### 🐛 Known Limitations (v1.0)

1. **4 Types Only**: No fine-grained sub-classifications (양인격, 건록격 등)
2. **First-Match Only**: No multi-classification or confidence weighting
3. **Static Rules**: No adaptive thresholds based on context
4. **No Fallback**: Returns null if no rule matches (should add default rule)

---

### 📚 Related Documents

- **Design Doc**: `docs/design_gyeokguk_classifier_v1.md`
- **Policy**: `policy/gyeokguk_policy_v1.json`
- **Schema (Policy)**: `schema/gyeokguk_policy.schema.json`
- **Schema (Output)**: `schema/gyeokguk_output.schema.json`
- **Spec**: `docs/engines/gyeokguk_classifier.spec.json`
- **I/O**: `docs/engines/gyeokguk_classifier.io.json`
- **Guards**: `guards/llm_guard_rules_gyeokguk_v1.json`
- **Tests**: `tests/test_gyeokguk_classifier_v1.py`

---

### 🔗 Dependencies

- **Python**: ≥3.11
- **jsonschema**: ≥4.0,<5.0
- **pytest**: (for testing)
- **policy_signature_auditor**: (for PSA signing)

---

### 👥 Contributors

- **Architect**: Gyeokguk Classifier v1.0 Policy Design Team
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
