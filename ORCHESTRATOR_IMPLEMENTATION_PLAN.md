# Saju Analysis Orchestrator - Implementation Plan v1.0

**Date:** 2025-10-10 KST
**Purpose:** Connect Pillars → Core Engines → Stage-3 Engines
**Status:** Planning Phase

---

## Executive Summary

**Problem:** The codebase has isolated engines that work independently but lack an orchestration layer to run a complete analysis pipeline from birth data to final insights.

**Solution:** Build a `MasterOrchestrator` that sequences core analysis engines and feeds their outputs to Stage-3 engines.

**Timeline:** 2-3 days (16-24 hours of work)

---

## 1. Current State Audit

###  1.1 ✅ Working Components

| Component | File | Key Method | Input | Output |
|-----------|------|------------|-------|--------|
| **Pillars Calculator** | `scripts/calculate_pillars_traditional.py` | `calculate_four_pillars()` | birth_dt, tz_str | {year, month, day, hour, metadata} |
| **Stage-3 Wrapper** | `services/analysis-service/app/core/engine.py` | `analyze()` | context dict | {luck_flow, gyeokguk, climate_advice, pattern} |
| **Policy Loader** | `services/common/policy_loader.py` | `load_policy_json()` | filename | policy dict |

### 1.2 🟡 Core Engines (Exist, Not Orchestrated)

| Engine | File | Class | Key Method | Dependencies | Output Keys |
|--------|------|-------|------------|--------------|-------------|
| **Strength** | `strength.py` | `StrengthEvaluator` | `evaluate()` | pillars, season | strength.{level, score, phase, details} |
| **Relations** | `relations.py` | `RelationTransformer` | `evaluate()` | pillars | relations.{he6, sanhe, chong, xing, po, hai} |
| **Climate** | `climate.py` | `ClimateEvaluator` | `evaluate()` | pillars, season, strength | climate.{season, flags, balance_index} |
| **Yongshin** | `yongshin_selector.py` | `YongshinSelector` | `select()` | day_master, strength, elements, relations, climate | yongshin.{primary, secondary, confidence} |
| **Luck** | `luck.py` | `LuckCalculator` | `compute_start_age()` | pillars, birth_dt, gender | luck.{start_age, direction, pillars[]} |
| **Shensha** | `luck.py` | `ShenshaCatalog` | (embedded) | pillars | shensha.{list[]} |
| **Korean Labels** | `korean_enricher.py` | `KoreanLabelEnricher` | `enrich()` | analysis_dict | enriched dict with *_ko |
| **School Profile** | `school.py` | `SchoolProfileManager` | (simple) | - | school_profile.{id, name} |
| **Recommendation** | `recommendation.py` | `RecommendationGuard` | (filter) | yongshin, structure | filtered recommendations |

**Note:** Ten Gods calculation is embedded in `StrengthEvaluator._get_ten_gods_relation()`

### 1.3 🆕 Stage-3 Engines (Integrated, Need Context)

| Engine | File | Class | Input Context Keys Required |
|--------|------|-------|----------------------------|
| **Climate Advice** | `climate_advice.py` | `ClimateAdvice` | season, strength.phase, strength.elements, climate.flags |
| **Luck Flow** | `luck_flow.py` | `LuckFlow` | yongshin.primary, climate.balance_index, strength.elements, relation.flags, daewoon, sewoon |
| **Gyeokguk** | `gyeokguk_classifier.py` | `GyeokgukClassifier` | strength, yongshin, relations, luck_flow (from previous) |
| **Pattern** | `pattern_profiler.py` | `PatternProfiler` | strength, relations, yongshin, luck_flow, gyeokguk |
| **Relations Extras** | `relations_extras.py` | `RelationAnalyzer` | branches[], five_he_pairs, zixing_counts, conflicts |

---

## 2. Architecture Design

### 2.1 Orchestrator Class Structure

```python
class MasterOrchestrator:
    """
    Main orchestrator that runs complete analysis pipeline.

    Flow: Pillars → Core Engines → Stage-3 Engines → Korean Labels
    """

    def __init__(self):
        # Core engines
        self.strength_evaluator = StrengthEvaluator()
        self.relation_transformer = RelationTransformer()
        self.climate_evaluator = ClimateEvaluator()
        self.yongshin_selector = YongshinSelector()
        self.luck_calculator = LuckCalculator()
        self.korean_enricher = KoreanLabelEnricher()
        self.school_manager = SchoolProfileManager()
        self.recommendation_guard = RecommendationGuard()

        # Stage-3 engines
        self.stage3_engine = AnalysisEngine()  # From engine.py

        # Relations extras
        self.relation_analyzer = RelationAnalyzer()

    def analyze(self, pillars: dict, birth_context: dict) -> dict:
        """
        Run complete analysis pipeline.

        Args:
            pillars: {year, month, day, hour, metadata} from calculate_four_pillars
            birth_context: {birth_dt, gender, timezone, unknown_hour}

        Returns:
            Complete analysis result with all engines
        """
        pass  # Implementation below
```

### 2.2 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    INPUT: Birth Data                             │
│  {date: 2000-09-14, time: 10:00, tz: Asia/Seoul}                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │  calculate_four_pillars()      │
            │  庚辰年 乙酉月 癸酉日 丁巳時      │
            └────────────┬───────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────┐
    │         CORE ANALYSIS PHASE                        │
    │  (Runs in dependency order)                        │
    └────────────┬───────────────────────────────────────┘
                 │
       ┌─────────┼─────────┬─────────┬─────────┐
       │         │         │         │         │
       ▼         ▼         ▼         ▼         ▼
   ┌───────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐
   │TenGods│ │Strength│ │Season│ │Luck  │ │Shensha│
   │(십신) │ │(강약)   │ │(계절)│ │(대운)│ │(신살)│
   └───┬───┘ └───┬────┘ └───┬──┘ └───┬──┘ └───┬──┘
       │         │          │        │        │
       │    ┌────▼──────────▼────┐   │        │
       │    │  Relations (관계)   │   │        │
       │    │  육합/삼합/충/형/파   │   │        │
       │    └────────┬────────────┘   │        │
       │             │                │        │
       │    ┌────────▼────────────┐   │        │
       │    │  Climate (조후)      │   │        │
       │    │  flags, balance_index│   │        │
       │    └────────┬────────────┘   │        │
       │             │                │        │
       └─────────────┼────────────────┴────────┘
                     │
            ┌────────▼──────────┐
            │  Yongshin (용신)  │
            │  primary/secondary│
            └────────┬──────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────┐
    │         STAGE-3 ANALYSIS PHASE                     │
    │  (Runs with core context)                          │
    └────────────┬───────────────────────────────────────┘
                 │
       ┌─────────┼─────────┬─────────┬─────────┐
       │         │         │         │         │
       ▼         ▼         ▼         ▼         ▼
   ┌────────┐ ┌──────┐ ┌────────┐ ┌───────┐ ┌──────┐
   │Climate │ │Luck  │ │Gyeokguk│ │Pattern│ │Rel.  │
   │Advice  │ │Flow  │ │Classif.│ │Profile│ │Extras│
   └────┬───┘ └───┬──┘ └───┬────┘ └───┬───┘ └───┬──┘
        │         │        │          │         │
        └─────────┴────────┴──────────┴─────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Korean Label Enrich  │
              │  Add *_ko fields      │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Final Output JSON   │
              │  Complete Analysis    │
              └───────────────────────┘
```

---

## 3. Dependency Mapping

### 3.1 Engine Dependencies (Execution Order)

```
Level 0 (No dependencies):
  - Pillars (input)
  - Season extraction (from pillars.month branch)
  - Gender (input)
  - Birth datetime (input)

Level 1 (Depends on Level 0):
  - TenGods calculation (pillars.day.stem vs other stems)
  - Shensha catalog (pillars only)

Level 2 (Depends on Level 0-1):
  - Strength evaluation (pillars, season, ten_gods)
  - Relations transformation (pillars only, but outputs used by many)

Level 3 (Depends on Level 0-2):
  - Climate evaluation (pillars, season, strength)
  - Luck calculation (pillars, birth_dt, gender)

Level 4 (Depends on Level 0-3):
  - Yongshin selection (day_master, strength, relations, climate)

Level 5 (Depends on Level 0-4):
  - Stage-3 Climate Advice (season, strength.phase, strength.elements, climate.flags)
  - Stage-3 Luck Flow (yongshin, climate, strength, relations, daewoon, sewoon)

Level 6 (Depends on Level 5):
  - Stage-3 Gyeokguk (strength, yongshin, relations, luck_flow)
  - Stage-3 Pattern (strength, relations, yongshin, luck_flow, gyeokguk)
  - Relations Extras (branches, five_he_pairs from relations, zixing counts)

Level 7 (Post-processing):
  - Korean Label Enrichment (all outputs)
  - School Profile (simple, no deps)
  - Recommendation Guard (yongshin, structure)
```

### 3.2 Data Contracts (What Each Engine Needs/Produces)

#### StrengthEvaluator
**Input:**
```python
{
  "pillars": {
    "year": "庚辰",
    "month": "乙酉",
    "day": "癸酉",
    "hour": "丁巳"
  },
  "season": "가을",
  "ten_gods": {  # Optional, can calculate internally
    "year_stem": "편인",
    "month_stem": "상관",
    ...
  }
}
```

**Output:**
```python
{
  "strength": {
    "level": "신약",
    "score": 35,
    "phase": "囚",
    "details": {
      "month_state_score": -15,
      "branch_root_score": 15,
      "stem_visible_score": 5,
      ...
    }
  },
  "strength_elements": {
    "wood": "low",
    "fire": "normal",
    "earth": "normal",
    "metal": "high",
    "water": "low"
  }
}
```

#### RelationTransformer
**Input:**
```python
{
  "pillars": {
    "year": "庚辰",
    "month": "乙酉",
    "day": "癸酉",
    "hour": "丁巳"
  }
}
```

**Output:**
```python
{
  "relations": {
    "he6": [],
    "sanhe": [],
    "chong": [{"positions": ["month_branch", "day_branch"], "pair": "酉酉"}],
    "xing": [],
    "po": [],
    "hai": []
  },
  "relation_flags": ["chong"],  # For Stage-3
  "five_he_pairs": []  # For relations_extras
}
```

#### YongshinSelector
**Input:**
```python
{
  "day_master": "癸",
  "strength": {
    "level": "신약",
    "score": 35,
    "phase": "囚"
  },
  "elements_distribution": {
    "wood": "low",
    "fire": "normal",
    "earth": "normal",
    "metal": "high",
    "water": "low"
  },
  "relations": {  # From RelationTransformer
    "he6": [],
    "sanhe": [],
    "chong": [...]
  },
  "climate": {
    "season": "가을",
    "flags": [],
    "balance_index": 0
  }
}
```

**Output:**
```python
{
  "yongshin": {
    "primary": "목",
    "secondary": "화",
    "confidence": 0.8,
    "rationale": ["신약하므로 생조 필요", "목생수로 일간 지원"]
  }
}
```

---

## 4. Implementation Plan

### Phase 1: Core Orchestrator (Days 1-2)

#### Step 1.1: Create Base Orchestrator Class
**File:** `services/analysis-service/app/core/master_orchestrator.py`

```python
# -*- coding: utf-8 -*-
"""
Master Orchestrator v1.0
Connects Pillars → Core Engines → Stage-3 Engines

Usage:
    from master_orchestrator import MasterOrchestrator

    orchestrator = MasterOrchestrator()
    result = orchestrator.analyze(pillars_dict, birth_context)
"""

from typing import Dict, Any, Optional
from datetime import datetime

# Core engines
from .strength import StrengthEvaluator
from .relations import RelationTransformer
from .climate import ClimateEvaluator
from .yongshin_selector import YongshinSelector
from .luck import LuckCalculator
from .korean_enricher import KoreanLabelEnricher
from .school import SchoolProfileManager
from .recommendation import RecommendationGuard

# Stage-3 engines
from .engine import AnalysisEngine  # Stage-3 wrapper
from .relations_extras import RelationAnalyzer, RelationContext


class MasterOrchestrator:
    """Main analysis pipeline orchestrator."""

    def __init__(self):
        """Initialize all engines."""
        # Core engines
        self.strength_evaluator = StrengthEvaluator()
        self.relation_transformer = RelationTransformer()
        self.climate_evaluator = ClimateEvaluator()
        self.yongshin_selector = YongshinSelector()
        self.luck_calculator = LuckCalculator()
        self.korean_enricher = KoreanLabelEnricher.from_files()
        self.school_manager = SchoolProfileManager()
        self.recommendation_guard = RecommendationGuard()

        # Stage-3 engines
        self.stage3_engine = AnalysisEngine()
        self.relation_analyzer = RelationAnalyzer()

        # Metadata
        self.version = "master_orchestrator_v1.0"

    def analyze(self, pillars: Dict[str, Any], birth_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete analysis pipeline.

        Args:
            pillars: {year, month, day, hour, metadata} from calculate_four_pillars
            birth_context: {
                birth_dt: datetime object,
                gender: "M" or "F",
                timezone: IANA timezone string,
                unknown_hour: bool (optional)
            }

        Returns:
            Complete analysis dict with all engine outputs
        """
        result = {
            "meta": {
                "orchestrator_version": self.version,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "pillars": pillars,
            "birth_context": birth_context
        }

        # Level 0: Extract basics
        result["season"] = self._extract_season(pillars["month"])
        result["day_master"] = pillars["day"][0]  # 癸酉 → 癸

        # Level 1: Ten Gods (embedded in strength evaluator)
        # Calculated internally, no separate step needed

        # Level 2: Strength & Relations (parallel, no deps on each other)
        result["strength"] = self._run_strength_evaluation(pillars, result["season"])
        result["relations"] = self._run_relation_transformation(pillars)

        # Level 3: Climate & Luck (parallel)
        result["climate"] = self._run_climate_evaluation(
            pillars, result["season"], result["strength"]
        )
        result["luck"] = self._run_luck_calculation(pillars, birth_context)

        # Level 4: Yongshin (depends on strength, relations, climate)
        result["yongshin"] = self._run_yongshin_selection(
            result["day_master"],
            result["strength"],
            result["relations"],
            result["climate"]
        )

        # Level 5-6: Stage-3 engines (depends on core context)
        result["stage3"] = self._run_stage3_engines(result)

        # Level 7: Post-processing
        result["korean_labels"] = self._apply_korean_labels(result)
        result["school_profile"] = self.school_manager.get_default()
        result["recommendations"] = self._apply_recommendation_guard(result)

        return result

    def _extract_season(self, month_pillar: str) -> str:
        """Extract season from month branch (乙酉 → 酉 → 가을)."""
        branch = month_pillar[1]  # Get branch character
        branch_to_season = {
            "寅": "봄", "卯": "봄", "辰": "장하",
            "巳": "여름", "午": "여름", "未": "장하",
            "申": "가을", "酉": "가을", "戌": "장하",
            "亥": "겨울", "子": "겨울", "丑": "장하"
        }
        return branch_to_season.get(branch, "unknown")

    def _run_strength_evaluation(self, pillars: Dict, season: str) -> Dict:
        """Run StrengthEvaluator."""
        # TODO: Implement call to StrengthEvaluator.evaluate()
        pass

    def _run_relation_transformation(self, pillars: Dict) -> Dict:
        """Run RelationTransformer."""
        # TODO: Implement call to RelationTransformer.evaluate()
        pass

    def _run_climate_evaluation(self, pillars: Dict, season: str, strength: Dict) -> Dict:
        """Run ClimateEvaluator."""
        # TODO: Implement call to ClimateEvaluator.evaluate()
        pass

    def _run_luck_calculation(self, pillars: Dict, birth_context: Dict) -> Dict:
        """Run LuckCalculator."""
        # TODO: Implement call to LuckCalculator.compute_start_age()
        pass

    def _run_yongshin_selection(self, day_master: str, strength: Dict,
                                 relations: Dict, climate: Dict) -> Dict:
        """Run YongshinSelector."""
        # TODO: Implement call to YongshinSelector.select()
        pass

    def _run_stage3_engines(self, core_result: Dict) -> Dict:
        """Run Stage-3 engines with core context."""
        # Build context for Stage-3
        context = {
            "season": core_result["season"],
            "year": core_result["birth_context"].get("birth_dt").year,
            "strength": {
                "phase": core_result["strength"].get("phase"),
                "elements": core_result["strength"].get("elements", {})
            },
            "relation": {
                "flags": core_result["relations"].get("flags", [])
            },
            "climate": {
                "flags": core_result["climate"].get("flags", []),
                "balance_index": core_result["climate"].get("balance_index", 0)
            },
            "yongshin": {
                "primary": core_result["yongshin"].get("primary")
            }
        }

        return self.stage3_engine.analyze(context)

    def _apply_korean_labels(self, result: Dict) -> Dict:
        """Apply Korean label enrichment."""
        return self.korean_enricher.enrich(result)

    def _apply_recommendation_guard(self, result: Dict) -> list:
        """Apply recommendation filtering."""
        # TODO: Implement recommendation guard logic
        return []
```

**Timeline:** 4-6 hours

#### Step 1.2: Implement Core Engine Calls
Fill in the `_run_*` methods with actual engine calls. Each method needs to:
1. Prepare input dict matching engine's expected format
2. Call engine method
3. Handle errors gracefully
4. Transform output to standard format

**Timeline:** 6-8 hours

#### Step 1.3: Write Unit Tests
**File:** `services/analysis-service/tests/test_master_orchestrator.py`

Test cases:
- Test each `_run_*` method in isolation
- Test full pipeline with known birth data
- Test error handling for missing data
- Test with unknown_hour flag

**Timeline:** 4-6 hours

---

### Phase 2: Integration & Testing (Day 3)

#### Step 2.1: End-to-End Integration Test
**File:** `tests/test_e2e_orchestrator.py`

```python
def test_full_pipeline_2000_09_14():
    """Test complete pipeline with known birth data."""
    from datetime import datetime
    from scripts.calculate_pillars_traditional import calculate_four_pillars
    from services.analysis_service.app.core.master_orchestrator import MasterOrchestrator

    # Calculate pillars
    pillars = calculate_four_pillars(
        birth_dt=datetime(2000, 9, 14, 10, 0),
        tz_str='Asia/Seoul',
        mode='traditional_kr',
        zi_hour_mode='traditional',
        return_metadata=True
    )

    # Run orchestrator
    orchestrator = MasterOrchestrator()
    result = orchestrator.analyze(
        pillars=pillars,
        birth_context={
            "birth_dt": datetime(2000, 9, 14, 10, 0),
            "gender": "M",  # Assuming
            "timezone": "Asia/Seoul",
            "unknown_hour": False
        }
    )

    # Assertions
    assert result["pillars"]["year"] == "庚辰"
    assert result["season"] == "가을"
    assert "strength" in result
    assert "yongshin" in result
    assert "stage3" in result

    # Print for manual inspection
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

**Timeline:** 2-3 hours

#### Step 2.2: Golden Test Cases
Create 5 golden test cases with expected outputs:
- Strong chart (신강)
- Weak chart (신약)
- Balanced chart (중화)
- Special structure (종격)
- Unknown hour case

**Timeline:** 2-3 hours

#### Step 2.3: Documentation
Create orchestrator usage guide:
- How to call from external services
- Input/output contracts
- Error handling patterns
- Performance expectations

**Timeline:** 1-2 hours

---

## 5. Error Handling Strategy

### 5.1 Error Categories

#### Category A: Fatal Errors (Stop Pipeline)
- Missing pillars data
- Invalid birth_dt format
- Engine initialization failure

**Response:** Raise exception, log error, return error response

#### Category B: Recoverable Errors (Fallback)
- Engine calculation failure (use defaults)
- Missing optional parameters
- Policy file load failure (use embedded defaults)

**Response:** Log warning, use fallback values, continue pipeline

#### Category C: Data Quality Issues (Flag)
- Unknown hour
- Ambiguous strength evaluation
- Low confidence yongshin

**Response:** Add warning flag, continue with best-effort, mark confidence

### 5.2 Error Response Format

```python
{
  "status": "partial_success",  # or "error", "success"
  "errors": [
    {
      "code": "STRENGTH_EVAL_FAILED",
      "message": "StrengthEvaluator failed: missing season data",
      "severity": "warning",  # or "fatal"
      "fallback_used": "default_moderate"
    }
  ],
  "warnings": [
    {
      "code": "UNKNOWN_HOUR",
      "message": "Birth hour unknown, luck calculation may be inaccurate"
    }
  ],
  "result": { ... }  # Partial or complete result
}
```

### 5.3 Fallback Values

```python
FALLBACK_VALUES = {
    "strength": {
        "level": "중화",
        "score": 50,
        "phase": "休",
        "confidence": 0.0
    },
    "yongshin": {
        "primary": None,
        "confidence": 0.0,
        "rationale": ["Default fallback used"]
    },
    "climate": {
        "season": "unknown",
        "flags": [],
        "balance_index": 0
    }
}
```

---

## 6. Performance Targets

| Phase | Target Time | Notes |
|-------|-------------|-------|
| Pillars calculation | <100ms | Already optimized |
| Core engines (all) | <500ms | Sequential execution |
| Stage-3 engines (all) | <300ms | Parallel where possible |
| Korean enrichment | <100ms | Dict lookups |
| **Total pipeline** | **<1000ms** | 1 second target |

### Optimization Opportunities
1. **Parallel execution** of independent engines (strength + relations)
2. **Caching** of policy files (already loaded once)
3. **Lazy loading** of optional engines (shensha, korean labels)
4. **Batch processing** for multiple birth dates

---

## 7. Testing Strategy

### 7.1 Unit Tests (Per Engine)
- Each `_run_*` method tested independently
- Mock engine responses
- Error handling paths

**Target:** 20 unit tests, 100% coverage of orchestrator code

### 7.2 Integration Tests (Engine Combinations)
- Strength → Yongshin flow
- Relations → Stage-3 flow
- Climate → Climate Advice flow

**Target:** 10 integration tests

### 7.3 End-to-End Tests (Full Pipeline)
- 5 golden cases with known outputs
- Performance benchmarks
- Error scenario tests

**Target:** 8 E2E tests

### 7.4 Regression Tests
- Compare outputs with existing analysis-service (if any)
- Ensure backward compatibility with Stage-3 engines

---

## 8. Deployment Plan

### 8.1 Phase 1: Development Branch
- Create `feature/master-orchestrator` branch
- Implement + test orchestrator
- Code review

### 8.2 Phase 2: Staging Integration
- Merge to `staging` branch
- Run full test suite
- Manual QA with real birth data

### 8.3 Phase 3: Production Release
- Merge to `main`
- Update CLAUDE.md and CODEBASE_MAP.md
- Tag as `v2.0-orchestrator`
- Monitor performance

---

## 9. Success Criteria

✅ **Must Have:**
1. Complete pipeline from birth_dt → final JSON
2. All core engines integrated and working
3. Stage-3 engines receiving correct context
4. Error handling for all failure modes
5. <1000ms total pipeline time
6. 100% test pass rate

🎯 **Should Have:**
1. Korean label enrichment working
2. 5 golden test cases passing
3. Documentation complete
4. Performance profiling done

💡 **Nice to Have:**
1. Parallel execution of independent engines
2. Caching optimization
3. Batch processing API
4. WebSocket streaming support

---

## 10. Implementation Checklist

### Day 1 (6-8 hours)
- [ ] Create `master_orchestrator.py` skeleton
- [ ] Implement `_extract_season()`
- [ ] Implement `_run_strength_evaluation()`
- [ ] Implement `_run_relation_transformation()`
- [ ] Write unit tests for above methods
- [ ] Test strength + relations integration

### Day 2 (6-8 hours)
- [ ] Implement `_run_climate_evaluation()`
- [ ] Implement `_run_luck_calculation()`
- [ ] Implement `_run_yongshin_selection()`
- [ ] Implement `_run_stage3_engines()`
- [ ] Write unit tests for above methods
- [ ] Test core → Stage-3 integration

### Day 3 (4-6 hours)
- [ ] Implement `_apply_korean_labels()`
- [ ] Implement error handling throughout
- [ ] Write E2E test with 2000-09-14 birth data
- [ ] Create 5 golden test cases
- [ ] Performance profiling
- [ ] Documentation
- [ ] Code review preparation

---

## 11. Open Questions

1. **Q:** Should ten_gods calculation be extracted from StrengthEvaluator into its own function?
   **A:** [TBD] Discuss with team - current embedding is acceptable for v1.0

2. **Q:** How to handle conflicting yongshin recommendations from different schools?
   **A:** [TBD] SchoolProfileManager can provide alternate interpretations in v2.0

3. **Q:** Should Stage-3 engines run in parallel or sequential?
   **A:** Sequential for v1.0 (dependencies exist), parallel optimization in v2.0

4. **Q:** How to version the orchestrator output schema?
   **A:** Include `meta.orchestrator_version` field, use semantic versioning

5. **Q:** What to do when yongshin confidence is very low (<0.3)?
   **A:** Include warning flag, provide multiple candidates, mark as "uncertain"

---

## 12. Next Steps After Orchestrator

1. **API Gateway Integration** - Connect orchestrator to REST API
2. **LLM Polish Integration** - Feed orchestrator output to LLM polish service
3. **Report Generation** - Use orchestrator output for PDF reports
4. **Caching Layer** - Cache orchestrator results by birth_dt hash
5. **Monitoring & Analytics** - Track engine performance and accuracy

---

## 13. References

- **CLAUDE.md** - Central reference hub
- **CODEBASE_MAP.md** - Architecture overview
- **STAGE3_V2_INTEGRATION_COMPLETE.md** - Stage-3 integration report
- **API_SPECIFICATION_v1.0.md** - API contracts
- **SAJU_REPORT_SCHEMA_v1.0.md** - Output schema

---

**Plan Version:** 1.0
**Author:** Claude (AI Assistant)
**Review Status:** Pending team review
**Target Start Date:** TBD
**Estimated Completion:** 2-3 days (16-24 hours)

---

*This plan provides a comprehensive roadmap for building the master orchestrator. All code samples are pseudocode for planning purposes. Actual implementation will require detailed method signatures and error handling based on actual engine interfaces.*
