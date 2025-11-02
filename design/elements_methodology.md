# Elements Distribution — Methodology (五行分析)

**Version**: 1.1
**Date**: 2025-10-04
**Status**: Policy-Driven Reference

---

## Purpose

Quantify the five-element composition (木/火/土/金/水) of a chart using policy-driven, reproducible rules.

**Outputs**:
- Per-element percentage (0-100%)
- Qualitative labels in 3 languages:
  - **Chinese**: 過旺/發達/平衡/不足
  - **Korean**: 과다/발달/적정/부족
  - **English**: Excessive/Developed/Balanced/Deficient

---

## Disclaimer

**본 정책의 임계값 및 가중치는 고전 문헌이 아닌 현대 사주 실무에 기반한 경험적 기준입니다.**

- 백분율은 오행의 **양적 분포**를 보여주며, 상생상극·조후·격국 등 **질적 해석**은 별도 규칙(다른 정책/엔진)에 의해 처리됩니다.
- 임계값과 가중치는 실무 경험을 반영한 것으로, 고전 원전에 명시된 수치가 아닙니다.

---

## Dependencies (ZangGan Policy)

이 정책은 **장간(藏干) 정책**에 의존합니다:

```json
"dependencies": {
  "zanggan_policy": {
    "name": "zanggan_table",
    "version": "2.6",
    "signature": "7457895fc970"
  }
}
```

### Signature Verification

런타임 로더는 실제 로딩된 장간 정책의 서명과 일치하지 않으면 실패해야 합니다:

```python
from app.core.policy_guards import validate_dependencies, DependencySignature

# Load zanggan policy and calculate signature
zanggan_sig = DependencySignature(
    name="zanggan_table",
    version="2.6",
    signature=calculate_signature(zanggan_data)
)

# Validate elements policy declares correct dependency
validate_dependencies(elements_policy, {"zanggan_table": zanggan_sig})
```

---

## Modes — Branch-as-Container

두 가지 집계 모드를 지원합니다:

### 1. `hidden_only` (숨은 간지만)

지지의 오행은 장간 합성으로만 집계 (지지 자체 가중치 0).

**Formula**:
```
score(e) = Σ stems[w_stem × 1[elem=e]]
         + Σ hidden[w_primary × 1[primary=e] + w_secondary × 1[secondary=e] + w_tertiary × 1[tertiary=e]]
```

**Example**:
- 子支: 壬(primary) 癸(secondary) → 水 元素만 집계
- 지지 자체의 水 속성은 무시

### 2. `branch_plus_hidden` (지지 + 장간) **[기본값]**

지지를 컨테이너 요소로 1.0 가중 + 장간은 1.0/0.5/0.3.

**Formula**:
```
score(e) = Σ stems[w_stem × 1[elem=e]]
         + Σ branches[w_branch × 1[elem=e]]
         + Σ hidden[w_primary × 1[primary=e] + w_secondary × 1[secondary=e] + w_tertiary × 1[tertiary=e]]
```

**Example**:
- 子支: 水(branch) + 壬(primary) + 癸(secondary)
- 水 元素가 이중 집계됨 (container + hidden)

### ⚠️ 이중 집계 주의사항

`branch_plus_hidden` 모드는 일부 환경에서 **이중 집계** 위험이 있으므로:

- Evidence에 모드·가중치를 명시적으로 기록
- 기존 기대값(E1~E5)과의 호환성을 위해 기본값으로 설정
- 향후 `hidden_only` 모드로 전환 시 기대값 스냅샷 갱신 필요

---

## Counting & Weights

### Stem → Element Mapping

| Stem | Element |
|------|---------|
| 甲乙 | 木 (Wood) |
| 丙丁 | 火 (Fire) |
| 戊己 | 土 (Earth) |
| 庚辛 | 金 (Metal) |
| 壬癸 | 水 (Water) |

### Branch → Element Mapping

| Branch | Element |
|--------|---------|
| 子 | 水 (Water) |
| 丑 | 土 (Earth) |
| 寅 | 木 (Wood) |
| 卯 | 木 (Wood) |
| 辰 | 土 (Earth) |
| 巳 | 火 (Fire) |
| 午 | 火 (Fire) |
| 未 | 土 (Earth) |
| 申 | 金 (Metal) |
| 酉 | 金 (Metal) |
| 戌 | 土 (Earth) |
| 亥 | 水 (Water) |

### Weight Configuration

```json
"counting_method": {
  "mode": "branch_plus_hidden",
  "stems": { "weight": 1.0 },
  "branches": { "weight": 1.0 },
  "hidden_stems": {
    "primary": { "weight": 1.0 },
    "secondary": { "weight": 0.5 },
    "tertiary": { "weight": 0.3 }
  }
}
```

---

## Formula

For each element `e ∈ {木, 火, 土, 金, 水}`:

### Score Calculation

```
score(e) = Σ_stems [w_s × 1[elem=e]]
         + Σ_branches [w_b × 1[elem=e]]
         + Σ_hidden_by_pillar [
             w_h,1 × 1[primary=e]
           + w_h,2 × 1[secondary=e]
           + w_h,3 × 1[tertiary=e]
           ]
```

### Normalization

```
pct(e) = (score(e) / Σ_x score(x)) × 100
```

### Total Sum Constraint

```
Σ_e pct(e) = 100.00 (±0.01 tolerance)
```

---

## Rounding & Labeling Rule

### 1. 라벨 판정 (Labeling)

라벨 판정은 **반올림 전**에 수행합니다:

```python
def normalize_and_label(percentages: dict, thresholds: dict) -> dict:
    labels = {}
    for element, pct in percentages.items():
        # Use RAW percentage (before rounding)
        if pct >= thresholds["excessive"]:
            labels[element] = "excessive"
        elif pct >= thresholds["developed"]:
            labels[element] = "developed"
        elif pct >= thresholds["appropriate"]:
            labels[element] = "appropriate"
        else:
            labels[element] = "deficient"
    return labels
```

**Example**:
- Raw percentage: 24.995%
- After rounding: 25.00%
- **Label**: "appropriate" (because 24.995 < 25.0 threshold)

### 2. 반올림 (Rounding)

표시는 `round(decimals)` 로 반올림:

```python
decimals = policy["counting_method"]["rounding"]["decimals"]  # 2
rounded_pct = round(raw_pct, decimals)
```

### 3. 합계 조정 (Sum Adjustment)

반올림 후 합계가 100.00%가 아니면, **마지막 항목**에 오차를 흡수:

```python
total = sum(rounded_percentages.values())
if abs(total - 100.0) > 0.01:
    # Adjust last element
    last_element = list(rounded_percentages.keys())[-1]
    rounded_percentages[last_element] += (100.0 - total)
```

---

## Thresholds → Labels

### Default Thresholds (%)

```json
"thresholds": {
  "excessive": 35.0,
  "developed": 25.0,
  "appropriate": 15.0,
  "deficient": 0.0
}
```

### Constraints

런타임 검증:
```
deficient < appropriate < developed < excessive
```

각 값은 `[0, 100]` 범위 내.

### Label Assignment

| Percentage Range | Label (zh) | Label (ko) | Label (en) |
|-----------------|-----------|-----------|-----------|
| ≥ 35.0 | 過旺 | 과다 | Excessive |
| ≥ 25.0 | 發達 | 발달 | Developed |
| ≥ 15.0 | 平衡 | 적정 | Balanced |
| < 15.0 | 不足 | 부족 | Deficient |

---

## Relation Transform (Future)

```json
"relation_transform": {
  "apply": false,
  "note": "Hook for future 三合/半合/三會/冲/刑/破/害; must obey element-conservation and no-double-deduction invariants."
}
```

### When Enabled (`apply: true`)

미래 통합 시 반영할 관계 변환:
- **三合** (삼합): 三合局 형성 시 원소 변환
- **半合** (반합): 반합 관계
- **三會** (삼회): 지지 삼회방
- **冲/刑/破/害**: 충/형/파/해 관계

### Invariants (Property Tests Required)

1. **Element Conservation**: 총량 보존
2. **No Double Deduction**: 중복 차감 금지
3. **Priority Rules**: 우선순위 명시

별도 정책/테스트에서 다룸.

---

## Evidence Recording

Evidence 로그에 포함할 필드:

```json
{
  "policy_version": "1.1",
  "mode": "branch_plus_hidden",
  "weights": {
    "stems": 1.0,
    "branches": 1.0,
    "hidden_primary": 1.0,
    "hidden_secondary": 0.5,
    "hidden_tertiary": 0.3
  },
  "thresholds": {
    "excessive": 35.0,
    "developed": 25.0,
    "appropriate": 15.0,
    "deficient": 0.0
  },
  "raw_counts": {
    "木": {"stems": 2, "branches": 1, "hidden": [1, 0.5, 0]},
    "...": "..."
  },
  "raw_percentages": {
    "木": 24.995,
    "火": 18.333,
    "土": 30.000,
    "金": 12.500,
    "水": 14.172
  },
  "labels": {
    "木": {"zh": "發達", "ko": "발달", "en": "Developed"},
    "...": "..."
  },
  "rounded_percentages": {
    "木": 25.00,
    "火": 18.33,
    "土": 30.00,
    "金": 12.50,
    "水": 14.17
  }
}
```

---

## Versioning

### Policy File Fields

```json
{
  "version": "1.1",
  "generated_on": "2025-10-04T00:00:00+09:00",
  "source_refs": [
    "三命通會 (Sanming Tonghui)",
    "子平真詮 (Ziping Zhenquan)",
    "Modern Bazi/Saju practice notes"
  ],
  "dependencies": {
    "zanggan_policy": {
      "name": "zanggan_table",
      "version": "2.6",
      "signature": "7457895fc970"
    }
  }
}
```

### Release Synchronization

- `version`: 릴리스 태그와 동기화 (e.g., v1.1)
- `generated_on`: ISO-8601 timestamp
- `dependencies.signature`: 의존 정책의 콘텐츠 해시

---

## Implementation Checklist

- [ ] Load elements policy with schema validation
- [ ] Load zanggan policy and calculate signature
- [ ] Validate dependency signatures match
- [ ] Validate threshold ordering constraints
- [ ] Calculate element scores using specified mode and weights
- [ ] Normalize to percentages (sum = 100%)
- [ ] Assign labels BEFORE rounding
- [ ] Round percentages to specified decimals
- [ ] Adjust sum to exactly 100.00% if needed
- [ ] Record full evidence (mode, weights, raw counts, labels, rounded values)

---

**End of Methodology Document**
