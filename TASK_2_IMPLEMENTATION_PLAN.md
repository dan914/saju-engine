# Task 2 Implementation Plan: Wire AnalysisEngine to SajuOrchestrator

**Status:** 🔴 CRITICAL - Blocks production API
**Complexity:** HIGH
**Estimated Effort:** 2-4 hours
**Risk:** MEDIUM-HIGH (touches API contract)

---

## Problem Statement

The current `AnalysisEngine` in `app/core/engine.py` is a **stub** that:
- Only runs 4 Stage-3 MVP engines (luck_flow, gyeokguk, climate_advice, pattern_profiler)
- Returns a plain dict with incomplete data
- Missing all core analysis: ten_gods, relations, strength, structure, luck, shensha
- Causes guard to crash (expects AnalysisResponse object, gets dict)

**Real orchestrator exists** (`SajuOrchestrator`) but is not wired to the API.

---

## Goal

Replace stub `AnalysisEngine` with integration to `SajuOrchestrator` to:
1. Return complete analysis data (all engines)
2. Return `AnalysisResponse` object (not dict)
3. Make /analyze endpoint functional with real data
4. Enable guard pipeline to work correctly

---

## Current Architecture

```
API Request (AnalysisRequest)
  ↓
engine.analyze(request)  ← STUB (only 4 Stage-3 engines)
  ↓
Returns: {"luck_flow": ..., "gyeokguk": ...}  ← DICT (incomplete)
  ↓
guard.prepare_payload(response)  ← CRASHES (expects object, gets dict)
```

---

## Target Architecture

```
API Request (AnalysisRequest)
  ↓
engine.analyze(request)
  ↓
  1. Extract pillars: {year: "庚辰", month: "乙酉", ...}
  2. Extract birth_context: {birth_dt, gender, timezone}
  3. Call orchestrator.analyze(pillars, birth_context)
  ↓
orchestrator returns comprehensive dict (20+ fields)
  ↓
  4. Map to AnalysisResponse structure
  5. Return AnalysisResponse object
  ↓
guard.prepare_payload(response)  ← WORKS (gets object)
```

---

## Step-by-Step Implementation

### Step 1: Understand Current Files (Analysis Phase)

#### File 1: Current Stub Engine
**Location:** `services/analysis-service/app/core/engine.py` (lines 1-27)

**Current Code:**
```python
class AnalysisEngine:
    def __init__(self):
        self.climate_advice = ClimateAdvice()
        self.luck_flow = LuckFlow()
        self.gyeokguk = GyeokgukClassifier()
        self.pattern = PatternProfiler()

    def analyze(self, context):
        lf = self.luck_flow.run(context)
        gk = self.gyeokguk.run({**context, "luck_flow": lf})
        ca = self.climate_advice.run(context)
        pp = self.pattern.run({**context, "luck_flow": lf, "gyeokguk": gk})
        return {"luck_flow": lf, "gyeokguk": gk, "climate_advice": ca, "pattern": pp}
```

**Problems:**
- `context` parameter is AnalysisRequest object (not dict)
- Stage-3 engines expect dict, do `isinstance(context, dict)` checks
- All engines fall back to defaults, return stub data
- Missing 16+ analysis fields required by AnalysisResponse

---

#### File 2: SajuOrchestrator
**Location:** `services/analysis-service/app/core/saju_orchestrator.py`

**Method Signature:**
```python
def analyze(
    self,
    pillars: Dict[str, str],  # {year, month, day, hour} in 60甲子
    birth_context: Dict[str, Any]  # {birth_dt, gender, timezone}
) -> Dict[str, Any]:
```

**Input Expected:**
```python
pillars = {
    "year": "庚辰",
    "month": "乙酉",
    "day": "乙亥",
    "hour": "辛巳"
}

birth_context = {
    "birth_dt": datetime(2000, 9, 14, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")),
    "gender": "M",
    "timezone": "Asia/Seoul"
}
```

**Output Structure (lines 226-267):**
```python
{
    "season": "봄",  # String
    "strength": {...},  # StrengthEvaluator result
    "relations": {...},  # RelationTransformer result
    "relations_weighted": {...},  # With weights added
    "relations_extras": {"banhe_groups": [...]},
    "climate": {...},  # ClimateEvaluator result
    "elements_distribution": {...},  # Element counts
    "elements_distribution_transformed": {...},
    "combination_trace": {...},
    "yongshin": {...},  # YongshinSelector result
    "luck": {...},  # LuckCalculator result
    "shensha": {...},  # ShenshaCatalog result
    "void": {...},  # VoidCalculator result
    "yuanjin": {...},  # YuanjinDetector result
    "stage3": {  # Stage-3 engines output
        "luck_flow": {...},
        "gyeokguk": {...},
        "climate_advice": {...},
        "pattern": {...}
    },
    "evidence": {...},  # EvidenceBuilder result
    "engine_summaries": {...},  # EngineSummariesBuilder result
    "school_profile": {...},  # SchoolProfileManager result
    "recommendations": {...}  # RecommendationGuard result
}
```

---

#### File 3: AnalysisResponse Model
**Location:** `services/analysis-service/app/models/analysis.py` (lines 113-128)

**Required Fields:**
```python
class AnalysisResponse(BaseModel):
    ten_gods: TenGodsResult
    relations: RelationsResult
    relation_extras: RelationsExtras
    strength: StrengthResult
    strength_details: StrengthDetails
    structure: StructureResultModel
    luck: LuckResult
    luck_direction: LuckDirectionResult
    shensha: ShenshaResult
    school_profile: SchoolProfileResult
    recommendation: RecommendationResult
    trace: dict[str, object]
```

**Note:** Field names differ from orchestrator output!
- Orchestrator: `relations_extras` → Response: `relation_extras`
- Orchestrator: `recommendations` → Response: `recommendation`
- Orchestrator: `luck.start_age` → Response needs `luck` AND `luck_direction` (split)
- Orchestrator: No `ten_gods` → Response needs it (from strength result?)

---

### Step 2: Extract Helper Functions

#### Helper 1: Extract Pillars
```python
def extract_pillars(request: AnalysisRequest) -> Dict[str, str]:
    """
    Extract 60甲子 strings from AnalysisRequest.

    Args:
        request.pillars: {
            "year": PillarInput(pillar="庚辰"),
            "month": PillarInput(pillar="乙酉"),
            ...
        }

    Returns:
        {"year": "庚辰", "month": "乙酉", ...}
    """
    return {
        position: pillar_input.pillar
        for position, pillar_input in request.pillars.items()
    }
```

---

#### Helper 2: Extract Birth Context
```python
def extract_birth_context(options: AnalysisOptions) -> Dict[str, Any]:
    """
    Extract birth context from AnalysisRequest.options.

    Args:
        options.birth_dt: ISO string or datetime
        options.gender: Optional[str]
        options.timezone: Optional[str]

    Returns:
        {
            "birth_dt": datetime object,
            "gender": str (M/F),
            "timezone": str (IANA)
        }
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Parse birth_dt if string
    if isinstance(options.birth_dt, str):
        birth_dt = datetime.fromisoformat(
            options.birth_dt.replace("Z", "+00:00")
        )
    else:
        birth_dt = options.birth_dt

    # Ensure timezone aware
    tz_str = options.timezone or "Asia/Seoul"
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=ZoneInfo(tz_str))

    return {
        "birth_dt": birth_dt,
        "gender": options.gender or "M",
        "timezone": tz_str
    }
```

---

#### Helper 3: Map Orchestrator Output to AnalysisResponse

**The Complex Part - Field Mapping:**

```python
def map_to_analysis_response(
    orchestrator_result: Dict[str, Any],
    pillars: Dict[str, str]
) -> AnalysisResponse:
    """
    Map SajuOrchestrator output to AnalysisResponse structure.

    This is the most complex part - need to extract and reshape data.
    """
    from app.models.analysis import (
        AnalysisResponse,
        TenGodsResult,
        RelationsResult,
        RelationsExtras,
        StrengthResult,
        StrengthDetails,
        StructureResultModel,
        LuckResult,
        LuckDirectionResult,
        ShenshaResult,
        SchoolProfileResult,
        RecommendationResult
    )

    # Extract strength data
    strength_data = orchestrator_result.get("strength", {})

    # 1. TenGodsResult - Extract from strength or relations?
    # TODO: Determine where ten_gods data comes from in orchestrator
    ten_gods = TenGodsResult(
        summary=strength_data.get("ten_gods", {}),  # May need adjustment
        details={}
    )

    # 2. RelationsResult
    relations_data = orchestrator_result.get("relations", {})
    relations = RelationsResult(
        he6=relations_data.get("he6", []),
        sanhe=relations_data.get("sanhe", []),
        chong=relations_data.get("chong", []),
        xing=relations_data.get("xing", []),
        po=relations_data.get("po", []),
        hai=relations_data.get("hai", []),
        combine=relations_data.get("combine", [])
    )

    # 3. RelationsExtras (note: singular vs plural)
    extras_data = orchestrator_result.get("relations_extras", {})
    relation_extras = RelationsExtras(
        banhe_groups=extras_data.get("banhe_groups", []),
        void=orchestrator_result.get("void", {}),
        yuanjin=orchestrator_result.get("yuanjin", {})
    )

    # 4. StrengthResult
    strength = StrengthResult(
        level=strength_data.get("grade", "중화"),
        bucket=strength_data.get("bucket", "중화"),
        phase=strength_data.get("phase", "相")
    )

    # 5. StrengthDetails
    strength_details = StrengthDetails(
        total=strength_data.get("score", 50),
        month_state=strength_data.get("month_state", 0),
        branch_root=strength_data.get("branch_root", 0),
        stem_visible=strength_data.get("stem_visible", 0),
        combo_clash=strength_data.get("combo_clash", 0)
    )

    # 6. StructureResultModel
    stage3 = orchestrator_result.get("stage3", {})
    gyeokguk = stage3.get("gyeokguk", {})
    structure = StructureResultModel(
        primary=gyeokguk.get("classification", ""),
        primary_confidence=gyeokguk.get("confidence", 0.0),
        candidates=gyeokguk.get("candidates", [])
    )

    # 7. LuckResult and LuckDirectionResult (split from luck data)
    luck_data = orchestrator_result.get("luck", {})
    luck = LuckResult(
        start_age=luck_data.get("start_age", 0),
        prev_term=luck_data.get("prev_term", ""),
        next_term=luck_data.get("next_term", ""),
        interval_days=luck_data.get("interval_days", 0)
    )

    luck_direction = LuckDirectionResult(
        direction=luck_data.get("direction", "forward"),
        method=luck_data.get("method", "traditional_sex"),
        sex_at_birth=luck_data.get("sex_at_birth", "")
    )

    # 8. ShenshaResult
    shensha_data = orchestrator_result.get("shensha", {})
    shensha = ShenshaResult(
        enabled=shensha_data.get("enabled", True),
        list=shensha_data.get("list", [])
    )

    # 9. SchoolProfileResult
    school_data = orchestrator_result.get("school_profile", {})
    school_profile = SchoolProfileResult(
        id=school_data.get("id", "practical_balanced"),
        notes=school_data.get("notes", "")
    )

    # 10. RecommendationResult (note: singular vs plural)
    reco_data = orchestrator_result.get("recommendations", {})
    recommendation = RecommendationResult(
        allowed=reco_data.get("allowed", []),
        blocked=reco_data.get("blocked", []),
        reason=reco_data.get("reason", "")
    )

    # 11. Trace - Include evidence and summaries
    trace = {
        "evidence": orchestrator_result.get("evidence", {}),
        "engine_summaries": orchestrator_result.get("engine_summaries", {}),
        "pillars": pillars,
        "stage3": stage3
    }

    # Construct AnalysisResponse
    return AnalysisResponse(
        ten_gods=ten_gods,
        relations=relations,
        relation_extras=relation_extras,
        strength=strength,
        strength_details=strength_details,
        structure=structure,
        luck=luck,
        luck_direction=luck_direction,
        shensha=shensha,
        school_profile=school_profile,
        recommendation=recommendation,
        trace=trace
    )
```

**⚠️ IMPORTANT:** This mapping function needs refinement:
- Need to verify exact field names in orchestrator output
- May need to adjust nested structure extractions
- Ten gods data source needs investigation

---

### Step 3: New AnalysisEngine Implementation

**Replace entire `services/analysis-service/app/core/engine.py`:**

```python
# -*- coding: utf-8 -*-
"""
Analysis Engine - Production Implementation

Integrates SajuOrchestrator for complete analysis.
Returns AnalysisResponse compatible with API contract.
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.analysis import AnalysisRequest, AnalysisResponse
from app.core.saju_orchestrator import SajuOrchestrator


class AnalysisEngine:
    """
    Main analysis engine that coordinates all sub-engines.

    Wraps SajuOrchestrator and provides API-compatible interface.
    """

    def __init__(self):
        """Initialize with SajuOrchestrator."""
        self.orchestrator = SajuOrchestrator()

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Perform complete Saju analysis.

        Args:
            request: AnalysisRequest with pillars and options

        Returns:
            AnalysisResponse with all analysis results

        Raises:
            ValueError: If request is invalid
        """
        # 1. Extract pillars (60甲子 strings)
        pillars = self._extract_pillars(request)

        # 2. Extract birth context
        birth_context = self._extract_birth_context(request.options)

        # 3. Call orchestrator
        orchestrator_result = self.orchestrator.analyze(pillars, birth_context)

        # 4. Map to AnalysisResponse
        response = self._map_to_response(orchestrator_result, pillars)

        return response

    @staticmethod
    def _extract_pillars(request: AnalysisRequest) -> Dict[str, str]:
        """Extract 60甲子 strings from request."""
        return {
            position: pillar_input.pillar
            for position, pillar_input in request.pillars.items()
        }

    @staticmethod
    def _extract_birth_context(options) -> Dict[str, Any]:
        """Extract birth context from options."""
        # Parse birth_dt
        birth_dt = options.birth_dt
        if isinstance(birth_dt, str):
            birth_dt = datetime.fromisoformat(
                birth_dt.replace("Z", "+00:00")
            )

        # Ensure timezone aware
        tz_str = options.timezone or "Asia/Seoul"
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=ZoneInfo(tz_str))

        return {
            "birth_dt": birth_dt,
            "gender": options.gender or "M",
            "timezone": tz_str
        }

    def _map_to_response(
        self,
        orchestrator_result: Dict[str, Any],
        pillars: Dict[str, str]
    ) -> AnalysisResponse:
        """
        Map orchestrator output to AnalysisResponse.

        NOTE: This is the complex part that needs careful field mapping.
        TODO: Verify all field names match orchestrator output.
        """
        from app.models.analysis import (
            TenGodsResult, RelationsResult, RelationsExtras,
            StrengthResult, StrengthDetails, StructureResultModel,
            LuckResult, LuckDirectionResult, ShenshaResult,
            SchoolProfileResult, RecommendationResult
        )

        # Extract data from orchestrator result
        strength_data = orchestrator_result.get("strength", {})
        relations_data = orchestrator_result.get("relations", {})
        extras_data = orchestrator_result.get("relations_extras", {})
        luck_data = orchestrator_result.get("luck", {})
        shensha_data = orchestrator_result.get("shensha", {})
        school_data = orchestrator_result.get("school_profile", {})
        reco_data = orchestrator_result.get("recommendations", {})
        stage3 = orchestrator_result.get("stage3", {})
        gyeokguk = stage3.get("gyeokguk", {})

        # Build response components
        # TODO: Verify these field mappings are correct

        ten_gods = TenGodsResult(
            summary=strength_data.get("ten_gods", {}),
            details={}
        )

        relations = RelationsResult(
            he6=relations_data.get("he6", []),
            sanhe=relations_data.get("sanhe", []),
            chong=relations_data.get("chong", []),
            xing=relations_data.get("xing", []),
            po=relations_data.get("po", []),
            hai=relations_data.get("hai", []),
            combine=relations_data.get("combine", [])
        )

        relation_extras = RelationsExtras(
            banhe_groups=extras_data.get("banhe_groups", []),
            void=orchestrator_result.get("void", {}),
            yuanjin=orchestrator_result.get("yuanjin", {})
        )

        strength = StrengthResult(
            level=strength_data.get("grade", "중화"),
            bucket=strength_data.get("bucket", "중화"),
            phase=strength_data.get("phase", "相")
        )

        strength_details = StrengthDetails(
            total=strength_data.get("score", 50),
            month_state=strength_data.get("month_state", 0),
            branch_root=strength_data.get("branch_root", 0),
            stem_visible=strength_data.get("stem_visible", 0),
            combo_clash=strength_data.get("combo_clash", 0)
        )

        structure = StructureResultModel(
            primary=gyeokguk.get("classification", ""),
            primary_confidence=gyeokguk.get("confidence", 0.0),
            candidates=gyeokguk.get("candidates", [])
        )

        luck = LuckResult(
            start_age=luck_data.get("start_age", 0),
            prev_term=luck_data.get("prev_term", ""),
            next_term=luck_data.get("next_term", ""),
            interval_days=luck_data.get("interval_days", 0)
        )

        luck_direction = LuckDirectionResult(
            direction=luck_data.get("direction", "forward"),
            method=luck_data.get("method", "traditional_sex"),
            sex_at_birth=luck_data.get("sex_at_birth", "")
        )

        shensha = ShenshaResult(
            enabled=shensha_data.get("enabled", True),
            list=shensha_data.get("list", [])
        )

        school_profile = SchoolProfileResult(
            id=school_data.get("id", "practical_balanced"),
            notes=school_data.get("notes", "")
        )

        recommendation = RecommendationResult(
            allowed=reco_data.get("allowed", []),
            blocked=reco_data.get("blocked", []),
            reason=reco_data.get("reason", "")
        )

        trace = {
            "evidence": orchestrator_result.get("evidence", {}),
            "engine_summaries": orchestrator_result.get("engine_summaries", {}),
            "pillars": pillars,
            "stage3": stage3
        }

        return AnalysisResponse(
            ten_gods=ten_gods,
            relations=relations,
            relation_extras=relation_extras,
            strength=strength,
            strength_details=strength_details,
            structure=structure,
            luck=luck,
            luck_direction=luck_direction,
            shensha=shensha,
            school_profile=school_profile,
            recommendation=recommendation,
            trace=trace
        )
```

---

### Step 4: Backup Current Stub (Safety)

**Before replacing, backup current engine:**

```bash
cd services/analysis-service/app/core
cp engine.py engine_stub_backup.py
```

Then replace with new implementation above.

---

### Step 5: Update routes.py (Minimal Changes)

**File:** `services/analysis-service/app/api/routes.py`

**Current code (lines 29-40):**
```python
@router.post("/analyze")
def analyze(
    payload: AnalysisRequest,
    engine: AnalysisEngine = Depends(get_engine),
    guard: LLMGuard = Depends(get_llm_guard),
) -> AnalysisResponse:
    """Return ten gods / relations / strength analysis."""
    response = engine.analyze(payload)  # Now returns AnalysisResponse ✅
    llm_payload = guard.prepare_payload(response)  # Works now ✅
    final_response = guard.postprocess(
        response, llm_payload, structure_primary=response.structure.primary, topic_tags=[]
    )
    return final_response
```

**No changes needed!** Once engine returns AnalysisResponse, routes.py will work.

---

### Step 6: Testing Strategy

#### Test 1: Unit Test Engine Directly
```python
# services/analysis-service/tests/test_new_engine.py
from app.core.engine import AnalysisEngine
from app.models.analysis import AnalysisRequest, PillarInput, AnalysisOptions
from datetime import datetime

def test_engine_returns_analysis_response():
    engine = AnalysisEngine()

    request = AnalysisRequest(
        pillars={
            "year": PillarInput(pillar="庚辰"),
            "month": PillarInput(pillar="乙酉"),
            "day": PillarInput(pillar="乙亥"),
            "hour": PillarInput(pillar="辛巳")
        },
        options=AnalysisOptions(
            birth_dt="2000-09-14T10:00:00+09:00",
            timezone="Asia/Seoul",
            gender="M"
        )
    )

    response = engine.analyze(request)

    # Verify it's AnalysisResponse object
    from app.models.analysis import AnalysisResponse
    assert isinstance(response, AnalysisResponse)

    # Verify required fields exist
    assert hasattr(response, 'ten_gods')
    assert hasattr(response, 'relations')
    assert hasattr(response, 'strength')
    assert hasattr(response, 'structure')
    assert hasattr(response, 'luck')

    # Verify data is not stub
    assert response.strength.total != 0  # Not stub data
    print(f"✅ Engine returns: {response.strength.level}")
```

#### Test 2: Integration Test via API
```bash
cd services/analysis-service
uvicorn app.main:app --reload --port 8000

# In another terminal:
curl -X POST http://localhost:8000/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pillars": {
      "year": {"pillar": "庚辰"},
      "month": {"pillar": "乙酉"},
      "day": {"pillar": "乙亥"},
      "hour": {"pillar": "辛巳"}
    },
    "options": {
      "birth_dt": "2000-09-14T10:00:00+09:00",
      "timezone": "Asia/Seoul",
      "gender": "M"
    }
  }'
```

**Expected:** 200 OK with full analysis data (not stub)

#### Test 3: Run Existing Tests
```bash
cd services/analysis-service
env PYTHONPATH=. ../../.venv/bin/pytest tests/test_analyze.py -v
```

**Expected:** Should pass (or at least not crash with AttributeError)

---

## Known Risks & Mitigations

### Risk 1: Field Name Mismatches
**Problem:** Orchestrator field names may not match AnalysisResponse
**Mitigation:**
- Print orchestrator output to inspect actual structure
- Add debug logging in mapping function
- Fallback to empty/default values if field missing

### Risk 2: Nested Structure Differences
**Problem:** Orchestrator may return different nesting than expected
**Mitigation:**
- Carefully inspect orchestrator output structure
- Use `.get()` with defaults everywhere
- Add validation after mapping

### Risk 3: Type Mismatches
**Problem:** Orchestrator may return int where str expected (or vice versa)
**Mitigation:**
- Pydantic will validate and raise clear errors
- Use `model_validate()` to catch issues early
- Add type coercion if needed

### Risk 4: Missing Ten Gods Data
**Problem:** Not clear where ten_gods data comes from in orchestrator
**Mitigation:**
- Inspect strength_result for ten_gods field
- May need to call TenGodsCalculator separately
- Can start with empty {} and fix later

---

## Debugging Strategy

If things break, add debug logging:

```python
def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
    pillars = self._extract_pillars(request)
    birth_context = self._extract_birth_context(request.options)

    print(f"DEBUG: Pillars = {pillars}")
    print(f"DEBUG: Birth context = {birth_context}")

    orchestrator_result = self.orchestrator.analyze(pillars, birth_context)

    print(f"DEBUG: Orchestrator returned keys: {orchestrator_result.keys()}")
    print(f"DEBUG: Strength data: {orchestrator_result.get('strength', {})}")

    response = self._map_to_response(orchestrator_result, pillars)
    return response
```

---

## Success Criteria

Task 2 is complete when:

- [x] AnalysisEngine.analyze() returns AnalysisResponse (not dict)
- [x] AnalysisResponse has all required fields populated
- [x] /analyze endpoint returns 200 (not 500)
- [x] Guard pipeline works without AttributeError
- [x] Test request returns real data (not stub values)
- [x] Existing tests pass (or have clear path to fix)

---

## Estimated Time Breakdown

| Step | Description | Time |
|------|-------------|------|
| 1 | Read/understand current code | 30 min |
| 2 | Inspect orchestrator output structure | 30 min |
| 3 | Write mapping function | 60 min |
| 4 | Replace engine.py | 15 min |
| 5 | Test and debug field mappings | 45-90 min |
| 6 | Fix any Pydantic validation errors | 30-60 min |
| **Total** | | **3.5-4.5 hours** |

---

## Next Steps After Task 2

Once Task 2 is complete:

1. ✅ **Task 3:** Fix guard pipeline (should "just work" now - 15 min)
2. ✅ **Test:** Verify /analyze endpoint works end-to-end
3. ✅ **Commit:** Save progress before moving to high-priority tasks
4. ⏭️ **Continue:** Move to high-priority tasks (hardcoded values)

---

## Questions to Investigate During Implementation

1. **Where does ten_gods data come from?**
   - Check strength_result for ten_gods field
   - May be in relations_result
   - May need separate TenGodsCalculator call

2. **What's the exact structure of orchestrator.luck output?**
   - Need both `luck` and `luck_direction` data
   - Verify field names: start_age, direction, method

3. **Are there any other required AnalysisResponse fields?**
   - Check model definition for Optional vs required
   - Verify all required fields have mappings

4. **Does orchestrator handle missing hour pillar?**
   - Test with `hour: None` case
   - May need special handling

---

## Rollback Plan

If Task 2 breaks things:

```bash
# Restore stub engine
cd services/analysis-service/app/core
mv engine_stub_backup.py engine.py

# Restart service
# API will return stub data again (but won't crash)
```

---

**Status:** 📋 PLAN READY
**Next:** Implement Step 1-6
**Owner:** Next session
**Priority:** 🔴 CRITICAL

---

**Created:** 2025-10-11
**Estimated Effort:** 2-4 hours
**Complexity:** HIGH
**Risk:** MEDIUM-HIGH
