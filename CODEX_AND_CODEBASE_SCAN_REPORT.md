# Codex Data & Codebase Scan Report

**Date**: 2025-10-04
**Scope**: Comprehensive scan of saju_codex directories + current codebase implementation status
**Purpose**: Identify what can be reused vs what needs to be created

---

## EXECUTIVE SUMMARY

### Codex Directories Scanned
- ✅ `saju_codex_batch_all_v2_6_signed/` - 18 policy files
- ✅ `saju_codex_addendum_v2/` - 6 policy files
- ✅ `rulesets/` - 2 policy files (root level)

### Codebase Scanned
- ✅ `services/analysis-service/` - Main analysis engine
- ✅ `services/pillars-service/` - Pillar computation
- ✅ `services/astro-service/` - Solar terms
- ✅ `services/tz-time-service/` - Timezone handling

### Key Findings

**What We Can Use Immediately** (✅ Complete in Codex):
- Strength evaluation policies (100%)
- Relations policies (100%)
- Structure detection policies (100%)
- Root/Seal scoring (100%)
- Zanggan table (100%)

**What We Have Partially** (🟡 40-50% in Codex + Code):
- Luck pillars (40% - direction policy exists, generation logic missing)
- Divine stars (30% - catalog exists, mapping incomplete)
- Ten Gods for branches (10% - extraction done, calculation missing)
- Hidden stems display (50% - backend done, API output missing)

**What's Completely Missing** (🔴 0% in both):
- 12 Lifecycle Stages (0%)
- Five Elements Distribution (0%)
- Yongshin calculation logic (0%)

---

## FEATURE-BY-FEATURE ANALYSIS

### 🔴 1. 12 Lifecycle Stages (十二運星)

#### Codex Status: NOT FOUND (0%)
**Searched in:**
- `saju_codex_batch_all_v2_6_signed/policies/` - No matches
- `saju_codex_addendum_v2/policies/` - No matches

**Keywords searched:**
- 장생, 목욕, 관대, 임관, 제왕, 衰, 病, 死, 墓, 絕, 胎, 養
- lifecycle, 십이운성, 12운성, 長生, 沐浴, 冠帶, 臨官, 帝旺

**Result:** No policy files exist for lifecycle stages

#### Codebase Status: NOT FOUND (0%)
**Searched in:**
- `services/analysis-service/app/core/*.py` - No matches
- `services/analysis-service/app/models/*.py` - No matches

**Result:** No implementation exists

#### What's Needed:
1. **Create policy file**: `saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json`
   - 10 stems × 12 branches = 120 mappings
   - Structure:
     ```json
     {
       "甲": {"子": "沐浴", "丑": "冠帶", "寅": "臨官", ...},
       "乙": {"子": "病", "丑": "衰", "寅": "帝旺", ...},
       ...
     }
     ```

2. **Create calculator**: `services/analysis-service/app/core/lifecycle.py`
   ```python
   class LifecycleCalculator:
       def calculate(self, day_stem: str, branches: List[str]) -> Dict[str, str]:
           # Returns {"year": "목욕", "month": "사", "day": "절", "hour": "관대"}
   ```

3. **Add response model**: `services/analysis-service/app/models/analysis.py`
   ```python
   class LifecycleResult(BaseModel):
       year: str
       month: str
       day: str
       hour: str
   ```

**Estimate**: 5 days (3 days policy creation + 2 days implementation)

---

### 🔴 2. Five Elements Distribution

#### Codex Status: NOT FOUND (0%)
**Searched in:**
- `saju_codex_batch_all_v2_6_signed/policies/` - No matches
- `saju_codex_addendum_v2/policies/` - No matches

**Keywords searched:**
- 오행분석, five elements distribution, element percentage, 木火土金水 distribution

**Related files found (but different purpose):**
- ✅ `saju_codex_batch_all_v2_6_signed/policies/seasons_wang_map_v2.json`
  - Purpose: Seasonal element **states** (旺相休囚死)
  - NOT element distribution percentages
  - Used for: Strength calculation only

**Result:** No distribution/percentage policy exists

#### Codebase Status: PARTIAL (5%)
**What exists:**
- ✅ Element mappings in `services/pillars-service/app/core/constants.py` (lines 57-83):
  ```python
  STEM_TO_ELEMENT = {"甲": "木", "乙": "木", "丙": "火", ...}
  BRANCH_TO_ELEMENT = {"子": "水", "丑": "土", "寅": "木", ...}
  ```
- ✅ Element relationships in `services/analysis-service/app/core/engine.py` (lines 33-42):
  ```python
  ELEMENT_GENERATES = {"木": "火", "火": "土", ...}
  ELEMENT_CONTROLS = {"木": "土", "火": "金", ...}
  ```

**What's missing:**
- ❌ No element counting function
- ❌ No percentage calculation
- ❌ No balance labels (발달/적정/과다/부족)

**Result:** Only basic mappings exist, no analysis feature

#### What's Needed:
1. **Create policy file**: `saju_codex_batch_all_v2_6_signed/policies/elements_distribution_criteria.json`
   ```json
   {
     "thresholds": {
       "excessive": 35.0,
       "developed": 25.0,
       "appropriate": 15.0,
       "deficient": 10.0
     },
     "labels": {
       "excessive": "과다",
       "developed": "발달",
       "appropriate": "적정",
       "deficient": "부족"
     }
   }
   ```

2. **Create calculator**: `services/analysis-service/app/core/elements.py`
   ```python
   class ElementsCalculator:
       def calculate_distribution(self, pillars, hidden_stems) -> ElementsDistribution:
           # Count elements from 4 stems + 4 branches + hidden stems
           # Calculate percentages
           # Assign labels (발달/적정/과다/부족)
   ```

3. **Add response model**: `services/analysis-service/app/models/analysis.py`
   ```python
   class ElementsDistribution(BaseModel):
       wood: float
       fire: float
       earth: float
       metal: float
       water: float
       wood_label: str
       fire_label: str
       earth_label: str
       metal_label: str
       water_label: str
   ```

**Estimate**: 3 days (1 day policy + 2 days implementation)

---

### 🟡 3. Ten Gods for Branches

#### Codex Status: NOT APPLICABLE
**Reason:** This is a calculation logic feature, not a policy-driven feature. No policy file needed.

#### Codebase Status: PARTIAL (10-15%)
**What exists:**
- ✅ **Hidden stems extraction** - COMPLETE:
  - File: `services/analysis-service/app/core/engine.py` (lines 141-147)
  - Function: `_extract_hidden_stems(branches) -> List[str]`
  - Data: `rulesets/zanggan_table.json` with all 12 branches
  - Example: `{"子": ["壬", "癸"], "丑": ["癸", "辛", "己"], ...}`

- ✅ **Ten Gods calculator** - COMPLETE:
  - File: `services/analysis-service/app/core/engine.py` (lines 50-85)
  - Function: `_calculate_ten_god(day_stem, target_stem) -> str`
  - Returns: 比肩, 劫財, 食神, 傷官, 偏財, 正財, 偏官, 正官, 偏印, 正印

**What's missing:**
- ❌ No function to **apply** Ten God calculator to branch hidden stems
- ❌ Hidden stems extracted but not converted to Ten Gods
- ❌ Current `TenGodsResult` model only has `summary: dict[str, str]` for stems
- ❌ No `branches: dict[str, str]` field in response

**Result:** All building blocks exist, just need to connect them

#### What's Needed:
1. **Modify existing method** in `services/analysis-service/app/core/engine.py`:
   ```python
   def _calculate_ten_gods_for_branches(self, day_stem: str, branches: List[str]) -> Dict[str, str]:
       """Calculate Ten God for primary hidden stem in each branch."""
       result = {}
       for i, branch in enumerate(branches):
           pillar_name = ["year", "month", "day", "hour"][i]
           if branch in ZANGGAN_TABLE:
               primary_hidden = ZANGGAN_TABLE[branch][0]  # First stem is primary
               ten_god = self._calculate_ten_god(day_stem, primary_hidden)
               result[pillar_name] = ten_god
       return result
   ```

2. **Update response model**:
   ```python
   class TenGodsResult(BaseModel):
       summary: dict[str, str]  # Existing: stem Ten Gods
       branches: dict[str, str] = Field(default_factory=dict)  # NEW: branch Ten Gods
   ```

3. **Update `analyze()` method** to call new function

**Estimate**: 2 days (simple implementation, all pieces exist)

---

### 🟡 4. Luck Pillars Generation

#### Codex Status: PARTIAL (40%)
**What exists:**
- ✅ `saju_codex_addendum_v2/policies/luck_policy_v1.json`
  - Defines luck direction methods (forward/backward)
  - Supports traditional_sex method (male→forward, female→reverse)
  - Structure:
    ```json
    {
      "methods": {
        "traditional_sex": {
          "default": true,
          "rule": "male->forward, female->reverse"
        }
      }
    }
    ```

**What's missing:**
- ❌ No 60-stem cycle (六十甲子) data
- ❌ No luck pillar generation rules
- ❌ No age period definitions

#### Codebase Status: PARTIAL (20%)
**What exists:**
- ✅ **Luck start age calculation** - COMPLETE:
  - File: `services/analysis-service/app/core/luck.py` (lines 65-98)
  - Function: `compute_start_age(birth_dt, prev_term, next_term) -> float`
  - Returns: Start age with fractional precision

- ✅ **Luck direction** - COMPLETE:
  - File: `services/analysis-service/app/core/luck.py` (lines 100-114)
  - Function: `luck_direction(year_stem, sex_at_birth) -> str`
  - Returns: "forward" or "reverse"

**What's missing:**
- ❌ No actual luck pillar generation (the 10-year periods)
- ❌ No function to cycle through 60 Jiazi stems/branches
- ❌ No Ten Gods calculation for each luck period
- ❌ No lifecycle stage calculation for each luck period

**Result:** Foundation exists (start age + direction), core generation missing

#### What's Needed:
1. **Create policy file**: `rulesets/sixty_jiazi.json`
   ```json
   {
     "cycle": [
       {"index": 0, "stem": "甲", "branch": "子"},
       {"index": 1, "stem": "乙", "branch": "丑"},
       ...
       {"index": 59, "stem": "癸", "branch": "亥"}
     ]
   }
   ```

2. **Extend existing calculator** in `services/analysis-service/app/core/luck.py`:
   ```python
   class LuckCalculator:
       def generate_luck_pillars(
           self,
           month_pillar: str,
           direction: str,
           start_age: float,
           count: int = 10
       ) -> List[LuckPillar]:
           # Find month pillar in 60-cycle
           # Move forward/backward to generate 10 periods
           # Calculate Ten Gods for each
           # Calculate lifecycle for each
   ```

3. **Add response models**:
   ```python
   class LuckPillar(BaseModel):
       age: int
       stem: str
       branch: str
       pillar: str
       ten_god: str
       lifecycle: str

   class LuckPillarsResult(BaseModel):
       pillars: List[LuckPillar]
   ```

**Estimate**: 7 days (2 days 60-cycle data + 5 days implementation + integration with lifecycle/ten gods)

---

### 🔴 5. Yongshin Calculation (用神)

#### Codex Status: PARTIAL (10%)
**What exists:**
- 🟡 `saju_codex_addendum_v2/policies/climate_map_v1.json`
  - Maps each branch × segment (初中末) to temp/humid
  - Example:
    ```json
    {
      "寅": {
        "초": {"temp": "cool", "humid": "neutral"},
        "중": {"temp": "mild", "humid": "neutral"},
        "말": {"temp": "mild", "humid": "dry"}
      }
    }
    ```
  - Related to 조후용신 (climate-based yongshin)
  - BUT: No actual yongshin decision logic

**What's missing:**
- ❌ No yongshin criteria/decision tree
- ❌ No yongshin type definitions (억부/조후/통관/병약)
- ❌ No element selection logic based on strength + elements + climate

#### Codebase Status: PARTIAL (5%)
**What exists:**
- 🟡 Climate evaluation in `services/analysis-service/app/core/climate.py`:
  - Provides temp/humid bias per month
  - Line 43: `"advice_bucket": []  # placeholder for future advice mapping`
  - Very basic, not connected to element recommendation

**What's missing:**
- ❌ No yongshin calculator module
- ❌ No logic to determine yongshin type
- ❌ No element selection algorithm

**Result:** Climate data exists but no yongshin logic

#### What's Needed:
1. **Create policy file**: `saju_codex_batch_all_v2_6_signed/policies/yongshin_criteria.json`
   ```json
   {
     "decision_tree": {
       "strong_day_master": {
         "condition": "strength >= 60",
         "elements_needed": ["財", "官", "食傷"],
         "types": ["억부용신"]
       },
       "weak_day_master": {
         "condition": "strength < 60",
         "elements_needed": ["印", "比劫"],
         "types": ["억부용신"]
       },
       "cold_climate": {
         "condition": "temp == cold",
         "elements_needed": ["火"],
         "types": ["조후용신"]
       }
     }
   }
   ```

2. **Create calculator**: `services/analysis-service/app/core/yongshin.py`
   ```python
   class YongshinCalculator:
       def calculate(
           self,
           strength: StrengthDetails,
           elements: ElementsDistribution,
           climate: ClimateResult
       ) -> YongshinResult:
           # Decision tree logic
           # Determine primary element
           # Determine yongshin type
   ```

3. **Add response model**:
   ```python
   class YongshinResult(BaseModel):
       primary_element: str
       yongshin_type: str
       recommendation: str
   ```

**Estimate**: 5 days (2 days policy research + 3 days implementation)

---

### 🟡 6. Divine Stars (十二神殺) - Shensha

#### Codex Status: PARTIAL (30%)
**What exists:**
- ✅ `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
  - Contains 4 divine stars:
    - 桃花 (Taohua)
    - 文昌 (Wenchang)
    - 天乙貴人 (Tianyiguiren)
    - 驛馬 (Yima)
  - Each star has:
    - `name`, `key`, `desc_modern`
    - `where_rule` (text description, not structured data)
  - Example:
    ```json
    {
      "name": "桃花(도화)",
      "key": "taohua",
      "desc_modern": "표현/매력 강조, 대인 주목도 상승",
      "where_rule": "日支 in {子午卯酉} → 桃花"
    }
    ```

**What's missing:**
- ❌ Catalog incomplete (~20+ more stars needed)
- ❌ No structured mapping tables (only text rules)
- ❌ No auspicious vs inauspicious classification
- ❌ No per-pillar assignment logic

#### Codebase Status: PARTIAL (10%)
**What exists:**
- ✅ Shensha catalog loader in `services/analysis-service/app/core/school.py`
  - Function: `ShenshaCatalog.list_enabled() -> List[object]`
  - Returns basic list only
  - No per-pillar mapping

**What's missing:**
- ❌ No mapping function to assign stars to specific pillars
- ❌ No auspicious/inauspicious separation in response

#### What's Needed:
1. **Expand policy file**: `saju_codex_addendum_v2/policies/shensha_catalog_v1.json`
   - Add ~20 more divine stars
   - Convert `where_rule` text to structured mappings
   - Add classification field

2. **Extend calculator** in `services/analysis-service/app/core/school.py`:
   ```python
   class ShenshaCatalog:
       def map_to_pillars(self, pillars: ParsedPillars) -> Dict[str, List[str]]:
           # Return {"year": ["桃花", "驛馬"], "month": [...], ...}
   ```

3. **Update response model**:
   ```python
   class ShenshaResult(BaseModel):
       enabled: bool
       list: List[object]
       auspicious: List[str] = Field(default_factory=list)
       inauspicious: List[str] = Field(default_factory=list)
       per_pillar: Dict[str, List[str]] = Field(default_factory=dict)
   ```

**Estimate**: 3 days (1 day expand catalog + 2 days mapping logic)

---

### ✅ 7. Hidden Stems Display

#### Codex Status: COMPLETE (100%)
**What exists:**
- ✅ `rulesets/zanggan_table.json` - Complete table with all 12 branches
  - Primary, secondary, tertiary stems
  - Source: SKY_LIZARD Fortune App v10.4
  - Example:
    ```json
    {
      "子": ["壬", "癸"],
      "丑": ["癸", "辛", "己"],
      "寅": ["戊", "丙", "甲"],
      ...
    }
    ```

#### Codebase Status: PARTIAL (50%)
**What exists:**
- ✅ Hidden stems extraction - COMPLETE:
  - File: `services/analysis-service/app/core/engine.py` (lines 141-147)
  - Function: `_extract_hidden_stems(branches) -> List[str]`
  - Currently used for root/seal calculation

**What's missing:**
- ❌ No UI-ready display format
- ❌ Hidden stems not returned in API response
- ❌ No response model for hidden stems per pillar

#### What's Needed:
1. **Modify existing method** to return structured data:
   ```python
   def _extract_hidden_stems_by_pillar(self, branches: List[str]) -> Dict[str, List[str]]:
       return {
           "year": ZANGGAN_TABLE.get(branches[0], []),
           "month": ZANGGAN_TABLE.get(branches[1], []),
           "day": ZANGGAN_TABLE.get(branches[2], []),
           "hour": ZANGGAN_TABLE.get(branches[3], [])
       }
   ```

2. **Add response model**:
   ```python
   class HiddenStemsResult(BaseModel):
       year: List[str]
       month: List[str]
       day: List[str]
       hour: List[str]
   ```

3. **Add to API response**

**Estimate**: 1 day (simple refactor, all data exists)

---

## EXISTING CODEX ASSETS (CAN BE USED IMMEDIATELY)

### ✅ Fully Complete & Production-Ready

1. **Strength Evaluation**
   - File: `saju_codex_batch_all_v2_6_signed/policies/strength_adjust_v1_3.json`
   - Contains: Seasonal state weights, grading tiers, month stem adjust
   - Status: Currently in use in codebase

2. **Root/Seal Policy**
   - File: `saju_codex_batch_all_v2_6_signed/policies/root_seal_policy_v2_3.json`
   - Contains: Scoring rules, month bonus, validity checks
   - Status: Currently in use in codebase

3. **Relations Policy**
   - File: `saju_codex_batch_all_v2_6_signed/policies/relation_aggregate_policy_v1.json`
   - Contains: All 6 relation types, priority order, weights
   - Status: Currently in use in codebase

4. **Structure Detection**
   - File: `saju_codex_batch_all_v2_6_signed/policies/structure_rules_v2_6.json`
   - Contains: Structure definitions, thresholds
   - Status: Currently in use in codebase

5. **Seasonal Wang Map**
   - File: `saju_codex_batch_all_v2_6_signed/policies/seasons_wang_map_v2.json`
   - Contains: Element states per branch (旺相休囚死)
   - Status: Currently in use in codebase

6. **Zanggan Table**
   - File: `rulesets/zanggan_table.json`
   - Contains: All 12 branches with hidden stems
   - Status: Currently in use in codebase

7. **Relation Transform Rules**
   - File: `saju_codex_addendum_v2/policies/relation_transform_rules.json`
   - Contains: Sanhe/Sanhui transformation logic
   - Status: Currently in use in codebase

---

## PRIORITY IMPLEMENTATION ROADMAP

### P0 - CRITICAL (Missing Features)

| Feature | Codex Data | Code Status | Files to Create | Days |
|---------|------------|-------------|-----------------|------|
| **12 Lifecycle Stages** | 0% | 0% | `policies/lifecycle_stages.json`<br>`app/core/lifecycle.py`<br>Response model | 5 |
| **Five Elements Distribution** | 0% | 5% | `policies/elements_distribution_criteria.json`<br>`app/core/elements.py`<br>Response model | 3 |
| **Ten Gods for Branches** | N/A | 15% | Modify existing engine.py<br>Update response model | 2 |
| **Luck Pillars Generation** | 40% | 20% | `rulesets/sixty_jiazi.json`<br>Extend luck.py<br>Response models | 7 |

**Total P0**: ~17 days

### P1 - IMPORTANT (Partially Exists)

| Feature | Codex Data | Code Status | Files to Create | Days |
|---------|------------|-------------|-----------------|------|
| **Yongshin Calculation** | 10% | 5% | `policies/yongshin_criteria.json`<br>`app/core/yongshin.py`<br>Response model | 5 |
| **Shensha Per-Pillar Mapping** | 30% | 10% | Expand shensha_catalog_v1.json<br>Extend school.py<br>Update response model | 3 |
| **Hidden Stems Display** | 100% | 50% | Modify engine.py<br>Add response model | 1 |

**Total P1**: ~9 days

### P2 - NICE TO HAVE

| Feature | Days |
|---------|------|
| Year/Month Luck | 8 |
| Daily Calendar | 5 |
| Pillar Labels | 2 |

**Total P2**: ~15 days

---

## TOTAL EFFORT ESTIMATE

- **MVP (P0 only)**: ~17 days
- **Complete (P0 + P1)**: ~26 days
- **Full Parity (P0 + P1 + P2)**: ~41 days

---

## FILES TO CREATE

### New Policy Files (Codex)
1. `saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json` - 120 mappings
2. `saju_codex_batch_all_v2_6_signed/policies/elements_distribution_criteria.json` - Thresholds
3. `saju_codex_batch_all_v2_6_signed/policies/yongshin_criteria.json` - Decision tree
4. `rulesets/sixty_jiazi.json` - 60-stem cycle

### New Code Files
1. `services/analysis-service/app/core/lifecycle.py` - Lifecycle calculator
2. `services/analysis-service/app/core/elements.py` - Elements calculator
3. `services/analysis-service/app/core/yongshin.py` - Yongshin calculator

### Files to Modify
1. `services/analysis-service/app/core/engine.py` - Integrate new calculators
2. `services/analysis-service/app/core/luck.py` - Add pillar generation
3. `services/analysis-service/app/core/school.py` - Extend shensha mapping
4. `services/analysis-service/app/models/analysis.py` - Add all new response models
5. `saju_codex_addendum_v2/policies/shensha_catalog_v1.json` - Expand catalog

---

## REUSABLE PATTERNS FROM EXISTING CODE

### Pattern 1: Policy-Driven Calculator
```python
# Example: services/analysis-service/app/core/strength.py
class StrengthEvaluator:
    def __init__(self, policy_path: Path):
        with policy_path.open("r", encoding="utf-8") as f:
            self.policy = json.load(f)

    def evaluate(self, ...) -> StrengthDetails:
        # Use self.policy for all decisions
```

**Apply to:** Lifecycle, Elements, Yongshin calculators

### Pattern 2: Static Table Lookup
```python
# Example: services/analysis-service/app/core/engine.py
ZANGGAN_TABLE = json.load(open("rulesets/zanggan_table.json"))

def _extract_hidden_stems(self, branches: List[str]) -> List[str]:
    hidden = []
    for branch in branches:
        if branch in ZANGGAN_TABLE:
            hidden.extend(ZANGGAN_TABLE[branch])
    return hidden
```

**Apply to:** Lifecycle stages lookup, 60-stem cycle

### Pattern 3: Response Model with Pydantic
```python
# Example: services/analysis-service/app/models/analysis.py
class StrengthDetails(BaseModel):
    month_state: int
    branch_root: int
    total: float
    grade_code: str
```

**Apply to:** All new result models (LifecycleResult, ElementsDistribution, etc.)

---

## CONCLUSION

### What We Can Use from Codex
- ✅ 7 complete policy files (strength, relations, structure, root/seal, zanggan, etc.)
- 🟡 2 partial policy files (luck direction 40%, shensha catalog 30%)
- ✅ All existing policy files are high quality and production-ready

### What Needs to Be Created
- 🔴 4 critical policy files (lifecycle, elements, yongshin, 60-cycle)
- 🔴 3 critical calculators (lifecycle, elements, yongshin)
- 🟡 3 partial implementations to complete (ten gods branches, luck pillars, hidden stems display)

### Recommended Next Steps
1. Create `lifecycle_stages.json` policy (research traditional tables)
2. Create `sixty_jiazi.json` data file (standard, can copy from references)
3. Create `elements_distribution_criteria.json` policy (simple thresholds)
4. Implement lifecycle calculator (straightforward table lookup)
5. Implement elements distribution calculator (counting + labeling)
6. Extend luck calculator for pillar generation
7. Research and create `yongshin_criteria.json` (most complex)

---

**Report Complete**: 2025-10-04
**Directories Scanned**: 3 (codex batch, codex addendum, rulesets)
**Code Files Scanned**: 40+
**Policy Files Analyzed**: 26
**Reusable Assets**: 7 complete, 2 partial
**New Assets Needed**: 4 policies, 3 calculators, 7 model updates
