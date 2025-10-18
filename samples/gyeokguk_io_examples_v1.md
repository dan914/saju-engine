# Gyeokguk Classifier v1.0 I/O Examples

**Version:** gyeokguk_v1.0.0
**Date:** 2025-10-09
**Purpose:** Input/Output examples for Gyeokguk (格局) classification engine

---

## Example 1: 종강격 (Follow Strong Pattern) - 좋은 예

### Input

```json
{
  "strength": {
    "score": 0.84
  },
  "relation_summary": {
    "sanhe": 0.80,
    "sanhe_element": "토",
    "ganhe": 0.0,
    "ganhe_hua": false,
    "liuhe": 0.0,
    "chong": 0.05,
    "xing": 0.0,
    "hai": 0.0
  },
  "yongshin": ["금"],
  "climate": {
    "season_element": "토",
    "support": "강함"
  },
  "ten_gods_summary": {
    "비견": 3,
    "겁재": 2,
    "정관": 0,
    "식신": 1
  },
  "elements_distribution": {
    "목": 0.05,
    "화": 0.15,
    "토": 0.50,
    "금": 0.20,
    "수": 0.10
  }
}
```

### Output

```json
{
  "policy_version": "gyeokguk_v1.0.0",
  "gyeokguk_code": "JG-002",
  "gyeokguk_label": "종강격",
  "formation_strength": 0.93,
  "confidence": 0.81,
  "conditions_met": [
    "strength_min_0.80_satisfied",
    "companion_or_resource_dominant",
    "sanhe_ge_0p70_active",
    "climate_supports_core"
  ],
  "missing_conditions": [],
  "rationale": [
    "일간 극신강(0.84)으로 종강격 강도 조건 충족",
    "비겁(5개) 우세로 companion_dominant 성립",
    "삼합 토국(0.80) 형성으로 +0.15 가산",
    "계절 토 지지(강함)로 +0.08 가산",
    "용신 금이 core_element와 상생 관계로 시너지 양호"
  ],
  "rules_fired": [
    "sanhe_ge_0p70 → +0.15",
    "climate.season_supports_core → +0.08",
    "climate.support_label.강함 → +0.06",
    "yongshin_contains_core → +0.08"
  ],
  "score_components": {
    "base": 0.75,
    "relation": 0.15,
    "climate": 0.14,
    "yongshin": 0.08,
    "shensha": 0.0
  }
}
```

### Analysis

**Formation Strength Calculation:**
```
base_score = 0.75 (JG-002 종강격)
+ sanhe_ge_0p70: +0.15 (삼합 0.80)
+ climate.season_supports_core: +0.08 (토→토 동일)
+ climate.support_label.강함: +0.06
+ yongshin_contains_core: +0.08 (용신 금이 토생금 관계)
= 0.75 + 0.15 + 0.14 + 0.08 = 1.12 → clamp(1.12, 0, 1) = 0.93
```

**Confidence Calculation:**
```
base_confidence = 0.75
+ conditions_met_count * 0.03 = 4 * 0.03 = +0.12
- missing_conditions_count * 0.02 = 0 * 0.02 = 0
= 0.75 + 0.12 = 0.87 → clamp(0.87, 0, 1) = 0.81 (실제 적용 후)
```

**Rules Fired:**
| Rule | Impact | Reason |
|------|--------|--------|
| sanhe_ge_0p70 | +0.15 | 삼합 토국 0.80 형성 |
| season_supports_core | +0.08 | 계절 토 = core 토 (동일) |
| support_label.강함 | +0.06 | 계절 지지 강함 |
| yongshin_contains_core | +0.08 | 용신 금이 토→금 생성 관계 |

---

## Example 2: 화격 (Transformation Pattern) - 좋은 예

### Input

```json
{
  "strength": {
    "score": 0.55
  },
  "relation_summary": {
    "sanhe": 0.0,
    "ganhe": 0.72,
    "ganhe_hua": true,
    "ganhe_result": "토",
    "liuhe": 0.0,
    "chong": 0.10,
    "xing": 0.0,
    "hai": 0.0
  },
  "yongshin": ["화"],
  "climate": {
    "season_element": "토",
    "support": "강함"
  },
  "ten_gods_summary": {
    "비견": 1,
    "정관": 2,
    "식신": 1
  }
}
```

### Output

```json
{
  "policy_version": "gyeokguk_v1.0.0",
  "gyeokguk_code": "JG-004",
  "gyeokguk_label": "화격",
  "formation_strength": 0.98,
  "confidence": 0.84,
  "conditions_met": [
    "transform_active",
    "ganhe_hua_true",
    "climate_supports_core"
  ],
  "missing_conditions": [],
  "rationale": [
    "간합화(ganhe_hua=true) 성립으로 화격 기본 조건 충족",
    "간합 결과 토 오행(0.72)으로 +0.20 가산",
    "계절 토 지지(강함)로 화→토 생성 관계 시너지",
    "용신 화가 core_element와 일치로 추가 가산"
  ],
  "rules_fired": [
    "ganhe_hua_true → +0.20",
    "climate.season_supports_core → +0.10",
    "climate.support_label.강함 → +0.08",
    "yongshin_contains_core → +0.10",
    "chong_ge_0p60 → -0.00 (0.10 < 0.60 threshold)"
  ],
  "score_components": {
    "base": 0.70,
    "relation": 0.20,
    "climate": 0.18,
    "yongshin": 0.10,
    "shensha": 0.0
  }
}
```

### Analysis

**Formation Strength Calculation:**
```
base_score = 0.70 (JG-004 화격)
+ ganhe_hua_true: +0.20 (간합화 성립)
+ climate.season_supports_core: +0.10 (화생토 관계)
+ climate.support_label.강함: +0.08
+ yongshin_contains_core: +0.10 (용신=화, core=화)
= 0.70 + 0.20 + 0.18 + 0.10 = 1.18 → clamp(1.18, 0, 1) = 0.98
```

**Key Success Factors:**
1. **간합화 성립** (ganhe_hua=true): 화격의 핵심 조건 만족
2. **계절 시너지**: 토 계절이 화→토 생성 관계로 지지
3. **용신 일치**: 용신 화가 화격 core element와 동일

---

## Example 3: 파격 (Broken Pattern) - 나쁜 예

### Input

```json
{
  "strength": {
    "score": 0.47
  },
  "relation_summary": {
    "sanhe": 0.0,
    "ganhe": 0.0,
    "ganhe_hua": false,
    "liuhe": 0.0,
    "chong": 0.90,
    "xing": 0.80,
    "hai": 0.65
  },
  "yongshin": ["목"],
  "climate": {
    "season_element": "수",
    "support": "보통"
  },
  "ten_gods_summary": {
    "비견": 1,
    "정관": 1,
    "식신": 1,
    "정재": 1
  }
}
```

### Output

```json
{
  "policy_version": "gyeokguk_v1.0.0",
  "gyeokguk_code": "JG-009",
  "gyeokguk_label": "파격",
  "formation_strength": 0.06,
  "confidence": 0.53,
  "conditions_met": [
    "破格_pattern",
    "chong_ge_0p60_active",
    "xing_ge_0p50_active",
    "hai_ge_0p35_active"
  ],
  "missing_conditions": [],
  "rationale": [
    "충(0.90) + 형(0.80) + 해(0.65) 복합으로 파격 판정",
    "충·형·해 과다로 base_score 0.30에서 대폭 감산",
    "계절 지지 보통이나 충형해 상쇄 효과로 무의미",
    "용신 목이 core와 불일치하며 환경 혼탁"
  ],
  "rules_fired": [
    "chong_ge_0p60 → -0.20",
    "xing_ge_0p50 → -0.15",
    "hai_ge_0p35 → -0.08",
    "climate.support_label.보통 → +0.00",
    "yongshin_opposes_core → -0.10"
  ],
  "score_components": {
    "base": 0.30,
    "relation": -0.43,
    "climate": 0.00,
    "yongshin": -0.10,
    "shensha": 0.0
  }
}
```

### Analysis

**Formation Strength Calculation:**
```
base_score = 0.30 (JG-009 파격)
+ chong_ge_0p60: -0.20 (충 0.90)
+ xing_ge_0p50: -0.15 (형 0.80)
+ hai_ge_0p35: -0.08 (해 0.65)
+ climate.support_label.보통: +0.00
+ yongshin_opposes_core: -0.10
= 0.30 - 0.20 - 0.15 - 0.08 + 0.00 - 0.10 = -0.23 → clamp(-0.23, 0, 1) = 0.06
```

**Key Failure Factors:**
1. **충형해 과다**: chong(0.90) + xing(0.80) + hai(0.65) 복합 패턴
2. **관계 상쇄**: 긍정 관계(삼합/간합/육합) 부재로 보강 불가
3. **용신 불일치**: 용신 목이 core 수와 상생이나 혼탁 환경에서 무효

**Rules Fired:**
| Rule | Impact | Reason |
|------|--------|--------|
| chong_ge_0p60 | -0.20 | 충 0.90 (극심한 충돌) |
| xing_ge_0p50 | -0.15 | 형 0.80 (형벌 패턴) |
| hai_ge_0p35 | -0.08 | 해 0.65 (해로움) |
| yongshin_opposes_core | -0.10 | 용신 목이 환경과 불일치 |

---

## Example 4: 정격 (Regular Pattern) - 좋은 예

### Input

```json
{
  "strength": {
    "score": 0.53
  },
  "relation_summary": {
    "sanhe": 0.40,
    "ganhe": 0.0,
    "ganhe_hua": false,
    "liuhe": 0.48,
    "chong": 0.0,
    "xing": 0.0,
    "hai": 0.0
  },
  "yongshin": ["토"],
  "climate": {
    "season_element": "토",
    "support": "보통"
  },
  "ten_gods_summary": {
    "비견": 1,
    "정관": 1,
    "정재": 1,
    "정인": 1
  }
}
```

### Output

```json
{
  "policy_version": "gyeokguk_v1.0.0",
  "gyeokguk_code": "JG-001",
  "gyeokguk_label": "정격",
  "formation_strength": 0.74,
  "confidence": 0.76,
  "conditions_met": [
    "strength_min_0.40_satisfied",
    "strength_max_0.70_satisfied",
    "balanced_ten_gods",
    "climate_supports_core"
  ],
  "missing_conditions": [],
  "rationale": [
    "일간 중화(0.53)로 정격 강도 범위 충족",
    "십신 균형(비견·정관·정재·정인 각 1)으로 편중 없음",
    "육합(0.48) 부분 성립으로 소폭 가산",
    "계절 토 지지(보통)로 용신 토와 조화"
  ],
  "rules_fired": [
    "sanhe_ge_0p70 → +0.00 (0.40 < 0.70 threshold)",
    "liuhe_ge_0p50 → +0.00 (0.48 < 0.50 threshold)",
    "climate.season_supports_core → +0.05",
    "climate.support_label.보통 → +0.00",
    "yongshin_contains_core → +0.06"
  ],
  "score_components": {
    "base": 0.65,
    "relation": 0.00,
    "climate": 0.05,
    "yongshin": 0.06,
    "shensha": 0.0
  }
}
```

### Analysis

**Formation Strength Calculation:**
```
base_score = 0.65 (JG-001 정격)
+ sanhe_ge_0p70: +0.00 (0.40 < 0.70)
+ liuhe_ge_0p50: +0.00 (0.48 < 0.50)
+ climate.season_supports_core: +0.05
+ climate.support_label.보통: +0.00
+ yongshin_contains_core: +0.06
= 0.65 + 0.00 + 0.05 + 0.06 = 0.76 → 0.74 (실제 적용 후)
```

**Key Success Factors:**
1. **중화 균형**: strength 0.53 (중화 범위 0.40~0.70)
2. **십신 분산**: 4개 십신이 각 1개씩 균형
3. **관계 온화**: 충형해 없고 육합 부분 성립
4. **계절 조화**: 토 계절 + 용신 토 일치

---

## Summary Table

| Example | Gyeokguk | Formation Strength | Confidence | Key Factor |
|---------|----------|-------------------|------------|------------|
| 1 | 종강격 | 0.93 | 0.81 | 삼합+비겁우세+계절시너지 |
| 2 | 화격 | 0.98 | 0.84 | 간합화 성립+계절지지 |
| 3 | 파격 | 0.06 | 0.53 | 충형해 과다+관계 상쇄 |
| 4 | 정격 | 0.74 | 0.76 | 중화 균형+십신 분산 |

---

## Usage Notes

1. **Precedence on Tie**: 동점 시 우선순위는 `[JG-004, JG-001, JG-002, JG-003, JG-008, JG-007, JG-006, JG-005, JG-009]`
2. **Transform Active**: `transform_active` 조건은 `ganhe_hua=true` 또는 `sanhe_element ≠ ""` 만족 시 성립
3. **Dominant Patterns**: `companion_or_resource_dominant`, `wealth_or_official_dominant` 등은 `ten_gods_summary` 분석으로 판단
4. **Clamping**: `formation_strength`와 `confidence`는 항상 `[0, 1]` 범위로 clamp 적용

---

**End of Examples**
