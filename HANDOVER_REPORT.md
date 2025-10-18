# Saju Engine Handover Report

**Date**: 2025-10-04
**Purpose**: Research and prepare calculation engines for missing features
**Audience**: AI assistants tasked with implementing missing Saju features

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Current State](#current-state)
3. [Missing Features](#missing-features)
4. [Implementation Requirements](#implementation-requirements)
5. [Technical Architecture](#technical-architecture)
6. [Research Tasks](#research-tasks)
7. [Expected Deliverables](#expected-deliverables)

---

## SYSTEM OVERVIEW

### What We're Building

A **Korean Saju (Four Pillars of Destiny) calculation engine** that provides:
- Accurate pillar computation (年月日時)
- Traditional Saju analysis (Ten Gods, Relations, Strength, etc.)
- Fortune predictions and recommendations
- RESTful API microservices architecture

### Technology Stack

- **Language**: Python 3.12
- **Framework**: FastAPI
- **Validation**: Pydantic models
- **Architecture**: 4 microservices
- **Design Pattern**: Policy-driven (JSON configuration files)
- **Testing**: pytest (47/47 tests passing, 100% coverage)

### Architecture

```
services/
├── pillars-service/     # Four Pillars computation (年月日時)
├── astro-service/       # Solar terms & astronomical calculations
├── tz-time-service/     # Timezone/DST handling
└── analysis-service/    # Saju analysis (Ten Gods, Strength, Relations, etc.)
```

---

## CURRENT STATE

### ✅ What We Have (35% Complete)

#### 1. Core Pillars Calculation - 100%
- **File**: `services/pillars-service/app/core/pillars.py`
- **Functionality**: Calculates Year/Month/Day/Hour pillars from birth datetime
- **Data**: Full solar terms 1900-2050
- **Status**: Production-ready, accurate

#### 2. Ten Gods for Stems - 100%
- **File**: `services/analysis-service/app/core/engine.py` (lines 50-85)
- **Functionality**: Maps 10 stems to Ten Gods (比肩/劫財/食神/傷官/etc.)
- **Logic**: Day stem vs other stems using five elements
- **Status**: Complete for heavenly stems only

#### 3. Relations Detection - 100%
- **File**: `services/analysis-service/app/core/engine.py` (lines 149-220)
- **Types**: 六合(He6), 三合(Sanhe), 冲(Chong), 害(Hai), 破(Po), 刑(Xing)
- **Status**: All 6 relation types fully implemented

#### 4. Strength Evaluation - 70%
- **File**: `services/analysis-service/app/core/strength.py`
- **Policy**: `saju_codex_batch_all_v2_6_signed/policies/strength_adjust_v1_3.json`
- **Output**: 5 grades (신강/편강/중화/편약/신약)
- **Components**: 得令/得地/得時/得勢 scoring
- **Status**: Core complete, missing detailed breakdown display

#### 5. Hidden Stems (藏干) - 50%
- **File**: `services/analysis-service/app/core/engine.py` (lines 141-147)
- **Data**: `rulesets/zanggan_table.json` (all 12 branches)
- **Functionality**: Extraction complete
- **Status**: Backend done, not exposed in API response

#### 6. Structure Detection (格局) - 80%
- **File**: `services/analysis-service/app/core/structure.py`
- **Policy**: `saju_codex_batch_all_v2_6_signed/policies/structure_rules_v2_6.json`
- **Types**: 正官/偏官(칠살)/正財/偏財/食神/傷官/etc.
- **Status**: Detection works, confidence scoring needs refinement

#### 7. Luck Direction & Start Age - 20%
- **File**: `services/analysis-service/app/core/luck.py`
- **Policy**: `saju_codex_addendum_v2/policies/luck_policy_v1.json`
- **Functionality**:
  - ✅ Calculates luck start age (based on solar terms)
  - ✅ Determines direction (forward/backward based on gender)
  - ❌ Does NOT generate 10-year luck pillars
- **Status**: Metadata only, no actual pillar generation

#### 8. Divine Stars Catalog - 10%
- **File**: `services/analysis-service/app/core/school.py`
- **Policy**: `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
- **Data**: 4 stars defined (桃花/文昌/天乙貴人/驛馬)
- **Status**: Basic catalog only, no per-pillar mapping

---

### 🔴 What's Missing (65% Incomplete)

These are the features we need you to research and prepare:

---

## MISSING FEATURES

### Priority 0 - CRITICAL (Blocking Basic Service)

#### 1. 🔴 12 Lifecycle Stages (十二運星) - 0% Implemented

**What It Is**:
- Traditional Chinese astrology system mapping day master to lifecycle stages
- 12 stages: 長生(longevity)/沐浴(bathing)/冠帶(crown)/臨官(official)/帝旺(emperor)/衰(decline)/病(illness)/死(death)/墓(tomb)/絕(extinction)/胎(embryo)/養(nurture)
- Korean names: 장생/목욕/관대/임관/제왕/쇠/병/사/묘/절/태/양

**How It Works**:
- Day stem (日干) determines reference point
- Each of 4 branches (Year/Month/Day/Hour) maps to one lifecycle stage
- Lookup table: 10 stems × 12 branches = 120 unique mappings

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Day stem: 乙
Lifecycle stages:
- Year branch 辰 → 乙 at 辰 = 墓 (tomb)
- Month branch 酉 → 乙 at 酉 = 絕 (extinction)
- Day branch 亥 → 乙 at 亥 = 長生 (longevity)
- Hour branch 子 → 乙 at 子 = 沐浴 (bathing)
```

**What's Needed**:
1. **Research Task**: Find authoritative 12 lifecycle stages lookup table
   - Need all 10 stems (甲乙丙丁戊己庚辛壬癸)
   - Need all 12 branches (子丑寅卯辰巳午未申酉戌亥)
   - Total: 120 mappings

2. **Policy File**: `saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json`
   ```json
   {
     "version": "1.0",
     "mappings": {
       "甲": {
         "子": "沐浴",
         "丑": "冠帶",
         "寅": "臨官",
         "卯": "帝旺",
         "辰": "衰",
         "巳": "病",
         "午": "死",
         "未": "墓",
         "申": "絕",
         "酉": "胎",
         "戌": "養",
         "亥": "長生"
       },
       "乙": { ... },
       ...
     }
   }
   ```

3. **Calculator Module**: `services/analysis-service/app/core/lifecycle.py`
   ```python
   class LifecycleCalculator:
       """Calculate 12 lifecycle stages for four pillars."""

       def __init__(self, policy_path: Path):
           with policy_path.open("r", encoding="utf-8") as f:
               self.mappings = json.load(f)["mappings"]

       def calculate(
           self,
           day_stem: str,
           branches: List[str]  # [year_br, month_br, day_br, hour_br]
       ) -> Dict[str, str]:
           """
           Returns: {
               "year": "墓",
               "month": "絕",
               "day": "長生",
               "hour": "沐浴"
           }
           """
           return {
               "year": self.mappings[day_stem][branches[0]],
               "month": self.mappings[day_stem][branches[1]],
               "day": self.mappings[day_stem][branches[2]],
               "hour": self.mappings[day_stem][branches[3]]
           }
   ```

4. **Response Model**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class LifecycleResult(BaseModel):
       """12 lifecycle stages for four pillars."""
       year: str
       month: str
       day: str
       hour: str
   ```

**Estimate**: 5 days (3 days research + 2 days implementation)

---

#### 2. 🔴 Five Elements Distribution (五行分析) - 0% Implemented

**What It Is**:
- Counts and analyzes distribution of five elements (木/火/土/金/水) in birth chart
- Calculates percentage of each element
- Assigns balance labels: 발달(developed)/적정(appropriate)/과다(excessive)/부족(deficient)

**How It Works**:
1. Count elements from:
   - 4 heavenly stems → each has an element
   - 4 earthly branches → each has an element
   - Hidden stems (藏干) → each has an element
2. Calculate percentage: element_count / total_count × 100
3. Assign labels based on thresholds:
   - >35% = 과다 (excessive)
   - 25-35% = 발달 (developed)
   - 15-25% = 적정 (appropriate)
   - <15% = 부족 (deficient)

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Stems: 庚(金) 乙(木) 乙(木) 庚(金)
Branches: 辰(土) 酉(金) 亥(水) 子(水)
Hidden stems in 辰: 乙(木) 癸(水) 戊(土)
Hidden stems in 酉: 辛(金)
Hidden stems in 亥: 壬(水) 甲(木)
Hidden stems in 子: 癸(水)

Element count:
- 木(Wood): 4 (乙×2 + 乙 + 甲) = 25%
- 火(Fire): 0 = 0%
- 土(Earth): 2 (辰 + 戊) = 12.5%
- 金(Metal): 4 (庚×2 + 酉 + 辛) = 25%
- 水(Water): 6 (亥 + 子 + 壬 + 癸×2) = 37.5%

Labels:
- 木: 25% → 발달 (developed)
- 火: 0% → 부족 (deficient)
- 土: 12.5% → 부족 (deficient)
- 金: 25% → 발달 (developed)
- 水: 37.5% → 과다 (excessive)
```

**What's Needed**:

1. **Research Task**: Verify element counting methodology
   - Should all hidden stems be counted equally?
   - Are there different weights (primary/secondary/tertiary hidden stems)?
   - Confirm threshold percentages for labels

2. **Policy File**: `saju_codex_batch_all_v2_6_signed/policies/elements_distribution_criteria.json`
   ```json
   {
     "version": "1.0",
     "counting_method": {
       "stems": {"weight": 1.0, "description": "All heavenly stems count equally"},
       "branches": {"weight": 1.0, "description": "Branch element counts"},
       "hidden_stems": {
         "primary": {"weight": 1.0},
         "secondary": {"weight": 0.5},
         "tertiary": {"weight": 0.3}
       }
     },
     "thresholds": {
       "excessive": 35.0,
       "developed": 25.0,
       "appropriate": 15.0,
       "deficient": 0.0
     },
     "labels": {
       "ko": {
         "excessive": "과다",
         "developed": "발달",
         "appropriate": "적정",
         "deficient": "부족"
       }
     }
   }
   ```

3. **Calculator Module**: `services/analysis-service/app/core/elements.py`
   ```python
   class ElementsCalculator:
       """Calculate five elements distribution."""

       def __init__(self, policy_path: Path):
           with policy_path.open("r", encoding="utf-8") as f:
               self.policy = json.load(f)

       def calculate_distribution(
           self,
           stems: List[str],  # [year, month, day, hour]
           branches: List[str],  # [year, month, day, hour]
           hidden_stems: Dict[str, List[str]]  # {"year": [...], "month": [...], ...}
       ) -> ElementsDistribution:
           """
           Count elements, calculate percentages, assign labels.
           """
           # Count from stems
           # Count from branches
           # Count from hidden stems (with weights if specified)
           # Calculate percentages
           # Assign labels based on thresholds
   ```

4. **Response Model**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class ElementsDistribution(BaseModel):
       """Five elements distribution analysis."""
       wood: float  # percentage
       fire: float
       earth: float
       metal: float
       water: float
       wood_label: str  # 발달/적정/과다/부족
       fire_label: str
       earth_label: str
       metal_label: str
       water_label: str
       total_count: int  # for debugging
   ```

**What We Already Have**:
- Element mappings in `services/pillars-service/app/core/constants.py`:
  ```python
  STEM_TO_ELEMENT = {
      "甲": "木", "乙": "木",
      "丙": "火", "丁": "火",
      "戊": "土", "己": "土",
      "庚": "金", "辛": "金",
      "壬": "水", "癸": "水"
  }

  BRANCH_TO_ELEMENT = {
      "子": "水", "丑": "土", "寅": "木", "卯": "木",
      "辰": "土", "巳": "火", "午": "火", "未": "土",
      "申": "金", "酉": "金", "戌": "土", "亥": "水"
  }
  ```
- Hidden stems extraction in `services/analysis-service/app/core/engine.py`
- Zanggan table in `rulesets/zanggan_table.json`

**Estimate**: 3 days (1 day research + 2 days implementation)

---

#### 3. 🔴 Ten Gods for Branches (地支十神) - 15% Implemented

**What It Is**:
- Calculate Ten Gods (十神) for earthly branches using their hidden stems
- Currently only calculated for heavenly stems

**How It Works**:
1. Each branch has hidden stems (藏干)
2. Take primary hidden stem from each branch
3. Calculate Ten God relationship between day stem and primary hidden stem
4. Display Ten God for each branch position

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Day stem: 乙

Branches and their Ten Gods:
- Year branch 辰 → primary hidden stem 乙 → 乙 vs 乙 = 比肩
- Month branch 酉 → primary hidden stem 辛 → 乙 vs 辛 = 偏官
- Day branch 亥 → primary hidden stem 壬 → 乙 vs 壬 = 正印
- Hour branch 子 → primary hidden stem 癸 → 乙 vs 癸 = 偏印
```

**What's Needed**:

1. **Research Task**: Confirm methodology
   - Should we use primary hidden stem only?
   - Or calculate for all hidden stems and show all?
   - What's the traditional/standard approach?

2. **No Policy File Needed** (logic-based calculation)

3. **Extend Existing Calculator**: Modify `services/analysis-service/app/core/engine.py`
   ```python
   def _calculate_ten_gods_for_branches(
       self,
       day_stem: str,
       branches: List[str]
   ) -> Dict[str, str]:
       """Calculate Ten God for primary hidden stem in each branch."""
       result = {}
       pillar_names = ["year", "month", "day", "hour"]

       for i, branch in enumerate(branches):
           if branch in ZANGGAN_TABLE:
               primary_hidden = ZANGGAN_TABLE[branch][0]  # First is primary
               ten_god = self._calculate_ten_god(day_stem, primary_hidden)
               result[pillar_names[i]] = ten_god

       return result
   ```

4. **Update Response Model**: Modify `TenGodsResult` in `services/analysis-service/app/models/analysis.py`
   ```python
   class TenGodsResult(BaseModel):
       """Ten Gods for stems and branches."""
       summary: dict[str, str]  # Existing: stem Ten Gods
       branches: dict[str, str] = Field(default_factory=dict)  # NEW
       # Example: {"year": "比肩", "month": "偏官", "day": "正印", "hour": "偏印"}
   ```

**What We Already Have**:
- ✅ Ten God calculator: `_calculate_ten_god(day_stem, target_stem) -> str`
- ✅ Hidden stems extractor: `_extract_hidden_stems(branches) -> List[str]`
- ✅ Zanggan table: `rulesets/zanggan_table.json`

**Just Need**: Connect existing pieces together

**Estimate**: 2 days (1 day research methodology + 1 day implementation)

---

#### 4. 🔴 Luck Pillars Generation (大運) - 20% Implemented

**What It Is**:
- Generate 10-year fortune periods (大運) starting from calculated start age
- Each period has stem/branch and shows Ten God and lifecycle stage
- Typically shows 10 periods (covering 100 years)

**How It Works**:
1. Start from month pillar (月柱)
2. Move forward or backward through 60-stem cycle based on direction
3. Generate 10 periods (ages 8-18-28-38-48-58-68-78-88-98)
4. For each period, calculate Ten God and lifecycle stage

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Day stem: 乙
Month pillar: 乙酉
Direction: Forward (male, yang year stem)
Start age: 8

Luck Pillars (大運):
Age 8:  丙戌 → 丙(食神) 戌(墓)
Age 18: 丁亥 → 丁(傷官) 亥(長生)
Age 28: 戊子 → 戊(偏財) 子(沐浴)
Age 38: 己丑 → 己(正財) 丑(冠帶)
Age 48: 庚寅 → 庚(偏官) 寅(臨官)
Age 58: 辛卯 → 辛(正官) 卯(帝旺)
Age 68: 壬辰 → 壬(偏印) 辰(衰)
Age 78: 癸巳 → 癸(正印) 巳(病)
Age 88: 甲午 → 甲(劫財) 午(死)
Age 98: 乙未 → 乙(比肩) 未(墓)
```

**What's Needed**:

1. **Research Task**: Find 60-stem cycle (六十甲子) data
   - Need ordered list of 60 stem-branch combinations
   - Standard cycle order starting from 甲子

2. **Policy File**: `rulesets/sixty_jiazi.json`
   ```json
   {
     "version": "1.0",
     "cycle": [
       {"index": 0, "stem": "甲", "branch": "子", "name": "甲子"},
       {"index": 1, "stem": "乙", "branch": "丑", "name": "乙丑"},
       {"index": 2, "stem": "丙", "branch": "寅", "name": "丙寅"},
       ...
       {"index": 59, "stem": "癸", "branch": "亥", "name": "癸亥"}
     ]
   }
   ```

3. **Extend Existing Calculator**: Modify `services/analysis-service/app/core/luck.py`
   ```python
   class LuckCalculator:
       # Existing methods: compute_start_age(), luck_direction()

       def generate_luck_pillars(
           self,
           month_pillar: str,  # e.g., "乙酉"
           direction: str,  # "forward" or "reverse"
           start_age: float,  # e.g., 8.5
           count: int = 10
       ) -> List[LuckPillar]:
           """
           Generate luck pillar sequence.

           Steps:
           1. Find month_pillar index in 60-cycle
           2. Move forward/backward to get next pillars
           3. Calculate Ten God for each pillar stem
           4. Calculate lifecycle for each pillar branch
           5. Return list of LuckPillar objects
           """
   ```

4. **Response Models**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class LuckPillar(BaseModel):
       """Single 10-year luck period."""
       age: int  # Starting age (8, 18, 28, ...)
       stem: str  # 丙, 丁, 戊, ...
       branch: str  # 戌, 亥, 子, ...
       pillar: str  # 丙戌, 丁亥, ...
       ten_god: str  # 食神, 傷官, ...
       lifecycle: str  # 墓, 長生, ...

   class LuckPillarsResult(BaseModel):
       """Complete luck pillars sequence."""
       start_age: float
       direction: str
       pillars: List[LuckPillar]
   ```

**What We Already Have**:
- ✅ Start age calculation: `compute_start_age()` in luck.py
- ✅ Direction calculation: `luck_direction()` in luck.py
- ✅ Ten God calculator (for stems)
- ⏳ Lifecycle calculator (from Feature #1)

**Just Need**: 60-stem cycle data + generation algorithm

**Estimate**: 7 days (2 days 60-cycle research + 5 days implementation + integration)

---

### Priority 1 - IMPORTANT (For Feature Completeness)

#### 5. 🟡 Yongshin Calculation (用神) - 5% Implemented

**What It Is**:
- Determines beneficial element (用神) for the person
- Recommends which element to strengthen based on chart balance
- Types: 억부용신/조후용신/통관용신/병약용신

**How It Works**:
- **억부용신 (Suppression/Support)**: Based on day master strength
  - Strong day master → need 財/官/食傷 (draining elements)
  - Weak day master → need 印/比劫 (supporting elements)
- **조후용신 (Climate Adjustment)**: Based on birth season
  - Cold season → need Fire
  - Hot season → need Water
- **통관용신 (Mediation)**: Mediates conflicts
- **병약용신 (Cure)**: Fixes specific imbalances

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Day stem: 乙 (Wood)
Strength: 신약 (weak) - 45%
Elements: 木25% 火0% 土12.5% 金25% 水37.5%
Season: 酉月 (autumn) - Metal season, cold

Analysis:
- Day master weak → needs support
- Missing Fire element completely
- Cold season → needs warming

Yongshin: 火 (Fire)
Type: 조후용신 (climate adjustment) + 억부용신 (support)
Reason: Warm the chart and support weak wood with fire
```

**What's Needed**:

1. **Research Task**: Study yongshin selection methodology
   - Decision tree for each type
   - Priority rules (which type takes precedence?)
   - How to combine multiple factors

2. **Policy File**: `saju_codex_batch_all_v2_6_signed/policies/yongshin_criteria.json`
   ```json
   {
     "version": "1.0",
     "decision_tree": {
       "priority_order": ["병약용신", "조후용신", "억부용신", "통관용신"],

       "억부용신": {
         "strong_day_master": {
           "condition": "strength_score >= 60",
           "elements_needed": {
             "if_wood": ["金", "土"],
             "if_fire": ["水", "金"],
             "if_earth": ["木", "水"],
             "if_metal": ["火", "木"],
             "if_water": ["土", "火"]
           }
         },
         "weak_day_master": {
           "condition": "strength_score < 60",
           "elements_needed": {
             "if_wood": ["水", "木"],
             "if_fire": ["木", "火"],
             "if_earth": ["火", "土"],
             "if_metal": ["土", "金"],
             "if_water": ["金", "水"]
           }
         }
       },

       "조후용신": {
         "cold_months": {
           "months": ["亥", "子", "丑"],
           "needed": "火"
         },
         "hot_months": {
           "months": ["巳", "午", "未"],
           "needed": "水"
         },
         "dry_months": {
           "months": ["辰", "戌", "丑", "未"],
           "needed": "水"
         },
         "wet_months": {
           "months": ["亥", "子"],
           "needed": "土"
         }
       },

       "통관용신": {
         "conditions": [
           {
             "conflict": "wood_controls_earth_too_strong",
             "mediator": "火"
           },
           {
             "conflict": "metal_controls_wood_too_strong",
             "mediator": "水"
           }
         ]
       }
     }
   }
   ```

3. **Calculator Module**: `services/analysis-service/app/core/yongshin.py`
   ```python
   class YongshinCalculator:
       """Determine beneficial element (用神)."""

       def __init__(self, policy_path: Path):
           with policy_path.open("r", encoding="utf-8") as f:
               self.policy = json.load(f)

       def calculate(
           self,
           day_stem: str,
           month_branch: str,
           strength: StrengthDetails,
           elements: ElementsDistribution
       ) -> YongshinResult:
           """
           Determine yongshin through decision tree.

           Steps:
           1. Check for 병약용신 (specific problems)
           2. Check for 조후용신 (climate needs)
           3. Check for 억부용신 (strength balance)
           4. Check for 통관용신 (mediation)
           5. Return primary element + type + reasoning
           """
   ```

4. **Response Model**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class YongshinResult(BaseModel):
       """Beneficial element recommendation."""
       primary_element: str  # 木/火/土/金/水
       yongshin_type: str  # 억부용신/조후용신/통관용신/병약용신
       reasoning: str  # Human-readable explanation
       secondary_elements: List[str] = Field(default_factory=list)
   ```

**What We Already Have**:
- ✅ Strength evaluation (gives strength score)
- ⏳ Elements distribution (from Feature #2)
- 🟡 Climate data: `saju_codex_addendum_v2/policies/climate_map_v1.json`

**Estimate**: 5 days (2 days research + 3 days implementation)

---

#### 6. 🟡 Divine Stars Per-Pillar Mapping (十二神殺) - 10% Implemented

**What It Is**:
- Map divine stars (神殺) to specific pillar positions
- Separate into auspicious (吉星) and inauspicious (凶星)
- Show which stars appear in Year/Month/Day/Hour positions

**Common Divine Stars**:
- **Auspicious**: 天乙貴人, 文昌, 天德, 月德, 福星, 祿神
- **Inauspicious**: 羊刃, 桃花, 驛馬, 華蓋, 孤辰, 寡宿, 空亡

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子
Day stem: 乙

Divine Stars:
Year (庚辰): 天乙貴人, 華蓋
Month (乙酉): 桃花, 咸池
Day (乙亥): 天德貴人, 文昌
Hour (庚子): 驛馬, 將星

Auspicious: 天乙貴人, 天德貴人, 文昌
Inauspicious: 桃花, 咸池, 驛馬
```

**What's Needed**:

1. **Research Task**: Compile complete divine stars list with mapping rules
   - Need ~24 common stars
   - Each star has specific calculation rule based on day stem or branch
   - Need to verify traditional mapping formulas

2. **Expand Existing Policy**: `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
   ```json
   {
     "version": "2.0",
     "classification": {
       "auspicious": ["天乙貴人", "文昌", "天德", "月德", "福星", "祿神"],
       "inauspicious": ["羊刃", "桃花", "驛馬", "華蓋", "孤辰", "寡宿"]
     },
     "stars": [
       {
         "name": "天乙貴人",
         "key": "tianyiguiren",
         "type": "auspicious",
         "calculation": {
           "based_on": "day_stem",
           "mappings": {
             "甲": ["丑", "未"],
             "乙": ["子", "申"],
             "丙": ["亥", "酉"],
             "丁": ["亥", "酉"],
             "戊": ["丑", "未"],
             "己": ["子", "申"],
             "庚": ["丑", "未"],
             "辛": ["寅", "午"],
             "壬": ["卯", "巳"],
             "癸": ["卯", "巳"]
           }
         }
       },
       {
         "name": "桃花",
         "key": "taohua",
         "type": "inauspicious",
         "calculation": {
           "based_on": "year_branch",
           "mappings": {
             "寅午戌": "卯",
             "申子辰": "酉",
             "巳酉丑": "午",
             "亥卯未": "子"
           }
         }
       }
     ]
   }
   ```

3. **Extend Calculator**: Modify `services/analysis-service/app/core/school.py`
   ```python
   class ShenshaCatalog:
       # Existing: list_enabled()

       def map_to_pillars(
           self,
           day_stem: str,
           year_branch: str,
           pillars: List[str]  # [year, month, day, hour] branches
       ) -> Dict[str, List[str]]:
           """
           Map divine stars to pillar positions.

           Returns: {
               "year": ["天乙貴人", "華蓋"],
               "month": ["桃花"],
               "day": ["天德貴人", "文昌"],
               "hour": ["驛馬"]
           }
           """
   ```

4. **Update Response Model**: Modify `ShenshaResult` in `services/analysis-service/app/models/analysis.py`
   ```python
   class ShenshaResult(BaseModel):
       """Divine stars analysis."""
       enabled: bool
       auspicious: List[str] = Field(default_factory=list)
       inauspicious: List[str] = Field(default_factory=list)
       per_pillar: Dict[str, List[str]] = Field(default_factory=dict)
       # Example per_pillar: {"year": ["天乙貴人"], "month": ["桃花"], ...}
   ```

**What We Already Have**:
- 🟡 Basic catalog with 4 stars in `shensha_catalog_v1.json`
- ✅ Catalog loader in `school.py`

**Just Need**: Expand catalog + implement mapping logic

**Estimate**: 3 days (1 day research + 2 days implementation)

---

#### 7. ✅ Hidden Stems Display - 50% Implemented

**What It Is**:
- Display hidden stems (藏干) for each branch position
- Already extracted in backend, just needs API exposure

**Example**:
```
Birth pillars: 庚辰 乙酉 乙亥 庚子

Hidden Stems:
Year (辰): 乙, 癸, 戊
Month (酉): 辛
Day (亥): 壬, 甲
Hour (子): 癸
```

**What's Needed**:

1. **No Research Needed** (data already complete)

2. **Modify Existing Method**: Refactor in `services/analysis-service/app/core/engine.py`
   ```python
   def _extract_hidden_stems_by_pillar(
       self,
       branches: List[str]
   ) -> Dict[str, List[str]]:
       """Extract hidden stems per pillar position."""
       return {
           "year": ZANGGAN_TABLE.get(branches[0], []),
           "month": ZANGGAN_TABLE.get(branches[1], []),
           "day": ZANGGAN_TABLE.get(branches[2], []),
           "hour": ZANGGAN_TABLE.get(branches[3], [])
       }
   ```

3. **Response Model**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class HiddenStemsResult(BaseModel):
       """Hidden stems per pillar."""
       year: List[str]
       month: List[str]
       day: List[str]
       hour: List[str]
   ```

**What We Already Have**:
- ✅ Complete zanggan table: `rulesets/zanggan_table.json`
- ✅ Extraction function: `_extract_hidden_stems()`

**Just Need**: Restructure output and add to API response

**Estimate**: 1 day (simple refactor)

---

## IMPLEMENTATION REQUIREMENTS

### Design Patterns to Follow

#### 1. Policy-Driven Architecture

All business logic should be in JSON policy files, NOT hardcoded:

```python
# ❌ BAD - Hardcoded logic
def calculate_lifecycle(day_stem, branch):
    if day_stem == "甲" and branch == "亥":
        return "長生"
    elif day_stem == "甲" and branch == "子":
        return "沐浴"
    # ... 120 more if statements

# ✅ GOOD - Policy-driven
class LifecycleCalculator:
    def __init__(self, policy_path: Path):
        with policy_path.open("r", encoding="utf-8") as f:
            self.mappings = json.load(f)["mappings"]

    def calculate(self, day_stem, branch):
        return self.mappings[day_stem][branch]
```

#### 2. Pydantic Response Models

All outputs must use typed Pydantic models:

```python
# ✅ Define clear response structure
class LifecycleResult(BaseModel):
    """12 lifecycle stages for four pillars."""
    year: str
    month: str
    day: str
    hour: str

# Usage in API
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    lifecycle = lifecycle_calculator.calculate(...)
    return AnalysisResponse(
        lifecycle=lifecycle,
        ...
    )
```

#### 3. File Organization

```
services/analysis-service/
├── app/
│   ├── core/              # Business logic
│   │   ├── lifecycle.py   # NEW: Lifecycle calculator
│   │   ├── elements.py    # NEW: Elements calculator
│   │   ├── yongshin.py    # NEW: Yongshin calculator
│   │   ├── engine.py      # MODIFY: Main orchestrator
│   │   ├── luck.py        # MODIFY: Add pillar generation
│   │   └── school.py      # MODIFY: Expand shensha mapping
│   │
│   └── models/
│       └── analysis.py    # MODIFY: Add all new response models

saju_codex_batch_all_v2_6_signed/policies/
├── lifecycle_stages.json          # NEW
├── elements_distribution_criteria.json  # NEW
└── yongshin_criteria.json         # NEW

rulesets/
└── sixty_jiazi.json               # NEW
```

---

## TECHNICAL ARCHITECTURE

### Current System Flow

```
1. User Request
   ↓
2. pillars-service: Calculate Year/Month/Day/Hour pillars
   ↓
3. analysis-service: Analyze pillars
   ├── Ten Gods calculation
   ├── Relations detection
   ├── Strength evaluation
   ├── Structure detection
   ├── Luck calculation
   └── Shensha catalog
   ↓
4. Return AnalysisResponse
```

### Integration Points

When implementing new features, integrate into `services/analysis-service/app/core/engine.py`:

```python
class AnalysisEngine:
    def __init__(self):
        # Existing calculators
        self.strength_evaluator = StrengthEvaluator(...)
        self.structure_scorer = StructureScorer(...)

        # NEW calculators to add
        self.lifecycle_calculator = LifecycleCalculator(policy_path)
        self.elements_calculator = ElementsCalculator(policy_path)
        self.yongshin_calculator = YongshinCalculator(policy_path)

    def analyze(self, pillars: dict) -> AnalysisResponse:
        # Existing calculations
        parsed = self._parse_pillars(pillars)
        ten_gods = self._calculate_ten_gods(...)
        relations = self._parse_relations(...)
        strength = self.strength_evaluator.evaluate(...)

        # NEW calculations to add
        lifecycle = self.lifecycle_calculator.calculate(
            day_stem=parsed.day_stem,
            branches=parsed.branches
        )

        elements = self.elements_calculator.calculate_distribution(
            stems=parsed.stems,
            branches=parsed.branches,
            hidden_stems=self._extract_hidden_stems_by_pillar(...)
        )

        yongshin = self.yongshin_calculator.calculate(
            day_stem=parsed.day_stem,
            month_branch=parsed.month_branch,
            strength=strength_details,
            elements=elements
        )

        # Return complete response
        return AnalysisResponse(
            ten_gods=ten_gods,
            relations=relations,
            strength=strength,
            lifecycle=lifecycle,  # NEW
            elements=elements,    # NEW
            yongshin=yongshin,   # NEW
            ...
        )
```

### Testing Requirements

Each feature must have tests in `services/analysis-service/tests/`:

```python
# tests/test_lifecycle.py
def test_lifecycle_calculation():
    """Test 12 lifecycle stages calculation."""
    calculator = LifecycleCalculator(policy_path)

    # Test case from premium report
    result = calculator.calculate(
        day_stem="乙",
        branches=["辰", "酉", "亥", "子"]
    )

    assert result["year"] == "墓"
    assert result["month"] == "絕"
    assert result["day"] == "長生"
    assert result["hour"] == "沐浴"
```

---

## RESEARCH TASKS

### Task 1: 12 Lifecycle Stages Lookup Table

**Objective**: Find authoritative 120-mapping table (10 stems × 12 branches)

**Sources to Check**:
- Traditional Saju textbooks (Korean/Chinese)
- Online Saju calculators (verify consistency)
- Academic papers on Chinese astrology
- 四柱推命 (Japanese) resources

**Deliverable**: Complete JSON with all 120 mappings

**Validation**: Cross-reference multiple sources for accuracy

---

### Task 2: Five Elements Distribution Methodology

**Objective**: Confirm counting and labeling methodology

**Questions to Answer**:
1. Should all hidden stems count equally or use weights?
2. What are standard threshold percentages?
3. Are there variations by school/tradition?

**Sources to Check**:
- Traditional Saju calculation books
- Modern Korean Saju apps (reverse engineer if needed)
- Online calculators

**Deliverable**: Policy JSON with counting rules and thresholds

---

### Task 3: Sixty Jiazi Cycle Data

**Objective**: Get ordered list of 60 stem-branch combinations

**This is Standard**: The 60-cycle order is well-established

**Sources**:
- Wikipedia: Sexagenary cycle
- Any Chinese calendar reference
- Verify order starts with 甲子

**Deliverable**: JSON array of 60 ordered combinations

---

### Task 4: Yongshin Decision Logic

**Objective**: Map out decision tree for beneficial element selection

**Questions to Answer**:
1. What are priority rules (which type first)?
2. How to combine 억부/조후/통관/병약?
3. What are specific conditions for each type?

**Sources to Check**:
- Yongshin theory in Saju textbooks
- Practical examples from experts
- Modern interpretations

**Deliverable**: Comprehensive decision tree in JSON

---

### Task 5: Divine Stars Mapping Rules

**Objective**: Compile 20+ stars with calculation formulas

**Stars to Research**:
- Auspicious: 天乙貴人, 文昌, 天德, 月德, 福星, 祿神, 德神, 太極貴人
- Inauspicious: 羊刃, 桃花, 驛馬, 華蓋, 孤辰, 寡宿, 空亡, 劫煞, 災煞, 亡神

**For Each Star**:
- Name (Chinese + Korean)
- Calculation rule (based on day stem or branch)
- Mapping table
- Classification (auspicious/inauspicious)

**Deliverable**: Expanded shensha_catalog JSON with all mappings

---

### Task 6: Ten Gods for Branches Methodology

**Objective**: Confirm which hidden stem to use

**Questions**:
- Primary only or all hidden stems?
- How do different traditions handle this?

**Sources**: Traditional references, modern implementations

**Deliverable**: Clear methodology documentation

---

## EXPECTED DELIVERABLES

### For Each Feature:

#### 1. Research Report
- Methodology explanation
- Sources consulted
- Variations/alternatives found
- Recommended approach with justification

#### 2. Policy File (if applicable)
- Complete JSON with all data
- Clear structure and comments
- Validated against multiple sources

#### 3. Calculator Module
- Python class following existing patterns
- Policy-driven (load from JSON)
- Clear method signatures
- Docstrings with examples

#### 4. Response Model
- Pydantic BaseModel class
- Type hints
- Field descriptions
- Example output

#### 5. Integration Code
- Modification to engine.py
- How to call the new calculator
- How to add to AnalysisResponse

#### 6. Test Cases
- At least 3 test cases per feature
- Use real Saju examples
- Cover edge cases

#### 7. Documentation
- Feature description
- Usage examples
- API response format

---

## EXAMPLE DELIVERABLE STRUCTURE

### For Lifecycle Stages Feature:

```
deliverables/lifecycle_stages/
├── research_report.md
│   ├── Methodology
│   ├── Sources
│   ├── Findings
│   └── Recommendations
│
├── policy/
│   └── lifecycle_stages.json
│       (120 mappings)
│
├── code/
│   ├── lifecycle.py
│   │   (LifecycleCalculator class)
│   │
│   ├── models.py
│   │   (LifecycleResult class)
│   │
│   └── integration.py
│       (How to add to engine.py)
│
├── tests/
│   └── test_lifecycle.py
│       (Test cases)
│
└── examples/
    ├── example_input.json
    └── example_output.json
```

---

## PRIORITY ORDER FOR IMPLEMENTATION

Based on impact and dependencies:

### Week 1 (5 days)
1. **12 Lifecycle Stages** - Foundation for luck pillars
2. **Sixty Jiazi Cycle** - Prerequisite for luck pillars

### Week 2 (5 days)
3. **Five Elements Distribution** - Prerequisite for yongshin
4. **Ten Gods for Branches** - Quick win, all pieces exist

### Week 3 (7 days)
5. **Luck Pillars Generation** - Depends on lifecycle + 60-cycle
6. **Hidden Stems Display** - Quick win, simple refactor

### Week 4 (5 days)
7. **Yongshin Calculation** - Depends on elements distribution

### Week 5 (3 days)
8. **Divine Stars Mapping** - Final polish feature

**Total**: ~25 days for complete implementation

---

## REFERENCE MATERIALS

### What You Already Have Access To

1. **Existing Codebase**:
   - `/Users/yujumyeong/coding/ projects/사주/services/`
   - Study existing calculators for patterns

2. **Existing Policies**:
   - `/Users/yujumyeong/coding/ projects/사주/saju_codex_batch_all_v2_6_signed/policies/`
   - See how current features use JSON policies

3. **Existing Tests**:
   - `/Users/yujumyeong/coding/ projects/사주/services/analysis-service/tests/`
   - Model new tests after existing ones

4. **Gap Analysis**:
   - `/Users/yujumyeong/coding/ projects/사주/FEATURE_GAP_ANALYSIS.md`
   - Shows what premium services have

5. **Codex Scan Report**:
   - `/Users/yujumyeong/coding/ projects/사주/CODEX_AND_CODEBASE_SCAN_REPORT.md`
   - Shows what data exists vs missing

### What You Need to Research

1. **Traditional Saju References** (Chinese/Korean):
   - 子平真詮 (Zi Ping Zhen Quan)
   - 滴天髓 (Di Tian Sui)
   - 窮通寶鑑 (Qiong Tong Bao Jian)
   - Korean Saju textbooks

2. **Online Resources**:
   - Reputable Saju calculators (for verification)
   - Academic papers on Chinese astrology
   - Forums/communities with experts

3. **Existing Apps** (for reverse engineering):
   - Premium Korean Saju apps
   - Chinese Bazi calculators
   - Japanese Shichusuimei tools

---

## QUALITY STANDARDS

### All Deliverables Must:

1. **Be Accurate**: Cross-referenced with multiple traditional sources
2. **Be Complete**: No placeholders or "TODO" items
3. **Be Documented**: Clear explanations and examples
4. **Be Tested**: Working test cases included
5. **Follow Patterns**: Match existing code style and architecture
6. **Be Policy-Driven**: Logic in JSON files, not hardcoded
7. **Be Typed**: Full Pydantic models with type hints

### Acceptance Criteria:

- [ ] Research report with 3+ authoritative sources
- [ ] Policy JSON validated against sources
- [ ] Calculator follows existing patterns
- [ ] Pydantic models with full type hints
- [ ] Integration code ready to merge
- [ ] Tests passing (100% coverage)
- [ ] Examples with real Saju cases
- [ ] Documentation complete

---

## QUESTIONS TO ANSWER DURING RESEARCH

### For Each Feature:

1. **What is the traditional/authoritative source?**
   - Which books/texts define this feature?
   - Are there variations by school/region?

2. **What is the exact calculation method?**
   - Step-by-step algorithm
   - Any special cases or exceptions?

3. **What are the possible output values?**
   - Complete list of all possible results
   - Korean and Chinese terms

4. **How do modern implementations handle this?**
   - What do premium apps show?
   - Any shortcuts or approximations?

5. **What are common errors or misconceptions?**
   - What mistakes do beginners make?
   - How to validate correctness?

---

## CONTACT POINTS

### When You Have Questions:

1. **Code Architecture**: Refer to existing calculators in `app/core/`
2. **Policy Format**: Refer to existing policies in `saju_codex_batch_all_v2_6_signed/policies/`
3. **Response Models**: Refer to `services/analysis-service/app/models/analysis.py`
4. **Testing**: Refer to `services/analysis-service/tests/`

### What to Submit:

Submit each feature deliverable package as outlined above, organized in folders.

---

## FINAL NOTES

### Remember:

- **Quality over speed** - Accuracy is critical for Saju calculations
- **Traditional sources first** - Modern apps may have errors
- **Cross-validate everything** - Check multiple sources
- **Document your reasoning** - Explain why you chose specific approaches
- **Test with real cases** - Use actual birth data examples
- **Follow existing patterns** - Don't reinvent the wheel

### Success Criteria:

When complete, we should be able to:
1. ✅ Calculate 12 lifecycle stages for any birth chart
2. ✅ Show five elements distribution with balance analysis
3. ✅ Display Ten Gods for both stems and branches
4. ✅ Generate 10-year luck pillar sequences
5. ✅ Recommend beneficial elements (yongshin)
6. ✅ Map divine stars to pillar positions
7. ✅ Expose hidden stems in API response

All with **100% test coverage** and **traditional accuracy**.

---

**End of Handover Report**

**Good luck with your research! 加油! 화이팅!**
