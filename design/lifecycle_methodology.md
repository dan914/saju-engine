# Lifecycle Stages Methodology (十二運星)

**Version**: 1.1
**Date**: 2025-10-05
**Status**: Canonical Reference

---

## 1. Overview

The 12 Lifecycle Stages (十二運星, 십이운성) represent the energy state of a Day Stem (日干) as it relates to each Earthly Branch (地支) in the Four Pillars.

**12 Stages**:
1. 長生 (장생, Birth) - Initial vitality
2. 沐浴 (목욕, Bath) - Cleansing, vulnerability
3. 冠帶 (관대, Crown) - Coming of age
4. 臨官 (임관, Office) - Prime productivity
5. 帝旺 (제왕, Peak) - Maximum strength
6. 衰 (쇠, Decline) - Beginning weakening
7. 病 (병, Sickness) - Significant weakness
8. 死 (사, Death) - Depleted state
9. 墓 (묘, Tomb) - Storage, dormancy
10. 絕 (절, Extinction) - Complete absence
11. 胎 (태, Embryo) - Conception
12. 養 (양, Nurture) - Gestation

---

## 2. Derivation Rules

### 2.1 Yin/Yang Classification

Heavenly Stems are classified by polarity:

**Yang Stems (陽干)**: 甲, 丙, 戊, 庚, 壬
**Yin Stems (陰干)**: 乙, 丁, 己, 辛, 癸

### 2.2 Starting Points (長生 Position)

Each stem has a designated 長生 (Birth) branch:

| Stem | 長生 Branch | Element Relationship |
|------|------------|---------------------|
| 甲 | 亥 | Wood born in Water |
| 乙 | 午 | Wood thrives in Fire season |
| 丙 | 寅 | Fire born in Wood |
| 丁 | 酉 | Fire tempered by Metal |
| 戊 | 寅 | Earth supported by Wood roots |
| 己 | 酉 | Earth nurtured by Metal minerals |
| 庚 | 巳 | Metal forged in Fire |
| 辛 | 子 | Metal refined by Water cooling |
| 壬 | 申 | Water sourced from Metal |
| 癸 | 卯 | Water nourished by Wood |

### 2.3 Direction Rules

**Yang Stems**: Progress **forward** through branches from 長生 point
**Yin Stems**: Progress **backward** through branches from 長生 point

Branch order (forward): 子 → 丑 → 寅 → 卯 → 辰 → 巳 → 午 → 未 → 申 → 酉 → 戌 → 亥
Branch order (backward): 亥 → 戌 → 酉 → 申 → 未 → 午 → 巳 → 辰 → 卯 → 寅 → 丑 → 子

---

## 3. Generation Algorithm

### 3.1 Yang Stem Example (甲)

Starting point: 亥 = 長生

| Branch | Index | Stage |
|--------|-------|-------|
| 亥 | 0 | 長生 (Birth) |
| 子 | 1 | 沐浴 (Bath) |
| 丑 | 2 | 冠帶 (Crown) |
| 寅 | 3 | 臨官 (Office) |
| 卯 | 4 | 帝旺 (Peak) |
| 辰 | 5 | 衰 (Decline) |
| 巳 | 6 | 病 (Sickness) |
| 午 | 7 | 死 (Death) |
| 未 | 8 | 墓 (Tomb) |
| 申 | 9 | 絕 (Extinction) |
| 酉 | 10 | 胎 (Embryo) |
| 戌 | 11 | 養 (Nurture) |

### 3.2 Yin Stem Example (乙)

Starting point: 午 = 長生 (BACKWARD direction)

| Branch | Index | Stage |
|--------|-------|-------|
| 午 | 0 | 長生 (Birth) |
| 巳 | 1 | 沐浴 (Bath) |
| 辰 | 2 | 冠帶 (Crown) |
| 卯 | 3 | 臨官 (Office) |
| 寅 | 4 | 帝旺 (Peak) |
| 丑 | 5 | 衰 (Decline) |
| 子 | 6 | 病 (Sickness) |
| 亥 | 7 | 死 (Death) |
| 戌 | 8 | 墓 (Tomb) |
| 酉 | 9 | 絕 (Extinction) |
| 申 | 10 | 胎 (Embryo) |
| 未 | 11 | 養 (Nurture) |

---

## 4. Verification Method

### 4.1 Completeness Check

Each stem MUST have exactly 12 mappings (one per branch).

### 4.2 Uniqueness Check

Within each stem's mappings, all 12 stages MUST appear exactly once.

### 4.3 Direction Consistency

- Yang stems: Verify forward progression from 長生 point
- Yin stems: Verify backward progression from 長生 point

### 4.4 Classical Reference Validation

Cross-check starting points and direction against:
- 子平眞詮 (Ziping Zhenquan)
- 三命通會 (Sanming Tonghui)
- 滴天髓 (Di Tian Sui)
- 窮通寶鑑 (Qiong Tong Bao Jian)

---

## 5. Implementation Notes

### 5.1 Policy-Driven Design

All 120 mappings (10 stems × 12 branches) are stored in `lifecycle_stages.json`.

**NO hardcoding** of stage logic in code.

### 5.2 Lookup Interface

```python
def get_lifecycle_stage(day_stem: str, branch: str) -> str:
    """
    Args:
        day_stem: One of 甲乙丙丁戊己庚辛壬癸
        branch: One of 子丑寅卯辰巳午未申酉戌亥

    Returns:
        Stage in Chinese: 長生/沐浴/冠帶/臨官/帝旺/衰/病/死/墓/絕/胎/養
    """
    return lifecycle_policy["mappings"][day_stem][branch]
```

### 5.3 Four Pillars Application

Lifecycle stages are calculated for ALL four pillars (年/月/日/時) using the Day Stem as reference:

```python
pillars = {
    "year": {"stem": "甲", "branch": "子"},
    "month": {"stem": "丙", "branch": "寅"},
    "day": {"stem": "戊", "branch": "午"},
    "hour": {"stem": "庚", "branch": "申"}
}

day_stem = pillars["day"]["stem"]  # 戊

lifecycle_stages = {
    "year": get_lifecycle_stage(day_stem, pillars["year"]["branch"]),   # 戊-子 → 胎
    "month": get_lifecycle_stage(day_stem, pillars["month"]["branch"]), # 戊-寅 → 長生
    "day": get_lifecycle_stage(day_stem, pillars["day"]["branch"]),     # 戊-午 → 帝旺
    "hour": get_lifecycle_stage(day_stem, pillars["hour"]["branch"])    # 戊-申 → 病
}
```

---

## 6. Interpretation Guidelines

### 6.1 Strong Positions
- **帝旺 (Peak)**: Maximum strength for Day Stem
- **臨官 (Office)**: Strong, productive energy
- **長生 (Birth)**: Fresh vitality, growth potential

### 6.2 Weak Positions
- **絕 (Extinction)**: Complete depletion
- **死 (Death)**: Very weak state
- **病 (Sickness)**: Compromised energy

### 6.3 Transitional Positions
- **墓 (Tomb)**: Storage, latent potential
- **胎 (Embryo)**: Conception, new beginning
- **養 (Nurture)**: Development phase

### 6.4 Context Matters

Lifecycle stage strength interacts with:
- Five Elements distribution
- Ten Gods relationships
- Hidden Stems (藏干)
- Seasonal climate (節氣)
- Pillar position (Year/Month/Day/Hour)

**Example**: 墓 (Tomb) in Month Pillar may indicate stored ancestral wealth, while in Hour Pillar may suggest legacy concerns.

---

## 7. Classical References

### 7.1 子平眞詮 (Ziping Zhenquan)
- Establishes yin/yang direction rules
- Defines 12-stage cycle as fundamental strength indicator

### 7.2 三命通會 (Sanming Tonghui)
- Provides comprehensive 長生 starting point table
- Discusses seasonal interactions with lifecycle stages

### 7.3 滴天髓 (Di Tian Sui)
- Emphasizes context-dependent interpretation
- Warns against mechanical application without elemental balance

### 7.4 窮通寶鑑 (Qiong Tong Bao Jian)
- Details seasonal adjustments to lifecycle strength
- Provides case studies of lifecycle-climate interactions

---

## 8. Schema Compliance

This methodology generates data that MUST validate against:
- `schemas/lifecycle_stages.schema.json` (v1.1)
- `schemas/daystem_yinyang.schema.json` (v1.0)

**Required Fields**:
- version (semantic versioning)
- generated_on (ISO-8601 date-time)
- source_refs (classical text citations)
- mappings (120 stem-branch combinations)
- labels (zh/ko/en for all 12 stages)

---

## 9. Testing Strategy

### 9.1 Schema Validation
Verify JSON policy passes JsonSchema validation.

### 9.2 Generation Equivalence
Verify algorithmic generation matches policy mappings.

### 9.3 Example Cases
Test all 10 stems with known correct mappings.

### 9.4 Property Tests
- Each stem has exactly 12 mappings
- Each stem uses all 12 stages exactly once
- Yang stems follow forward direction
- Yin stems follow backward direction

---

**End of Methodology Document**
