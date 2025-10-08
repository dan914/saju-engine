# Missing Features Report: Critical Gaps

**Date**: 2025-10-04
**Status**: Based on gap analysis vs premium Saju service
**Scope**: Features missing from codebase (not just placeholders)

---

## 🔴 CRITICAL: 12 Lifecycle Stages (十二運星)

### What's Missing
**Status**: 0% implemented - COMPLETELY MISSING

**Required Components**:
1. **Policy File**: `rulesets/lifecycle_stages.json`
   - Lookup table mapping day stem to lifecycle stage per branch
   - 10 stems × 12 branches = 120 mappings
   - Stage names: 長生, 沐浴, 冠帶, 臨官, 帝旺, 衰, 病, 死, 墓, 絕, 胎, 養
   - Korean names: 장생, 목욕, 관대, 임관, 제왕, 쇠, 병, 사, 묘, 절, 태, 양

2. **Core Module**: `services/analysis-service/app/core/lifecycle.py`
   - LifecycleCalculator class
   - Method: `calculate(day_stem: str, branches: List[str]) -> Dict[str, str]`
   - Returns: `{"year": "목욕", "month": "사", "day": "절", "hour": "관대"}`

3. **Response Model**: `services/analysis-service/app/models/analysis.py`
   - New model: `LifecycleResult(BaseModel)`
   - Fields: `year: str, month: str, day: str, hour: str`
   - Add to `AnalysisResponse`: `lifecycle: LifecycleResult`

4. **Integration**: `services/analysis-service/app/core/engine.py`
   - Import LifecycleCalculator
   - Call in `analyze()` method
   - Add to response

**Example Premium Report Output**:
```
12운성
목욕 (bath)
사 (death)
절 (extinction)
관대 (official belt)
```

**Why Critical**: Core traditional Saju feature, expected by all users

---

## 🔴 CRITICAL: Five Elements Distribution (五行分析)

### What's Missing
**Status**: 0% implemented - COMPLETELY MISSING

**Required Components**:
1. **Core Module**: `services/analysis-service/app/core/elements.py`
   - ElementsCalculator class
   - Method: `calculate_distribution(pillars: ParsedPillars, hidden_stems: List[str]) -> ElementsDistribution`
   - Count elements from:
     - 4 heavenly stems (year/month/day/hour)
     - 4 earthly branches (converted to element)
     - Hidden stems (藏干)
   - Calculate percentages
   - Assign labels: 발달 (developed), 적정 (appropriate), 과다 (excessive), 부족 (deficient)

2. **Response Model**: Add to `services/analysis-service/app/models/analysis.py`
   ```python
   class ElementsDistribution(BaseModel):
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
   ```
   - Add to `AnalysisResponse`: `elements: ElementsDistribution`

3. **Policy File**: `rulesets/elements_criteria.json`
   - Thresholds for labels:
     ```json
     {
       "thresholds": {
         "excessive": 35.0,
         "developed": 25.0,
         "appropriate": 15.0,
         "deficient": 10.0
       }
     }
     ```

**Example Premium Report Output**:
```
오행
목(木)    25.0% 발달
화(火)    12.5% 적정
토(土)    12.5% 적정
금(金)    37.5% 과다
수(水)    12.5% 적정
```

**Why Critical**: Users expect to see element balance, affects recommendations

---

## 🔴 CRITICAL: Ten Gods for Branches (地支十神)

### What's Missing
**Status**: 0% implemented - Have for stems only

**Required Components**:
1. **Extend Existing**: `services/analysis-service/app/core/engine.py`
   - Modify `_calculate_ten_gods()` method
   - For each branch:
     - Extract hidden stems from branch
     - Calculate Ten God for primary hidden stem
     - Add to result

2. **Response Model**: Modify `TenGodsResult` in `analysis.py`
   ```python
   class TenGodsResult(BaseModel):
       summary: dict[str, str]  # Existing: year/month/day/hour stems
       branches: dict[str, str] = Field(default_factory=dict)  # NEW
       # branches = {"year": "정재", "month": "상관", ...}
   ```

3. **Use Existing**: Already have hidden stems extractor
   - `_extract_hidden_stems()` returns all hidden stems
   - Need to map to branch positions

**Example Premium Report Output**:
```
천간        십성      지지        십성
신辛        편관      사巳        상관
을乙        비견      해亥        정인
을乙        비견      유酉        편관
경庚        정관      진辰        정재
```

**Why Critical**: Incomplete Ten Gods display, missing 50% of data

---

## 🔴 CRITICAL: Luck Pillars Generation (大運)

### What's Missing
**Status**: 10% implemented - Only have start age

**Existing**:
- `LuckResult` has `start_age: float | None`
- `luck_direction` has direction (forward/backward)

**Required Components**:
1. **Core Module**: `services/analysis-service/app/core/luck.py`
   - Modify existing `LuckCalculator` class
   - New method: `generate_luck_pillars(month_pillar: str, direction: str, start_age: float, count: int = 10) -> List[LuckPillar]`
   - Algorithm:
     - Start from month pillar
     - Move forward or backward through 60-stem cycle
     - Generate 10 periods (each 10 years)
     - Calculate Ten Gods for each luck pillar
     - Calculate lifecycle stage for each luck pillar

2. **Response Model**: Add to `analysis.py`
   ```python
   class LuckPillar(BaseModel):
       age: int  # Starting age (8, 18, 28, ...)
       stem: str  # 병, 정, 무, ...
       branch: str  # 묘, 술, 사, ...
       pillar: str  # 병묘, 정술, 무사, ...
       ten_god: str  # 상관, 식신, 정재, ...
       lifecycle: str  # 목욕, 사, 절, ...

   class LuckPillarsResult(BaseModel):
       pillars: List[LuckPillar]
   ```
   - Add to `AnalysisResponse`: `luck_pillars: LuckPillarsResult`

3. **Policy File**: Already have 60-stem cycle data
   - May need: `rulesets/sixty_jiazi.json` for cycle

**Example Premium Report Output**:
```
대운수: 8(을유)
대운
8   상관 병丙 묘卯 목욕 정재
18  식신 정丁 술戌 사   정인
28  정재 무戊 사巳 절   병인
38  편재 기己 해亥 관대 편관
...
```

**Why Critical**: Major feature gap, users expect 10-year fortune periods

---

## 🟡 HIGH: Hidden Stems Display per Branch

### What's Missing
**Status**: 50% implemented - Backend only

**Existing**:
- `_extract_hidden_stems()` returns flat list: `["무", "경", "병", ...]`
- Not exposed in response model

**Required**:
1. **Modify Method**: `services/analysis-service/app/core/engine.py`
   - Change `_extract_hidden_stems()` to return structured data:
   ```python
   def _extract_hidden_stems(self, branches: List[str]) -> Dict[str, List[str]]:
       return {
           "year_branch": ["무", "경", "병"],
           "month_branch": ["무", "갑", "임"],
           # ...
       }
   ```

2. **Response Model**: Add to `analysis.py`
   ```python
   class HiddenStemsResult(BaseModel):
       year: List[str]
       month: List[str]
       day: List[str]
       hour: List[str]
   ```
   - Add to `AnalysisResponse`: `hidden_stems: HiddenStemsResult`

**Example Premium Report Output**:
```
지장간
사巳: 무경병
해亥: 무갑임
유酉: 경신
진辰: 을계무
```

---

## 🟡 HIGH: Yongshin Calculation Logic (用神)

### What's Missing
**Status**: 20% implemented - Only placeholder guard

**Existing**:
- `RecommendationGuard.decide()` enables/disables recommendation
- No actual yongshin logic

**Required Components**:
1. **Core Module**: `services/analysis-service/app/core/yongshin.py`
   - YongshinCalculator class
   - Method: `calculate(strength: str, elements: ElementsDistribution, ten_gods: TenGodsResult) -> YongshinResult`
   - Logic:
     - If 신강 (strong): Need 財/官/食傷 (draining elements)
     - If 신약 (weak): Need 印/比劫 (supporting elements)
     - Determine yongshin type: 억부용신, 조후용신, 통관용신, etc.

2. **Response Model**: Add to `analysis.py`
   ```python
   class YongshinResult(BaseModel):
       primary_element: str  # 수, 화, 목, 금, 토
       yongshin_type: str  # 억부용신, 조후용신, etc.
       recommendation: str  # Human-readable explanation
   ```
   - Add to `AnalysisResponse`: `yongshin: YongshinResult`

3. **Policy File**: `rulesets/yongshin_criteria.json`
   - Decision tree for yongshin selection
   - Type definitions

**Example Premium Report Output**:
```
용신: 수(억부용신)
```

---

## 🟡 MEDIUM: Divine Stars Per-Pillar Mapping (十二神殺)

### What's Missing
**Status**: 10% implemented - Have catalog, no mapping

**Existing**:
- `ShenshaCatalog.list_enabled()` returns basic list

**Required**:
1. **Extend Module**: `services/analysis-service/app/core/school.py`
   - Modify `ShenshaCatalog` class
   - Add method: `map_to_pillars(pillars: ParsedPillars) -> Dict[str, List[str]]`
   - Use policy files to map stars to year/month/day/hour

2. **Response Model**: Modify `ShenshaResult` in `analysis.py`
   ```python
   class ShenshaResult(BaseModel):
       enabled: bool
       list: List[object]  # Existing
       auspicious: List[str] = Field(default_factory=list)  # NEW
       inauspicious: List[str] = Field(default_factory=list)  # NEW
       per_pillar: Dict[str, List[str]] = Field(default_factory=dict)  # NEW
   ```

3. **Policy Files**: Already exist in `saju_codex_batch_all_v2_6_signed/policies/`
   - Use existing shensha policy files

---

## 🟢 LOWER PRIORITY: Year/Month Luck (年運/月運)

### What's Missing
**Status**: 0% implemented

**Required**: Similar to Luck Pillars but for:
- Year luck: Generate yearly pillars from current year forward
- Month luck: Generate monthly pillars for current year

**Effort**: 3-5 days each after Luck Pillars implemented

---

## 🟢 LOWER PRIORITY: Daily Calendar (日進 달력)

### What's Missing
**Status**: 0% implemented

**Required**:
- Generate daily pillars for a given month
- Mark auspicious/inauspicious days
- Calculate Ten Gods per day

**Effort**: 3-5 days, not blocking basic service

---

## 🟢 LOWER PRIORITY: Pillar Life Stage Labels

### What's Missing
**Status**: 0% implemented

**Required**:
- Add interpretive labels to pillars:
  - Year = 조상/시대상 (ancestors/era)
  - Month = 부모/사회상 (parents/society)
  - Day = 자아/배우자 (self/spouse)
  - Hour = 자녀/결실 (children/results)
- Also: 초년운/청년운/중년운/말년운 (early/youth/middle/late life)

**Effort**: 1-2 days, display only

---

## Summary: Implementation Priority

### P0 - BLOCKING (Must Have)
1. ✅ **12 Lifecycle Stages** - 0% → Estimated 5 days
2. ✅ **Five Elements Distribution** - 0% → Estimated 3 days
3. ✅ **Ten Gods for Branches** - 0% → Estimated 2 days
4. ✅ **Luck Pillars Generation** - 10% → Estimated 7 days

**Total P0**: ~17 days work

### P1 - IMPORTANT (Should Have)
5. ✅ **Hidden Stems Display** - 50% → Estimated 2 days
6. ✅ **Yongshin Logic** - 20% → Estimated 5 days
7. ✅ **Shensha Mapping** - 10% → Estimated 3 days

**Total P1**: ~10 days work

### P2 - NICE TO HAVE (Could Have)
8. Year/Month Luck - 0% → Estimated 8 days
9. Daily Calendar - 0% → Estimated 5 days
10. Pillar Labels - 0% → Estimated 2 days

**Total P2**: ~15 days work

---

## Files That Need Creation

### New Files Required
1. `services/analysis-service/app/core/lifecycle.py` - 12 lifecycle stages calculator
2. `services/analysis-service/app/core/elements.py` - Five elements distribution
3. `services/analysis-service/app/core/yongshin.py` - Yongshin recommendation logic
4. `rulesets/lifecycle_stages.json` - Lifecycle lookup table (120 mappings)
5. `rulesets/elements_criteria.json` - Element balance thresholds
6. `rulesets/yongshin_criteria.json` - Yongshin decision tree
7. `rulesets/sixty_jiazi.json` - 60-stem cycle (if not exists)

### Files That Need Modification
1. `services/analysis-service/app/core/engine.py` - Integrate new calculators
2. `services/analysis-service/app/core/luck.py` - Add luck pillar generation
3. `services/analysis-service/app/core/school.py` - Extend shensha mapping
4. `services/analysis-service/app/models/analysis.py` - Add new response models
5. `services/analysis-service/app/models/__init__.py` - Export new models

---

## Existing Assets (Can Be Reused)

### Already Have
- ✅ Pillar parsing logic
- ✅ Ten Gods calculation (for stems)
- ✅ Hidden stems extraction (藏干)
- ✅ Relations detection (all 6 types)
- ✅ Strength evaluation framework
- ✅ Policy-driven architecture
- ✅ Zanggan table (rulesets/zanggan_table.json)
- ✅ Test infrastructure

### Can Build On
- Element knowledge embedded in Ten Gods calculator
- Existing luck calculator (has start age, direction)
- Existing shensha catalog
- Policy file loading patterns

---

**Report Complete**: 2025-10-04
**Total Critical Features Missing**: 4 (P0)
**Estimated Effort for MVP**: 17 days
**Estimated Effort for Full Parity**: 42 days
