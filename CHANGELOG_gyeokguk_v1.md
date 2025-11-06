# Gyeokguk Classifier Changelog

## Version 1.0.0 (2025-10-09)

### Overview

Initial release of **Gyeokguk (格局) Classifier v1.0**, a deterministic pattern classification engine for Korean Four Pillars (Saju) analysis. This engine integrates outputs from Strength Evaluator v2.0, Relation Weight Evaluator v1.0, Yongshin Selector v1.0, and Shensha Catalog v2.0 to automatically classify destiny patterns (격국) with formation strength scoring and confidence metrics.

### Features

#### 1. Nine Gyeokguk Classes

**Core Patterns:**
- **JG-001 정격 (Regular Pattern)**: Balanced middle-strength patterns (strength 0.40-0.70)
- **JG-002 종강격 (Follow Strong)**: Extreme high-strength with companion/resource dominance (strength ≥0.80)
- **JG-003 종약격 (Follow Weak)**: Extreme low-strength with wealth/official dominance (strength ≤0.30)
- **JG-004 화격 (Transformation)**: Transformation patterns via ganhe_hua or sanhe formation

**Specialized Patterns:**
- **JG-005 인수격 (Resource Pattern)**: Resource (인성) dominance
- **JG-006 식상격 (Output Pattern)**: Output (식상) dominance
- **JG-007 관살격 (Official Pattern)**: Official (관살) dominance
- **JG-008 재격 (Wealth Pattern)**: Wealth (재성) dominance

**Invalid Pattern:**
- **JG-009 파격 (Broken Pattern)**: Excessive chong/xing/hai causing structural breakdown

#### 2. Formation Strength Scoring

**Formula:**
```
formation_strength = clamp(base_score + Σ(modifiers_hit), 0, 1)
```

**Modifiers by Category:**

**Relation Modifiers:**
- `sanhe_ge_0p70`: +0.09 to +0.18 (삼합 ≥0.70)
- `ganhe_hua_true`: +0.07 to +0.20 (간합화 성립)
- `liuhe_ge_0p50`: +0.02 to +0.06 (육합 ≥0.50)
- `chong_ge_0p60`: -0.09 to -0.20 (충 ≥0.60)
- `xing_ge_0p50`: -0.04 to -0.15 (형 ≥0.50)
- `hai_ge_0p35`: -0.02 to -0.08 (해 ≥0.35)

**Climate Modifiers:**
- `season_supports_core`: +0.02 to +0.10 (계절 오행이 core와 동일/생성)
- `season_conflicts_core`: -0.05 to -0.10 (계절 오행이 core와 상극)
- `support_label`: 강함 (+0.01 to +0.08), 보통 (0), 약함 (-0.04 to -0.08)

**Yongshin Synergy:**
- `yongshin_contains_core`: +0.02 to +0.10 (용신이 core element 포함)
- `yongshin_opposes_core`: -0.06 to -0.12 (용신이 core와 상극)

**Shensha Modifiers:**
- `favorable_each`: +0.01 to +0.04 per favorable shensha
- `unfavorable_each`: -0.03 to -0.05 per unfavorable shensha

#### 3. Confidence Calculation

**Formula:**
```
confidence = clamp(base_confidence + 0.03 * conditions_met_count - 0.02 * missing_conditions_count, 0, 1)
```

**Base Confidence by Pattern:**
- 화격 (JG-004): 0.78 (highest, due to clear transformation signal)
- 종강격 (JG-002): 0.75
- 종약격 (JG-003): 0.72
- 정격 (JG-001): 0.70
- 관살격 (JG-007): 0.67
- 인수격 (JG-005): 0.68
- 식상격 (JG-006): 0.66
- 재격 (JG-008): 0.65
- 파격 (JG-009): 0.50 (lowest, structural breakdown)

#### 4. Precedence on Tie

When multiple patterns have identical formation_strength scores, apply precedence order:

```
[JG-004, JG-001, JG-002, JG-003, JG-008, JG-007, JG-006, JG-005, JG-009]
```

**Rationale:**
1. **JG-004 (화격)**: Transformation patterns take highest priority (rare and significant)
2. **JG-001 (정격)**: Regular balanced patterns are archetypal defaults
3. **JG-002/003**: Follow patterns (strong/weak) ranked by frequency
4. **JG-008/007/006/005**: Specialized patterns ranked by structural clarity
5. **JG-009 (파격)**: Broken patterns are last resort (diagnostic fallback)

#### 5. Audit Trail

All outputs include comprehensive audit fields:

- **`rules_fired`**: List of modifiers applied (e.g., `"sanhe_ge_0p70 → +0.15"`)
- **`conditions_met`**: Conditions satisfied (e.g., `"strength_min_0.80_satisfied"`)
- **`missing_conditions`**: Conditions not satisfied
- **`score_components`**: Breakdown of formation_strength calculation
  - `base`: Base score from gyeokguk class
  - `relation`: Sum of relation modifiers
  - `climate`: Sum of climate modifiers
  - `yongshin`: Yongshin synergy adjustment
  - `shensha`: Shensha modifier sum

---

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| strength_policy_v2.json | 2.0 | Strength score (0.0-1.0) for gyeokguk classification |
| relation_weight_v1.0.0.json | 1.0.0 | Relation impact weights (sanhe, ganhe, chong, xing, hai) |
| yongshin_selector_policy_v1.json | yongshin_v1.0.0 | Beneficial elements for synergy calculation |
| shensha_v2.json | 2.0 | Shensha (favorable/unfavorable) for modifiers |

---

### Input Schema

**Required Fields:**
- `strength.score` (number, 0-1): Normalized strength score
- `relation_summary` (object): Relation weights (sanhe, ganhe, chong, xing, hai, etc.)
- `yongshin` (array): Beneficial elements (1+ elements)
- `climate` (object): Seasonal element and support level

**Optional Fields:**
- `ten_gods_summary` (object): Ten Gods distribution for dominant pattern detection
- `elements_distribution` (object): Five elements distribution for balance analysis
- `context` (object): Additional context (e.g., month_branch)

---

### Output Schema

**Required Fields:**
- `policy_version` (string): Policy version used (e.g., `"gyeokguk_v1.0.0"`)
- `gyeokguk_code` (string): Pattern code (e.g., `"JG-002"`)
- `gyeokguk_label` (string): Pattern label in Korean (e.g., `"종강격"`)
- `formation_strength` (number, 0-1): Pattern formation strength
- `confidence` (number, 0-1): Classification confidence
- `conditions_met` (array): Satisfied conditions
- `missing_conditions` (array): Unsatisfied conditions
- `rationale` (array): Classification rationale in Korean
- `rules_fired` (array): Applied modifiers
- `score_components` (object): Breakdown of formation_strength

---

### Test Coverage

**Total Test Cases:** 20 JSONL cases

**Coverage by Pattern:**
- 종강격 (JG-002): 2 cases
- 종약격 (JG-003): 2 cases
- 화격 (JG-004): 3 cases
- 정격 (JG-001): 2 cases
- 파격 (JG-009): 2 cases
- 인수격 (JG-005): 2 cases
- 식상격 (JG-006): 2 cases
- 관살격 (JG-007): 2 cases
- 재격 (JG-008): 2 cases

**Validation Criteria:**
- `gyeokguk_label` exact match
- `formation_strength_min` threshold validation
- `formation_strength_max` threshold validation (for 파격)
- `confidence_min` threshold validation (optional)

---

### I/O Examples

**4 comprehensive examples provided:**

1. **Example 1 (종강격)**: High strength (0.84) + sanhe (0.80) + companion dominance → formation_strength 0.93
2. **Example 2 (화격)**: ganhe_hua=true + climate support → formation_strength 0.98
3. **Example 3 (파격)**: Excessive chong (0.90) + xing (0.80) + hai (0.65) → formation_strength 0.06
4. **Example 4 (정격)**: Balanced strength (0.53) + balanced ten gods → formation_strength 0.74

---

### Usage Notes

#### Dominant Pattern Detection

**Conditions:**
- `companion_or_resource_dominant`: 비견+겁재+인성 count > 일간 외 십신 합계의 50%
- `wealth_or_official_dominant`: 재성+관살 count > 일간 외 십신 합계의 50%
- `resource_dominant`: 인성 count > 일간 외 십신 합계의 40%
- `output_dominant`: 식상 count > 일간 외 십신 합계의 40%
- `official_dominant`: 관살 count > 일간 외 십신 합계의 40%
- `wealth_dominant`: 재성 count > 일간 외 십신 합계의 40%
- `transform_active`: ganhe_hua=true OR sanhe_element ≠ ""
- `破格_pattern`: (chong ≥0.60 AND xing ≥0.50) OR (chong+xing+hai ≥1.80)

#### Core Element Assignment

Each gyeokguk class has a `core_element` representing its structural focus:

- 정격 (JG-001): 토 (earth, balance)
- 종강격 (JG-002): 목 (wood, growth)
- 종약격 (JG-003): 금 (metal, contraction)
- 화격 (JG-004): 화 (fire, transformation)
- 인수격 (JG-005): 수 (water, resource flow)
- 식상격 (JG-006): 토 (earth, output grounding)
- 관살격 (JG-007): 금 (metal, authority)
- 재격 (JG-008): 토 (earth, wealth accumulation)
- 파격 (JG-009): 수 (water, dissolution)

---

### Policy Signature

**Status:** UNSIGNED

This policy file is delivered with `policy_signature: "UNSIGNED"`. The signature will be computed and injected by **Policy Signature Auditor v1.0** using RFC-8785 JCS canonicalization + SHA-256 hashing.

**Signing Process:**
```bash
python3 policy_signature_auditor/psa_cli.py sign policy/gyeokguk_policy_v1.json
```

**Expected Signature Field:**
```json
{
  "policy_signature": "UNSIGNED"  // Will be replaced with SHA-256 hash
}
```

---

### Known Limitations

1. **Ten Gods Dependency**: Dominant pattern detection (`companion_or_resource_dominant`, etc.) requires `ten_gods_summary` input. If omitted, only strength-based and transformation-based patterns (정격, 종강격, 종약격, 화격) can be reliably classified.

2. **Shensha Integration**: Shensha modifiers are defined in policy but require integration with Shensha Catalog v2.0 for runtime application. Current implementation provides modifier weights; actual shensha detection must be provided in input or computed separately.

3. **Climate Evaluation**: Climate support requires ClimateEvaluator integration (not yet completed in analysis-service). Manual `climate` input required until integration.

4. **Threshold Sensitivity**: Some thresholds (e.g., `sanhe_ge_0p70`) may require tuning based on real-world saju data distribution. Current values are derived from traditional saju theory and expert consensus.

---

### Breaking Changes

**None.** This is the initial release (v1.0.0).

---

### Migration Path (Future v1.1)

Planned enhancements for v1.1 (2025-Q4):

1. **Auto-Detection of Dominant Patterns**: Compute `companion_or_resource_dominant` etc. from `ten_gods_summary` within classifier (remove manual condition checking)
2. **Shensha Runtime Integration**: Automatically fetch shensha list from Shensha Catalog and apply modifiers
3. **Climate Auto-Fetch**: Integrate ClimateEvaluator to auto-populate `climate` field
4. **Threshold Tuning**: Adjust relation thresholds (sanhe_ge_0p70 → sanhe_ge_0p65) based on production data
5. **Multi-Pattern Support**: Allow secondary gyeokguk classification when formation_strength gap < 0.10

---

### Contributors

- **Policy Design**: Gyeokguk Theory Research Team
- **Algorithm**: Deterministic Scoring Framework Squad
- **Test Coverage**: QA Automation Team
- **Documentation**: Tech Writers

---

### References

**Traditional Saju Theory:**
- 적천수 (滴天髓): 格局 분류 이론
- 연해자평 (淵海子平): 십신·격국 체계
- 궁통보감 (窮通寶鑑): 조후·계절 관계

**Modern Extensions:**
- Strength Evaluator v2.0: Deterministic strength scoring
- Relation Weight Evaluator v1.0: Multi-dimensional relation impact
- Yongshin Selector v1.0: Algorithmic beneficial element selection

---

## Version 0.9.0 (2025-10-08) - DRAFT

Pre-release draft for internal review. Not deployed.

---

**End of Changelog**
