# ENGINE USAGE AUDIT

**Date**: 2025-10-06
**Scope**: Complete codebase scan for all engines, calculators, and execution flows

---

## EXECUTIVE SUMMARY

This codebase contains a Saju (Korean Four Pillars of Destiny) calculation engine split across multiple microservices. Key findings:

- **Two parallel pillars calculation systems** (one in scripts/, one in services/)
- **12 active engines** in analysis-service
- **6 orphaned engines** that are fully implemented but never called
- **3 critical import issues** including services importing from scripts/
- **1 unused evaluator** (ClimateEvaluator)
- **3 code duplications** across services

---

## 1. PILLARS CALCULATION ENGINES

### 1.1 **calculate_four_pillars() [ACTIVE - PRIMARY]**
- **File**: `scripts/calculate_pillars_traditional.py`
- **Type**: Standalone function (459 lines)
- **Purpose**: Calculate Four Pillars using Traditional Korean Rules (子時 + LMT + DST)
- **Key Features**:
  - LMT (Local Mean Time) adjustment for Seoul (-32 minutes)
  - Traditional 子時 (Zi Hour) day transition rule (23:00 = next day)
  - DST handling for 1948-1960, 1987-1988
  - Refined Saju Lite astronomical solar terms (with ΔT corrections)
  - Zi hour mode toggle ('traditional' vs 'modern')
- **Called By**:
  - **PillarsEngine** (services/pillars-service/app/core/engine.py:48)
  - **TimeEventDetector** (services/tz-time-service/app/core/events.py:9)
- **Status**: **ACTIVE** - This is the canonical pillars calculator

### 1.2 **PillarsEngine [ACTIVE - WRAPPER]**
- **File**: `services/pillars-service/app/core/engine.py`
- **Class**: `PillarsEngine` (118 lines)
- **Purpose**: Service adapter that wraps calculate_four_pillars() for FastAPI
- **Imports**: `from scripts.calculate_pillars_traditional import calculate_four_pillars`
- **Called By**: API endpoint POST `/pillars/compute`
- **Status**: **ACTIVE** - Main API entry point
- **⚠️ Issue**: **CIRCULAR DEPENDENCY RISK** - Service importing from scripts/

### 1.3 **PillarsCalculator [ORPHANED]**
- **File**: `services/pillars-service/app/core/pillars.py`
- **Class**: `PillarsCalculator` (lines 75-122)
- **Purpose**: High-level calculator composing resolvers (alternative implementation)
- **Dependencies**: MonthBranchResolver, DayBoundaryCalculator, TimeResolver
- **Called By**: NONE
- **Status**: **ORPHANED** - Complete implementation but never integrated
- **Note**: Appears to be alternative/newer implementation that was abandoned

### 1.4 **Supporting Calculators [ALL ORPHANED]**

#### MonthBranchResolver
- **File**: `services/pillars-service/app/core/month.py` (lines 80-143)
- **Status**: ORPHANED - Only used by PillarsCalculator

#### DayBoundaryCalculator
- **File**: `services/pillars-service/app/core/resolve.py` (line 49)
- **Status**: ORPHANED - Only used by PillarsCalculator

#### TimeResolver
- **File**: `services/pillars-service/app/core/resolve.py` (line 13)
- **Status**: ORPHANED - Only used by PillarsCalculator and analysis-service/luck.py

#### SimpleSolarTermLoader
- **File**: `services/pillars-service/app/core/month.py` (lines 57-77)
- **Status**: ORPHANED - Only used by MonthBranchResolver

---

## 2. ANALYSIS ENGINES

### 2.1 **AnalysisEngine [ACTIVE - PRIMARY]**
- **File**: `services/analysis-service/app/core/engine.py`
- **Class**: `AnalysisEngine` (lines 69-457)
- **Purpose**: Main analysis orchestrator - applies KR_classic v1.4 ten gods/relations/strength rules
- **Sub-Engines**:
  - RelationTransformer
  - StrengthEvaluator
  - StructureDetector
  - LuckCalculator
  - ShenshaCatalog
  - RecommendationGuard
  - SchoolProfileManager
- **Called By**: API endpoint POST `/analyze`
- **Status**: **ACTIVE**

### 2.2 **Sub-Engines (Analysis Service)**

#### RelationTransformer [ACTIVE]
- **File**: `services/analysis-service/app/core/relations.py` (lines 51-214)
- **Purpose**: Evaluate relation transformations (sanhe, banhe, chong, xing, po, hai)
- **Policies**: relation_policy v2, v2.1, v2.5
- **Called By**: AnalysisEngine.analyze():371
- **Status**: **ACTIVE**

#### StrengthEvaluator [ACTIVE]
- **File**: `services/analysis-service/app/core/strength.py` (lines 64-434)
- **Purpose**: Evaluate day master strength using strength_adjust_v1_3.json
- **Components**: WangStateMapper, Root/seal scoring, Wealth bonus, Seal validity
- **Called By**: AnalysisEngine.analyze():396
- **Status**: **ACTIVE**

#### StructureDetector [ACTIVE]
- **File**: `services/analysis-service/app/core/structure.py` (lines 34-107)
- **Purpose**: Detect primary structure (격국) from Ten Gods scores
- **Policies**: v2.6 (preferred) → v2.5 → v1
- **Called By**: AnalysisEngine.analyze():421
- **Status**: **ACTIVE**

#### LuckCalculator [ACTIVE]
- **File**: `services/analysis-service/app/core/luck.py` (lines 65-114)
- **Purpose**: Calculate luck pillar start age and direction
- **Dependencies**: Imports from pillars-service via importlib.util workaround
- **Called By**: AnalysisEngine.analyze():431-432
- **Status**: **ACTIVE**
- **⚠️ Issue**: **CROSS-SERVICE IMPORT** using hacky importlib workaround

#### ShenshaCatalog [ACTIVE]
- **File**: `services/analysis-service/app/core/luck.py` (lines 116-124)
- **Purpose**: List enabled shensha (神煞) from catalog
- **Called By**: AnalysisEngine.analyze():433
- **Status**: **ACTIVE**

#### RecommendationGuard [ACTIVE]
- **File**: `services/analysis-service/app/core/recommendation.py` (lines 19-38)
- **Purpose**: Enforce recommendation policy based on structure detection
- **Called By**: AnalysisEngine.analyze():440, LLMGuard.postprocess():60
- **Status**: **ACTIVE**

#### SchoolProfileManager [ACTIVE]
- **File**: `services/analysis-service/app/core/school.py` (lines 14-29)
- **Purpose**: Load school profiles from policy
- **Called By**: AnalysisEngine.analyze():443
- **Status**: **ACTIVE**

#### ClimateEvaluator [UNUSED]
- **File**: `services/analysis-service/app/core/climate.py` (lines 26-45)
- **Purpose**: Evaluate climate bias (temp/humidity) from month branch
- **Called By**: NONE
- **Status**: **UNUSED** - Defined but never instantiated

---

## 3. LLM GUARD & ENRICHMENT

### LLMGuard [ACTIVE]
- **File**: `services/analysis-service/app/core/llm_guard.py` (lines 15-69)
- **Purpose**: JSON validation and post-processing for LLM workflow
- **Sub-components**: TextGuard, RecommendationGuard, KoreanLabelEnricher
- **Called By**: API endpoint POST `/analyze`:32
- **Status**: **ACTIVE**

### KoreanLabelEnricher [ACTIVE]
- **File**: `services/analysis-service/app/core/korean_enricher.py` (lines 28-342)
- **Purpose**: Enrich payloads with Korean labels (141 mappings)
- **Policies**: localization_ko_v1.json, gyeokguk_policy.json, shensha_v2_policy.json, sixty_jiazi.json
- **Called By**: LLMGuard.prepare_payload():36
- **Status**: **ACTIVE**

### TextGuard [ACTIVE]
- **File**: `services/analysis-service/app/core/text_guard.py` (lines 19-49)
- **Purpose**: Filter forbidden terms and append policy notes
- **Called By**: LLMGuard.postprocess():57
- **Status**: **ACTIVE**

### Policy Guards [ACTIVE - VALIDATION]
- **policy_guards.py**: Runtime validation for elements distribution
- **policy_guards_luck.py**: Runtime validation for luck pillars
- **Status**: **ACTIVE** - Used for validation

---

## 4. PILLARS-SERVICE ORPHANED CODE

### StrengthEvaluator (pillars-service) [ORPHANED]
- **File**: `services/pillars-service/app/core/strength.py` (lines 233-315)
- **Purpose**: Alternative strength evaluator
- **Note**: **DUPLICATE** of analysis-service strength evaluator
- **Called By**: NONE
- **Status**: **ORPHANED**

### RootSealScorer (pillars-service) [ORPHANED]
- **File**: `services/pillars-service/app/core/strength.py` (lines 28-230)
- **Purpose**: Score roots/seal strength
- **Called By**: StrengthEvaluator (which is orphaned)
- **Status**: **ORPHANED**

---

## 5. OTHER SERVICES

### Astro Service [ACTIVE]
- **SolarTermService**: `services/astro-service/app/core/service.py` (lines 19-58)
- **SolarTermLoader**: `services/astro-service/app/core/loader.py`
- **Status**: **ACTIVE**

### TZ-Time Service [ACTIVE]
- **TimezoneConverter**: `services/tz-time-service/app/core/converter.py` (lines 23-54)
- **TimeEventDetector**: `services/tz-time-service/app/core/events.py` (line 18)
  - ⚠️ Imports from scripts: `from scripts.calculate_pillars_traditional import apply_traditional_adjustments`
- **Status**: **ACTIVE**

---

## 6. EXECUTION FLOWS

### Pillars Calculation Flow (ACTIVE)
```
API Request → POST /pillars/compute
    ↓
PillarsEngine (pillars-service/app/core/engine.py)
    ↓
calculate_four_pillars() (scripts/calculate_pillars_traditional.py)
    ↓
- Apply DST adjustments
- Apply LMT adjustments (-32 min for Seoul)
- Apply 子時 transition rule
- Load solar terms from data/canonical/canonical_v1/
- Calculate year/month/day/hour pillars
    ↓
Return PillarsComputeResponse
```

### Analysis Flow (ACTIVE)
```
API Request → POST /analyze
    ↓
AnalysisEngine.analyze() (analysis-service/app/core/engine.py)
    ↓
- Parse pillars → Ten Gods calculation (inline)
- RelationTransformer.evaluate() → Relations
- StrengthEvaluator.evaluate() → Strength
- StructureDetector.evaluate() → Structure
- LuckCalculator.compute_start_age() → Luck
- ShenshaCatalog.list_enabled() → Shensha
- RecommendationGuard.decide() → Recommendation
- SchoolProfileManager.get_profile() → School profile
    ↓
LLMGuard.prepare_payload() → Korean enrichment
    ↓
LLMGuard.postprocess() → Validation & guards
    ↓
Return AnalysisResponse
```

### Orphaned Flow (NEVER EXECUTED)
```
[NOT USED]
    ↓
PillarsCalculator (pillars-service/app/core/pillars.py)
    ↓
- MonthBranchResolver.resolve()
- DayBoundaryCalculator.compute()
- TimeResolver.resolve()
    ↓
[NEVER CALLED]
```

---

## 7. CRITICAL ISSUES

### 7.1 Import Issues

#### ⚠️ Issue 1: PillarsEngine imports from scripts/
```python
# services/pillars-service/app/core/engine.py:11
from scripts.calculate_pillars_traditional import calculate_four_pillars
```
- **Problem**: Service depends on scripts/ folder
- **Risk**: Circular dependency, deployment issues
- **Impact**: HIGH - Core functionality

#### ⚠️ Issue 2: TimeEventDetector imports from scripts/
```python
# services/tz-time-service/app/core/events.py:9
from scripts.calculate_pillars_traditional import apply_traditional_adjustments
```
- **Problem**: Service depends on scripts/ folder
- **Impact**: MEDIUM - DST detection

#### ⚠️ Issue 3: LuckCalculator hacky cross-service import
```python
# services/analysis-service/app/core/luck.py:14-48
import importlib.util
# Creates fake package to import from pillars-service
```
- **Problem**: Uses importlib.util workaround
- **Risk**: Fragile, breaks package structure
- **Impact**: MEDIUM - Luck calculation

### 7.2 Code Duplication

1. **StrengthEvaluator** duplicated:
   - `services/pillars-service/app/core/strength.py` (orphaned)
   - `services/analysis-service/app/core/strength.py` (active)

2. **LuckCalculator** duplicated:
   - `services/pillars-service/app/core/evidence.py` (stub)
   - `services/analysis-service/app/core/luck.py` (active)

3. **TimeResolver** duplicated:
   - `services/pillars-service/app/core/resolve.py` (orphaned)
   - Used via hacky import by analysis-service

---

## 8. SCRIPTS ANALYSIS

**Total**: 45 Python scripts in `/scripts/`

**Key Scripts**:
- `calculate_pillars_traditional.py` - PRIMARY calculator (imported by services)
- `calculate_user_saju.py` - User-facing script
- 11 test scripts (test_*.py)
- 5 debug scripts (debug_*.py)
- 8 comparison scripts (compare_*.py)
- 7 data generation scripts (generate_*.py, extrapolate_*.py)

**Status**: Only `calculate_pillars_traditional.py` is imported by services, rest are utilities.

---

## 9. RECOMMENDATIONS

### 9.1 Critical - Architecture

1. **MOVE scripts/calculate_pillars_traditional.py into pillars-service**
   - Eliminate service→scripts dependency
   - Make it `services/pillars-service/app/core/calculator.py`
   - Update imports in PillarsEngine and TimeEventDetector

2. **REMOVE or ACTIVATE PillarsCalculator**
   - Decision: Keep old system or migrate to new?
   - If new: Migrate API to use PillarsCalculator
   - If old: Delete pillars.py, month.py, resolve.py, canonical_calendar.py

3. **FIX cross-service imports in LuckCalculator**
   - Extract shared utilities to `services/common/`
   - Remove importlib.util hack

### 9.2 Code Cleanup

1. **DELETE orphaned engines** (if confirmed unused):
   - `services/pillars-service/app/core/strength.py`
   - `services/pillars-service/app/core/evidence.py`

2. **ACTIVATE or REMOVE ClimateEvaluator**
   - If future: Document as WIP
   - If abandoned: Delete

3. **CONSOLIDATE StrengthEvaluator**
   - Only analysis-service version should exist

### 9.3 Testing

1. **VERIFY orphaned code can be deleted**
   - Check all test files
   - Grep for imports

2. **ADD integration tests**
   - Test full pillars→analysis flow

---

## 10. SUMMARY STATISTICS

| Category | Count | Status |
|----------|-------|--------|
| **Services** | 7 | 5 active |
| **Active Engines** | 12 | All in analysis-service + PillarsEngine |
| **Orphaned Engines** | 6 | Never called |
| **Unused Evaluators** | 1 | ClimateEvaluator |
| **Scripts** | 45 | 1 imported by services |
| **Import Issues** | 3 | Critical |
| **Code Duplications** | 3 | StrengthEvaluator, LuckCalculator, TimeResolver |

---

## 11. CRITICAL PATH ENGINES

**Required for system to function**:

1. **calculate_four_pillars()** - Core pillars calculation
2. **PillarsEngine** - API wrapper
3. **AnalysisEngine** - Main analysis orchestrator
4. **RelationTransformer** - Relations analysis
5. **StrengthEvaluator** (analysis-service) - Strength analysis
6. **StructureDetector** - Structure detection
7. **LuckCalculator** (analysis-service) - Luck calculation
8. **LLMGuard** - Output validation
9. **KoreanLabelEnricher** - Korean enrichment

All other engines are utilities, orphaned, or optional.

---

**End of Report**
