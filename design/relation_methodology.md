# Relation Transformer Methodology v1.1

## Overview

The Relation Transformer analyzes interactions between earthly branches (地支) in a Four Pillars chart, identifying 12 types of relationships that affect energy flow and transformation. This methodology implements **energy conservation**, **mutual exclusion**, and **conflict attenuation** principles.

## 1. The 12 Relationship Types (十二地支關係)

### 1.1 Auspicious Relationships (吉)

#### 六合 (Liùhé / Six Harmonies)
- **Nature**: Binary pairing, attraction and cooperation
- **Rules**: 6 pairs (子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未)
- **Score Range**: +10 to +15
- **Element Production**: None (attraction only)
- **Conservation**: 2 consume → 2 produce (no net transformation)

#### 三合 (Sānhé / Triple Harmony)
- **Nature**: Triadic elemental fusion
- **Rules**: 4 bureaus producing specific elements
  - 申子辰 → 水局
  - 亥卯未 → 木局
  - 寅午戌 → 火局
  - 巳酉丑 → 金局
- **Score Range**: +15 to +20
- **Conservation**: 3 consume → 3 produce (elemental transformation)
- **Promotion**: Suppresses 半合 and 拱合 when complete

#### 半合 (Bànhé / Half Harmony)
- **Nature**: Partial triadic fusion (2 of 3 branches)
- **Rules**: Subset of 三合 patterns
- **Score Range**: +8 to +12
- **Conservation**: 2 consume → 2 produce
- **Suppression**: Fully suppressed (weight=0.0) when 三合 is present

#### 方合 (Fānghé / Directional Harmony)
- **Nature**: Seasonal/directional alignment (4 branches)
- **Rules**: 4 directions
  - 寅卯辰 (東方木局)
  - 巳午未 (南方火局)
  - 申酉戌 (西方金局)
  - 亥子丑 (北方水局)
- **Score Range**: +12 to +18
- **Conservation**: 3 consume → 3 produce

#### 拱合 (Gǒnghé / Arch Harmony)
- **Nature**: Implied missing branch creates triadic energy
- **Rules**: 2 branches imply the 3rd in 三合 pattern
- **Score Range**: +6 to +10
- **Conservation**: 2 consume → 2 produce (implied 3rd branch)
- **Suppression**: Fully suppressed (weight=0.0) when 三合 is present

### 1.2 Inauspicious Relationships (凶)

#### 沖 (Chōng / Clash)
- **Nature**: Direct opposition, energy conflict
- **Rules**: 6 pairs (子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥)
- **Score Range**: -15 to -20
- **Conservation**: 2 consume → 2 produce (turbulent transformation)
- **Attenuation**: Weakens 三合 and 六合 by 50% (factor=0.5)

#### 刑 (Xíng / Punishment)
- **Nature**: Indirect conflict, karmic punishment
- **Types**:
  - **Self-punishment** (自刑): 辰辰, 午午, 酉酉, 亥亥
  - **Ungrateful punishment** (無恩之刑): 寅巳申 (3-way cycle)
  - **Punishment of power** (恃勢之刑): 丑戌未 (3-way cycle), 子卯 (binary)
- **Score Range**: -10 to -15
- **Conservation**: Variable (2 or 3 consume → produce)
- **Stacking**: per_set mode with cap=1 (one punishment per complete set)

#### 破 (Pò / Destruction)
- **Nature**: Subtle undermining, gradual erosion
- **Rules**: 6 pairs (子酉, 午卯, 辰丑, 未戌, 寅亥, 巳申)
- **Score Range**: -8 to -12
- **Conservation**: 2 consume → 2 produce

#### 害 (Hài / Harm)
- **Nature**: Indirect conflict through 六合 disruption
- **Rules**: 6 pairs (子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌)
- **Score Range**: -10 to -14
- **Conservation**: 2 consume → 2 produce

## 2. Energy Conservation System

### 2.1 Hidden Stems Budget (藏干預算)

Each earthly branch contains hidden stems (藏干) with weighted element distribution:

```
子: 水=1.0
丑: 土=0.6, 金=0.2, 水=0.2
寅: 木=0.6, 火=0.2, 土=0.2
卯: 木=1.0
辰: 土=0.6, 木=0.2, 水=0.2
巳: 火=0.6, 土=0.2, 金=0.2
午: 火=0.7, 土=0.3
未: 土=0.6, 火=0.2, 木=0.2
申: 金=0.6, 水=0.2, 土=0.2
酉: 金=1.0
戌: 土=0.6, 金=0.2, 火=0.2
亥: 水=0.7, 木=0.3
```

### 2.2 Fusion Rules

Each relationship type defines energy consumption and production:

| Relationship | Consume Units | Produce Units | Implied Missing | Element Override |
|--------------|---------------|---------------|-----------------|------------------|
| 三合 | 3.0 | 3.0 | No | Yes (bureau element) |
| 半合 | 2.0 | 2.0 | No | Yes (bureau element) |
| 方合 | 3.0 | 3.0 | No | Yes (directional element) |
| 拱合 | 2.0 | 2.0 | Yes (3rd branch) | Yes (bureau element) |
| 六合 | 2.0 | 2.0 | No | No |
| 沖 | 2.0 | 2.0 | No | No |
| 刑 | 2.0-3.0 | 2.0-3.0 | No | No |
| 破 | 2.0 | 2.0 | No | No |
| 害 | 2.0 | 2.0 | No | No |

### 2.3 Conservation Validation

For each detected relationship:

1. **Calculate Available Budget**: Sum hidden stems weights for participating branches
2. **Check Consumption**: `consume_units ≤ available_budget`
3. **Record Production**: Element and quantity produced
4. **Update Conservation Flag**: `conservation_ok = true/false`

Example (申子辰 三合水局):
```
Available:
  申: 金=0.6, 水=0.2, 土=0.2
  子: 水=1.0
  辰: 土=0.6, 木=0.2, 水=0.2
  Total: 水=1.4, 金=0.6, 土=0.8, 木=0.2

Consume: 3.0 units
Produce: 3.0 units 水
Conservation: ✓ (1.4 water available, enough to support transformation)
```

## 3. Mutual Exclusion and Promotion

### 3.1 Exclusion Groups

**Group 1: {三合, 半合, 拱合}**
- **Promotion**: 三合 (highest priority)
- **Suppression**: When 三合 is detected, 半合 and 拱合 are suppressed with `lower_rank_weight = 0.0`
- **Rationale**: Complete triadic fusion supersedes partial formations

Example:
```
Branches: 申, 子, 辰

Detected:
  - 三合 (申子辰)
  - 半合 (申子)
  - 半合 (子辰)

Result:
  - 三合: Active (weight=1.0)
  - 半合 (申子): Suppressed (weight=0.0)
  - 半合 (子辰): Suppressed (weight=0.0)
```

### 3.2 Promotion Logic

1. **Detect all relationships** in the group
2. **Identify highest-priority** relationship (promotion target)
3. **Apply suppression weight** to lower-priority relationships
4. **Record evidence** of suppression in trace

## 4. Conflict Attenuation

### 4.1 Attenuation Rules

**Rule 1: 沖 weakens 三合 and 六合**
- **Condition**: `沖 present`
- **Attenuate**: `[三合, 六合]`
- **Factor**: `0.5` (50% strength reduction)
- **Rationale**: Direct opposition disrupts harmony patterns

**Rule 2: 刑 weakens 三合**
- **Condition**: `刑 present`
- **Attenuate**: `[三合]`
- **Factor**: `0.7` (30% strength reduction)
- **Rationale**: Punishment disrupts triadic fusion

### 4.2 Attenuation Application

1. **Detect conflict** (沖 or 刑)
2. **Identify affected relationships** (三合, 六合)
3. **Apply factor**: `attenuated_score = original_score × factor`
4. **Record attenuation** in evidence

Example:
```
Branches: 申, 子, 辰, 午

Detected:
  - 三合 (申子辰): score_hint = +18
  - 沖 (子午): score_hint = -18

Attenuation:
  - 三合 attenuated: +18 × 0.5 = +9
  - Final score: +9 (三合) + (-18) (沖) = -9
```

## 5. Confidence Calculation

### 5.1 Deterministic Formula

```
confidence = clamp01(
  round(
    w_norm × (score_normalized / 100) +
    w_conservation × (conservation_ok ? 1 : 0) +
    w_priority × (priority_avg / 100) +
    w_conflict × conflict_ratio,
    2
  )
)
```

### 5.2 Weights

| Component | Weight | Description |
|-----------|--------|-------------|
| w_norm | 0.40 | Normalized score contribution |
| w_conservation | 0.30 | Conservation check (0 or 1) |
| w_priority | 0.20 | Average priority of relationships |
| w_conflict | 0.10 | Ratio of conflicts to harmonies |

### 5.3 Normalization

- **Score Range**: -20 to +20
  - `score_normalized = (score - (-20)) / (20 - (-20)) × 100`
- **Priority Range**: 1 to 100
  - `priority_avg = sum(priorities) / count`

### 5.4 Conflict Ratio

```
conflict_ratio = -1.0 × (inauspicious_count / total_count)
```

### 5.5 Example Calculation

```
Detected Relationships:
  - 三合 (申子辰): score=+18, priority=95, conservation=✓
  - 沖 (子午): score=-18, priority=90, conservation=✓

Step 1: Score normalization
  total_score = +18 + (-18) = 0
  score_normalized = (0 - (-20)) / 40 × 100 = 50

Step 2: Conservation
  conservation_ok = true → 1

Step 3: Priority
  priority_avg = (95 + 90) / 2 = 92.5

Step 4: Conflict ratio
  conflict_ratio = -1.0 × (1 / 2) = -0.5

Step 5: Calculate confidence
  conf = 0.40×(50/100) + 0.30×1 + 0.20×(92.5/100) + 0.10×(-0.5)
       = 0.20 + 0.30 + 0.185 - 0.05
       = 0.635
       ≈ 0.64 (rounded to 2 decimals)
```

## 6. Evidence Recording

### 6.1 Evidence Template

```json
{
  "relation_type": "三合",
  "branches_involved": ["申", "子", "辰"],
  "element_produced": "水",
  "conservation_detail": {
    "budget_available": 3.0,
    "consume_units": 3.0,
    "produce_units": 3.0,
    "conservation_ok": true
  },
  "attenuation_applied": {
    "factor": 0.5,
    "reason": "沖 present"
  },
  "confidence": 0.64
}
```

### 6.2 Trace Array

Each evidence object includes:
- **relation_type**: Key of the relationship (e.g., "三合")
- **branches_involved**: Array of participating branches
- **element_produced**: Resulting element (if applicable)
- **conservation_detail**: Budget calculation breakdown
- **attenuation_applied**: Attenuation factor and reason (if applicable)
- **confidence**: Calculated confidence score

## 7. Implementation Guarantees

### 7.1 Determinism

1. **Canonical JSON**: RFC8785 canonicalization for policy JSON
2. **SHA-256 Hashing**: Policy signature for version control
3. **Sorted Arrays**: All arrays sorted for consistent ordering
4. **Floating-point Precision**: Rounded to 2 decimals

### 7.2 Validation (CI Checks)

1. **CI-REL-01**: All relationships have positive priority
2. **CI-REL-02**: Score ranges are valid (min ≤ max)
3. **CI-REL-03**: Hidden stems weights sum to 1.0 for each branch
4. **CI-REL-04**: All 六合 pairs are symmetric
5. **CI-REL-05**: All 三合 bureaus are complete (3 branches each)
6. **CI-REL-06**: All 沖 pairs are opposites (6 pairs)
7. **CI-REL-07**: Confidence weights sum to 1.0
8. **CI-REL-08**: Fusion rules define consume and produce units
9. **CI-REL-09**: Mutual exclusion groups have valid promotion targets
10. **CI-REL-10**: Attenuation factors are in range [0, 1]
11. **CI-REL-11**: All relationship types have non-empty rules arrays
12. **CI-REL-12**: Branch patterns contain only valid earthly branches

## 8. Limitations and Future Work

### 8.1 Current Limitations

1. **Context Independence**: Relationships analyzed in isolation without day master or ten gods context
2. **Score Range Subjectivity**: ±20 range is conventional but not empirically derived
3. **Static Weights**: Confidence weights are fixed and may need tuning for specific use cases
4. **Simplified Conservation**: Hidden stems budget is approximate, not precise traditional calculations

### 8.2 Future Enhancements

1. **Contextual Analysis**: Integrate day master strength and ten gods relevance
2. **Dynamic Weighting**: LLM-assisted confidence tuning based on practitioner feedback
3. **Multi-layer Relationships**: Support nested relationships (e.g., 三合 within 方合)
4. **Temporal Analysis**: Extend to luck pillars and year transits

## 9. References

- **Classic Text**: 《淵海子平》 (Yuānhǎi Zǐpíng)
- **Modern Interpretation**: 《子平真詮》 (Zǐpíng Zhēnquán)
- **Conservation Theory**: Original research based on 藏干 traditional weights
- **JSON Schema**: Draft 2020-12 specification
- **Canonicalization**: RFC8785 (JSON Canonicalization Scheme)

---

**Document Version**: 1.1
**Last Updated**: 2025-10-05
**Author**: Saju Engine Development Team
**License**: Proprietary
