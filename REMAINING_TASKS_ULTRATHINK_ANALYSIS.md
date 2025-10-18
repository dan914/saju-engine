# Remaining Tasks: Ultra-Deep Analysis & Implementation Plan

**Date:** 2025-10-12
**Completed:** 10/17 tasks (58.8%)
**Remaining:** 7 tasks
**Total Estimated Time:** 13.5-19.5 hours

---

## Executive Summary

This document provides a comprehensive analysis of the 7 remaining tasks from the audit action plan, with detailed implementation strategies, risk assessments, and dependency mappings.

### Remaining Tasks by Priority

**HIGH (1 task - 3-4 hours):**
- Task #6: Replace TimezoneConverter stub

**MEDIUM (4 tasks - 8-13 hours):**
- Task #11: Fix EngineSummaries placeholder confidences
- Task #12: Fix Stage-3 golden test skips
- Task #14: Add validation for 4 support policy files
- Task #15: Complete skeleton services or mark as WIP

**LOW (2 tasks - 2.5-3 hours):**
- Task #16: Package services.common properly
- Task #17: Fix hardcoded tzdb_version

---

## Task #6: Replace TimezoneConverter Stub (HIGH PRIORITY)

### Current State Analysis

**File:** `services/tz-time-service/app/core/converter.py:34-36`

**Current Implementation:**
```python
trace = TraceMetadata(
    rule_id="KR_classic_v1.4",
    delta_t_seconds=0.0,  # ❌ HARDCODED - Should calculate real delta-T
    tz={
        "source": request.source_tz,
        "target": request.target_tz,
        "tzdbVersion": self.tzdb_version,
    },
    flags={"tzTransition": bool(events)},
)
```

**Problems:**
1. **delta_t_seconds=0.0** - Always zero, doesn't account for Earth's rotation slowdown
2. **No LMT adjustments** - Doesn't calculate longitude-based time corrections
3. **No metadata propagation** - Trace doesn't capture calculation details

### Required Changes

#### 1. Implement Delta-T Calculation

**What is Delta-T?**
- Difference between Terrestrial Time (TT) and Universal Time (UT)
- Earth's rotation is slowing down → Delta-T increases over time
- Critical for accurate astronomical calculations (solar terms, moon phases)

**Example Values:**
- 1900: ~-3 seconds
- 1987: ~54 seconds
- 2000: ~64 seconds
- 2025: ~69 seconds (estimated)

**Implementation Strategy:**

```python
# Create: services/tz-time-service/app/core/delta_t.py

def calculate_delta_t(dt: datetime) -> float:
    """
    Calculate Delta-T (TT - UT1) for a given datetime.

    Based on Morrison & Stephenson (2004) and NASA interpolation tables.

    Args:
        dt: Datetime to calculate Delta-T for

    Returns:
        Delta-T in seconds
    """
    year = dt.year + (dt.timetuple().tm_yday - 1) / 365.25

    # Historical polynomial fits (Morrison & Stephenson)
    if year < 1600:
        t = (year - 1000) / 100
        return 1360.0 + 320.0 * t + 44.3 * t**2
    elif year < 1700:
        t = (year - 1600) / 100
        return 120.0 - 98.08 * t - 153.2 * t**2
    elif year < 1800:
        t = (year - 1700) / 100
        return 8.83 + 16.71 * t - 6.34 * t**2
    elif year < 1860:
        t = (year - 1800) / 100
        return 13.72 - 33.2 * t + 55.9 * t**2
    elif year < 1900:
        t = (year - 1860) / 100
        return 7.62 + 57.37 * t - 23.51 * t**2
    elif year < 1920:
        t = (year - 1900) / 100
        return -2.79 + 149.4 * t - 598.9 * t**2
    elif year < 1941:
        t = (year - 1920) / 100
        return 21.20 + 84.493 * t - 761.00 * t**2
    elif year < 1961:
        t = (year - 1950) / 100
        return 29.07 + 40.7 * t - 114.4 * t**2
    elif year < 1986:
        t = (year - 1975) / 100
        return 45.45 + 106.7 * t - 36.3 * t**2
    elif year < 2005:
        t = (year - 2000) / 100
        return 63.86 + 33.45 * t - 60.3 * t**2
    elif year < 2050:
        # Linear extrapolation for near-future
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    else:
        # Long-term extrapolation (less accurate)
        t = (year - 1820) / 100
        return -20.0 + 32.0 * t**2

# Example usage:
# >>> calculate_delta_t(datetime(2000, 9, 14))
# 63.8 seconds
```

**Validation Data Sources:**
- [US Naval Observatory Delta-T](https://maia.usno.navy.mil/products/deltaT)
- [IERS Bulletins](https://www.iers.org/IERS/EN/DataProducts/EarthOrientationData/eop.html)

#### 2. Implement LMT (Local Mean Time) Adjustments

**What is LMT?**
- Time based on local longitude before timezone standardization
- Each degree of longitude = 4 minutes time difference
- Critical for birth times before ~1900 (Korea: before 1908)

**Formula:**
```
LMT offset (minutes) = (Local Longitude - Standard Meridian) / 15° × 60
```

**Korea Example:**
- Seoul longitude: 126.978°E
- Standard meridian (KST): 135°E
- LMT offset: (126.978 - 135) / 15 × 60 = -32.088 minutes

**Implementation Strategy:**

```python
# In converter.py

from typing import Dict

# Longitude data for major cities
CITY_LONGITUDES: Dict[str, float] = {
    "Seoul": 126.978,
    "Busan": 129.075,
    "Incheon": 126.705,
    "Daegu": 128.601,
    "Daejeon": 127.385,
    "Gwangju": 126.853,
    "Ulsan": 129.311,
    "Suwon": 127.029,
    # Add more as needed
}

# Standard meridians for timezones
TIMEZONE_MERIDIANS: Dict[str, float] = {
    "Asia/Seoul": 135.0,
    "Asia/Tokyo": 135.0,
    "Asia/Shanghai": 120.0,
    "UTC": 0.0,
    # Add more as needed
}

def calculate_lmt_offset(
    location: str,
    timezone: str,
    birth_year: int
) -> float:
    """
    Calculate LMT offset in minutes for a given location.

    Only applies for dates before timezone standardization.
    Korea: Before 1908-04-01

    Args:
        location: City name (e.g., "Seoul")
        timezone: IANA timezone (e.g., "Asia/Seoul")
        birth_year: Year of birth

    Returns:
        LMT offset in minutes (negative = west of standard meridian)
    """
    # Check if LMT applies
    if timezone == "Asia/Seoul" and birth_year >= 1908:
        return 0.0  # Modern KST applies

    if timezone == "Asia/Tokyo" and birth_year >= 1888:
        return 0.0  # Modern JST applies

    # Get longitudes
    local_lon = CITY_LONGITUDES.get(location, TIMEZONE_MERIDIANS.get(timezone, 0.0))
    standard_lon = TIMEZONE_MERIDIANS.get(timezone, 0.0)

    # Calculate offset
    return (local_lon - standard_lon) / 15.0 * 60.0

# Example:
# >>> calculate_lmt_offset("Seoul", "Asia/Seoul", 1900)
# -32.088 minutes
```

#### 3. Update TimezoneConverter

**New Implementation:**

```python
# services/tz-time-service/app/core/converter.py

from .delta_t import calculate_delta_t

@dataclass(slots=True)
class TimezoneConverter:
    """Converts instants between timezones while tracking tzdb version info."""

    tzdb_version: str
    event_detector: TimeEventDetector

    def convert(self, request: TimeConversionRequest) -> TimeConversionResponse:
        src = _ensure_awareness(request.instant, request.source_tz)
        src = src.astimezone(ZoneInfo(request.source_tz))
        converted = src.astimezone(ZoneInfo(request.target_tz))

        # Calculate Delta-T
        delta_t = calculate_delta_t(src)

        # Calculate LMT offset if location provided
        lmt_offset = 0.0
        if hasattr(request, 'location') and request.location:
            lmt_offset = calculate_lmt_offset(
                request.location,
                request.source_tz,
                src.year
            )

        # Detect timezone transition events
        events = self.event_detector.detect(request)

        # Build trace metadata
        trace = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=delta_t,  # ✅ Real calculation
            tz={
                "source": request.source_tz,
                "target": request.target_tz,
                "tzdbVersion": self.tzdb_version,
                "lmtOffsetMinutes": lmt_offset,  # New field
            },
            flags={
                "tzTransition": bool(events),
                "lmtApplied": abs(lmt_offset) > 0.01,  # New flag
            },
        )

        return TimeConversionResponse(
            input=request,
            converted=converted,
            tzdb_version=self.tzdb_version,
            events=events,
            trace=trace.to_dict(),
        )
```

### Testing Strategy

**Unit Tests:**
```python
# services/tz-time-service/tests/test_delta_t.py

def test_delta_t_historical():
    """Test Delta-T for historical dates with known values."""
    # 1900: approximately -3 seconds
    dt_1900 = datetime(1900, 1, 1)
    delta = calculate_delta_t(dt_1900)
    assert -5 < delta < 0, f"Expected ~-3s, got {delta}s"

    # 2000: approximately 64 seconds
    dt_2000 = datetime(2000, 1, 1)
    delta = calculate_delta_t(dt_2000)
    assert 63 < delta < 65, f"Expected ~64s, got {delta}s"

def test_lmt_offset_seoul():
    """Test LMT offset for Seoul before 1908."""
    offset = calculate_lmt_offset("Seoul", "Asia/Seoul", 1900)
    assert -33 < offset < -31, f"Expected ~-32min, got {offset}min"

def test_lmt_not_applied_modern():
    """Test LMT offset is zero for modern dates."""
    offset = calculate_lmt_offset("Seoul", "Asia/Seoul", 2000)
    assert offset == 0.0, "Modern dates should not have LMT offset"
```

**Integration Tests:**
```python
# services/tz-time-service/tests/test_converter_integration.py

def test_converter_with_delta_t():
    """Test converter includes real delta-T values."""
    converter = TimezoneConverter(
        tzdb_version="2025a",
        event_detector=TimeEventDetector(dst_data={})
    )

    request = TimeConversionRequest(
        instant=datetime(2000, 9, 14, 10, 0, 0),
        source_tz="Asia/Seoul",
        target_tz="UTC"
    )

    response = converter.convert(request)

    # Check delta_t is calculated
    assert response.trace["delta_t_seconds"] > 60
    assert response.trace["delta_t_seconds"] < 70

    # Check trace completeness
    assert "lmtOffsetMinutes" in response.trace["tz"]
    assert "lmtApplied" in response.trace["flags"]
```

### Risk Assessment

**Technical Risks:**
- ⚠️ **MEDIUM:** Delta-T polynomial accuracy decreases for dates >2050
  - **Mitigation:** Add warning in docstring, use IERS data for production
- ⚠️ **LOW:** LMT longitude data incomplete for non-major cities
  - **Mitigation:** Fall back to standard meridian, document limitations

**Impact:**
- **High:** Affects accuracy of all downstream astronomical calculations
- **High:** Critical for historical birth chart calculations (pre-1908)

**Dependencies:**
- None - self-contained module

### Effort Estimate

- **Delta-T implementation:** 1 hour
- **LMT calculation:** 1 hour
- **Converter integration:** 30 minutes
- **Unit tests:** 1 hour
- **Integration tests:** 30 minutes
- **Total:** 4 hours

---

## Task #11: Fix EngineSummaries Placeholder Confidences (MEDIUM PRIORITY)

### Current State Analysis

**File:** `services/analysis-service/app/core/engine_summaries.py:151,162,174`

**Current Code:**
```python
# Line 151
strength = {
    "score": result.get("strength_details", {}).get("total", 50) / 100.0,
    "bucket": result.get("strength", {}).get("level", "중화"),
    "confidence": 0.8,  # ❌ TODO: Add confidence to StrengthEvaluator output
}

# Line 162
relation_items.append({
    "type": rel_type,
    "impact_weight": 0.7,  # ❌ TODO: Get from relation_weight policy
    "formed": True,
    ...
})

# Line 174
yongshin = {
    "yongshin": yongshin_data.get("primary", []),
    "bojosin": yongshin_data.get("secondary", []),
    "confidence": 0.75,  # ❌ TODO: Add confidence to YongshinAnalyzer
}
```

**Problems:**
1. **Strength confidence=0.8** - Hardcoded, doesn't reflect actual confidence
2. **Relation impact_weight=0.7** - Hardcoded, should come from relation_weight_policy_v1.0.json
3. **Yongshin confidence=0.75** - Hardcoded, doesn't reflect selection confidence

### Solution Strategy

#### 1. Strength Confidence Calculation

**Approach:** Calculate confidence based on strength score certainty

**Factors:**
- **Score concentration:** How far from boundary (40/60)?
- **Conservation match:** Do hidden stems align with score?
- **Conflict penalty:** Reduce confidence if many conflicting relationships

**Implementation:**

```python
# In services/analysis-service/app/core/strength.py

def calculate_confidence(
    self,
    total_score: float,
    bucket: str,
    conservation_ok: bool,
    num_conflicts: int
) -> float:
    """
    Calculate confidence score for strength evaluation.

    Args:
        total_score: Raw strength score (0-100)
        bucket: Assigned bucket (극신강, 신강, 중화, 신약, 극신약)
        conservation_ok: Whether energy conservation checks passed
        num_conflicts: Number of conflicting relationships (chong, xing, etc.)

    Returns:
        Confidence score (0.0-1.0)
    """
    # Base confidence starts at 0.5
    confidence = 0.5

    # Factor 1: Distance from bucket boundaries (max +0.3)
    boundaries = {
        "극신강": (80, 100),
        "신강": (60, 79),
        "중화": (40, 59),
        "신약": (20, 39),
        "극신약": (0, 19)
    }

    min_bound, max_bound = boundaries[bucket]
    bucket_range = max_bound - min_bound

    # Distance from nearest boundary
    distance_from_min = total_score - min_bound
    distance_from_max = max_bound - total_score
    min_distance = min(distance_from_min, distance_from_max)

    # Normalize to 0-0.3
    distance_bonus = min(0.3, (min_distance / bucket_range) * 0.3)
    confidence += distance_bonus

    # Factor 2: Conservation match (±0.15)
    if conservation_ok:
        confidence += 0.15
    else:
        confidence -= 0.15

    # Factor 3: Conflict penalty (-0.05 per conflict, max -0.2)
    conflict_penalty = min(0.2, num_conflicts * 0.05)
    confidence -= conflict_penalty

    # Clamp to valid range
    return max(0.0, min(1.0, confidence))

# Example:
# >>> calculate_confidence(
#       total_score=75,    # Mid-range 신강
#       bucket="신강",
#       conservation_ok=True,
#       num_conflicts=1
#     )
# 0.5 + 0.15 (mid-range) + 0.15 (conservation) - 0.05 (1 conflict) = 0.75
```

**Update StrengthEvaluator:**

```python
# In services/analysis-service/app/core/strength.py

def evaluate(self, request: AnalysisRequest) -> Dict[str, Any]:
    """Evaluate strength with confidence."""
    # ... existing code ...

    # Count conflicts
    relations = self._get_relations(request)  # Helper method
    num_conflicts = sum(
        len(relations.get(rel_type, []))
        for rel_type in ["chong", "xing", "po"]
    )

    # Calculate confidence
    confidence = self.calculate_confidence(
        total_score=total_score,
        bucket=bucket,
        conservation_ok=conservation_checks_passed,
        num_conflicts=num_conflicts
    )

    return {
        "strength": {"level": bucket, "confidence": confidence},  # ✅ Add confidence
        "strength_details": {"total": total_score, ...},
        ...
    }
```

#### 2. Relation Impact Weight from Policy

**Approach:** Load from `relation_weight_policy_v1.0.json`

**Current Policy Structure:**
```json
{
  "version": "1.0",
  "policy_name": "relation_weight_policy",
  "description": "Quantifies impact of each relationship type",
  "weights": {
    "六合": 0.7,
    "三合": 0.9,
    "半合": 0.6,
    "方合": 0.5,
    "拱合": 0.4,
    "沖": 0.8,
    "刑_三刑": 0.7,
    "刑_自刑": 0.6,
    "刑_偏刑": 0.5,
    "破": 0.5,
    "害": 0.4
  },
  "policy_signature": "..."
}
```

**Implementation:**

```python
# In services/analysis-service/app/core/engine_summaries.py

from pathlib import Path
import json

class EngineSummariesBuilder:
    def __init__(self):
        self.relation_weight_policy = self._load_relation_weight_policy()

    def _load_relation_weight_policy(self) -> Dict[str, Any]:
        """Load relation weight policy."""
        policy_path = (
            Path(__file__).parents[4]
            / "policy"
            / "relation_weight_policy_v1.0.json"
        )
        with open(policy_path) as f:
            return json.load(f)

    def build_engine_summaries(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Build engine summaries with real impact weights."""
        # ... existing code ...

        # Extract relations with policy-based weights
        relations_data = result.get("relations", {})
        relation_items = []
        for rel_type in ["he6", "sanhe", "chong", "xing", "po", "hai"]:
            items = relations_data.get(rel_type, [])
            for item in items:
                # Map internal names to policy names
                policy_rel_type = self._map_to_policy_type(rel_type, item)

                # Get weight from policy
                impact_weight = self.relation_weight_policy["weights"].get(
                    policy_rel_type,
                    0.5  # Default fallback
                )

                relation_items.append({
                    "type": rel_type,
                    "impact_weight": impact_weight,  # ✅ From policy
                    "formed": True,
                    "hua": item.get("hua", False),
                    "element": item.get("element", ""),
                    **item
                })

        # ... rest of code ...

    def _map_to_policy_type(self, internal_type: str, item: Dict) -> str:
        """Map internal relation type to policy name."""
        mapping = {
            "he6": "六合",
            "sanhe": "三合",
            "chong": "沖",
            "xing": self._get_xing_variant(item),  # Handle xing variants
            "po": "破",
            "hai": "害"
        }
        return mapping.get(internal_type, internal_type)

    def _get_xing_variant(self, item: Dict) -> str:
        """Determine xing variant from item data."""
        xing_type = item.get("xing_type", "")
        if xing_type == "self":
            return "刑_自刑"
        elif xing_type == "ungrateful":
            return "刑_偏刑"
        else:
            return "刑_三刑"  # Default to tri-punishment
```

#### 3. Yongshin Confidence Calculation

**Approach:** Calculate based on selection clarity

**Factors:**
- **Dominant element:** How clear is the yongshin choice?
- **Multiple candidates:** Reduce confidence if many viable options
- **Strength alignment:** Does yongshin align with strength needs?

**Implementation:**

```python
# In services/analysis-service/app/core/yongshin_selector.py

def calculate_yongshin_confidence(
    self,
    primary: List[str],
    secondary: List[str],
    strength_bucket: str,
    element_scores: Dict[str, float]
) -> float:
    """
    Calculate confidence for yongshin selection.

    Args:
        primary: Primary yongshin elements
        secondary: Secondary (bojosin) elements
        strength_bucket: Strength bucket (극신강, 신강, 중화, 신약, 극신약)
        element_scores: Element balance scores {木: 0.2, 火: 0.3, ...}

    Returns:
        Confidence score (0.0-1.0)
    """
    # Base confidence
    confidence = 0.5

    # Factor 1: Single clear choice (+0.3)
    if len(primary) == 1 and len(secondary) == 0:
        confidence += 0.3
    elif len(primary) == 1:
        confidence += 0.2
    elif len(primary) == 2:
        confidence += 0.1
    else:
        confidence -= 0.1  # Too many options reduces confidence

    # Factor 2: Strength-yongshin alignment (+0.2)
    if strength_bucket in ["극신약", "신약"]:
        # Weak → Need 비겁/인성 (Wood/Water support)
        if any(elem in ["木", "水"] for elem in primary):
            confidence += 0.2
    elif strength_bucket in ["극신강", "신강"]:
        # Strong → Need 식상/재성/관성 (Fire/Earth/Metal drain)
        if any(elem in ["火", "土", "金"] for elem in primary):
            confidence += 0.2

    # Factor 3: Element dominance clarity (max +0.2)
    if element_scores:
        sorted_scores = sorted(element_scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            top_gap = sorted_scores[0] - sorted_scores[1]
            confidence += min(0.2, top_gap * 0.4)  # Larger gap = higher confidence

    return max(0.0, min(1.0, confidence))

# Update select_yongshin method
def select_yongshin(self, request: AnalysisRequest) -> Dict[str, Any]:
    """Select yongshin with confidence."""
    # ... existing selection logic ...

    # Calculate confidence
    confidence = self.calculate_yongshin_confidence(
        primary=primary_yongshin,
        secondary=secondary_yongshin,
        strength_bucket=strength_result["bucket"],
        element_scores=element_balance
    )

    return {
        "yongshin": {
            "primary": primary_yongshin,
            "secondary": secondary_yongshin,
            "confidence": confidence  # ✅ Add confidence
        }
    }
```

### Testing Strategy

**Unit Tests:**
```python
def test_strength_confidence_high():
    """Test high confidence when score is mid-range."""
    confidence = calculate_confidence(
        total_score=70,  # Mid-range 신강
        bucket="신강",
        conservation_ok=True,
        num_conflicts=0
    )
    assert confidence >= 0.8

def test_relation_weight_from_policy():
    """Test impact weights loaded from policy."""
    builder = EngineSummariesBuilder()

    # Check policy loaded
    assert "weights" in builder.relation_weight_policy

    # Check specific weight
    sanhe_weight = builder.relation_weight_policy["weights"]["三合"]
    assert sanhe_weight == 0.9
```

### Risk Assessment

**Technical Risks:**
- ⚠️ **LOW:** Policy file not found
  - **Mitigation:** Fallback to default values, add file existence check
- ⚠️ **LOW:** Confidence formulas may need tuning
  - **Mitigation:** Add configuration for confidence weights

**Impact:**
- **Medium:** Improves LLM Guard decision quality
- **Medium:** Better reflection of analysis certainty

### Effort Estimate

- **Strength confidence:** 30 minutes
- **Relation weight loading:** 30 minutes
- **Yongshin confidence:** 30 minutes
- **Unit tests:** 30 minutes
- **Total:** 2 hours

---

## Task #12: Fix Stage-3 Golden Test Skips (MEDIUM PRIORITY)

### Current State Analysis

**File:** `tests/test_stage3_golden_cases.py:54/69/86/102`

**Current Skips:**
```python
# Line 54
if "climate_policy_id" not in expected:
    pytest.skip("No climate_policy_id expectation")

# Line 69
if "luck_flow_trend" not in expected:
    pytest.skip("No luck_flow_trend expectation")

# Line 86
if "gyeokguk_type" not in expected:
    pytest.skip("No gyeokguk_type expectation")

# Line 102
if "patterns_include" not in expected:
    pytest.skip("No patterns_include expectation")
```

**Root Cause:**
Golden test cases in `tests/golden_cases/` don't have expected values for Stage-3 MVP engines (climate, luck_flow, gyeokguk, pattern_profiler).

### Solution Strategy

**Option A: Populate Expected Values (Recommended)**
- Generate expected outputs using current engine implementations
- Add to golden case JSON files
- Enable full test validation

**Option B: Separate Test Cases**
- Create new test file: `test_stage3_mvp_engines.py`
- Keep original golden tests as-is
- Add MVP-specific test cases

**Recommendation:** Option A - Ensures golden cases test full pipeline

### Implementation (Option A)

#### Step 1: Generate Expected Outputs

**Create Script:**
```python
# tools/generate_stage3_golden_expectations.py

#!/usr/bin/env python3
"""
Generate expected Stage-3 MVP engine outputs for golden test cases.
"""

import json
from pathlib import Path
import sys

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.analysis_service.app.core.climate import ClimateEvaluator
from services.analysis_service.app.core.luck_flow import LuckFlowEvaluator
from services.analysis_service.app.core.gyeokguk_classifier import GyeokgukClassifier
from services.analysis_service.app.core.pattern_profiler import PatternProfiler

def generate_expectations_for_case(case_file: Path):
    """Generate Stage-3 expectations for a golden case."""
    with open(case_file) as f:
        case = json.load(f)

    # Get input
    input_data = case["input"]

    # Run engines
    climate_eval = ClimateEvaluator()
    luck_flow_eval = LuckFlowEvaluator()
    gyeokguk_classifier = GyeokgukClassifier()
    pattern_profiler = PatternProfiler()

    # Generate outputs
    climate_result = climate_eval.evaluate(input_data)
    luck_flow_result = luck_flow_eval.evaluate(input_data)
    gyeokguk_result = gyeokguk_classifier.classify(input_data)
    pattern_result = pattern_profiler.profile(input_data)

    # Add to expected
    if "expected" not in case:
        case["expected"] = {}

    case["expected"]["climate_policy_id"] = climate_result.get("policy_id")
    case["expected"]["luck_flow_trend"] = luck_flow_result.get("trend")
    case["expected"]["gyeokguk_type"] = gyeokguk_result.get("type")
    case["expected"]["patterns_include"] = pattern_result.get("tags", [])

    # Save updated case
    with open(case_file, 'w') as f:
        json.dump(case, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated {case_file.name}")

def main():
    golden_dir = Path(__file__).parent.parent / "tests" / "golden_cases"

    for case_file in golden_dir.glob("case_*.json"):
        print(f"Processing {case_file.name}...")
        try:
            generate_expectations_for_case(case_file)
        except Exception as e:
            print(f"❌ Error processing {case_file.name}: {e}")
            continue

    print("\n✅ All golden cases updated!")

if __name__ == "__main__":
    main()
```

#### Step 2: Run Generator

```bash
cd /Users/yujumyeong/coding/\ projects/사주
.venv/bin/python3 tools/generate_stage3_golden_expectations.py
```

#### Step 3: Remove Skip Statements

**Update Test File:**
```python
# tests/test_stage3_golden_cases.py

def test_climate_advice_mvp(case_data):
    """Test climate advice MVP engine."""
    expected = case_data["expected"]
    actual = case_data["actual"]

    # Remove skip - now have expectations
    # if "climate_policy_id" not in expected:
    #     pytest.skip("No climate_policy_id expectation")

    assert "climate_policy_id" in expected, "Missing climate_policy_id in golden case"
    assert actual.get("climate", {}).get("policy_id") == expected["climate_policy_id"]

# Repeat for other 3 tests
```

### Testing Strategy

**Validation Steps:**
1. Run generator script
2. Verify all golden cases updated
3. Run tests: `pytest tests/test_stage3_golden_cases.py -v`
4. Check all 4 previously-skipped tests now pass

### Risk Assessment

**Technical Risks:**
- ⚠️ **LOW:** Generated expectations may be wrong if engines have bugs
  - **Mitigation:** Manual review of 2-3 sample cases
- ⚠️ **LOW:** Engines may not be fully implemented
  - **Mitigation:** Check engine status before running generator

**Impact:**
- **Medium:** Improves test coverage for Stage-3 MVP engines
- **Low:** Catches regressions in MVP implementations

### Effort Estimate

- **Generator script:** 1 hour
- **Run and validate:** 30 minutes
- **Update test file:** 30 minutes
- **Manual review:** 30 minutes
- **Total:** 2.5 hours

---

## Task #14: Add Validation for 4 Support Policy Files (MEDIUM PRIORITY)

### Current State Analysis

**Files:**
1. `policy/seasons_wang_map_v2.json` (1,851 bytes)
2. `policy/strength_grading_tiers_v1.json` (572 bytes)
3. `policy/yongshin_dual_policy_v1.json` (1,108 bytes)
4. `policy/zanggan_table.json` (1,360 bytes)

**Status:**
- ✅ All files exist
- ✅ All have RFC-8785 signatures
- ❌ No JSON Schemas
- ❌ No unit tests

### Solution Strategy

Create JSON Schema and unit tests for each policy file to ensure:
1. **Structural validation** - Correct fields and types
2. **Semantic validation** - Valid values and relationships
3. **Signature validation** - RFC-8785 integrity

### Implementation

#### 1. seasons_wang_map_v2.json Schema

**Policy Structure:**
```json
{
  "version": "2.0",
  "policy_name": "seasons_wang_map",
  "description": "Maps seasons/months to Wang-Xiang-Xiu-Qiu-Si states",
  "seasons": {
    "spring": {
      "wood": "旺",
      "fire": "相",
      "water": "休",
      "metal": "囚",
      "earth": "死"
    },
    ...
  },
  "policy_signature": "..."
}
```

**Create Schema:**
```json
// schema/seasons_wang_map.schema.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sajuengine.example.com/schemas/seasons_wang_map.schema.json",
  "title": "Seasons Wang Map Policy Schema",
  "description": "Validates seasons_wang_map policy structure",
  "type": "object",
  "required": ["version", "policy_name", "description", "seasons", "policy_signature"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "policy_name": {
      "type": "string",
      "const": "seasons_wang_map"
    },
    "description": {
      "type": "string"
    },
    "seasons": {
      "type": "object",
      "required": ["spring", "summer", "autumn", "winter"],
      "properties": {
        "spring": {"$ref": "#/$defs/season_states"},
        "summer": {"$ref": "#/$defs/season_states"},
        "autumn": {"$ref": "#/$defs/season_states"},
        "winter": {"$ref": "#/$defs/season_states"}
      },
      "additionalProperties": false
    },
    "policy_signature": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    }
  },
  "additionalProperties": false,
  "$defs": {
    "season_states": {
      "type": "object",
      "required": ["wood", "fire", "earth", "metal", "water"],
      "properties": {
        "wood": {"$ref": "#/$defs/wang_state"},
        "fire": {"$ref": "#/$defs/wang_state"},
        "earth": {"$ref": "#/$defs/wang_state"},
        "metal": {"$ref": "#/$defs/wang_state"},
        "water": {"$ref": "#/$defs/wang_state"}
      },
      "additionalProperties": false
    },
    "wang_state": {
      "type": "string",
      "enum": ["旺", "相", "休", "囚", "死"],
      "description": "Wang-Xiang-Xiu-Qiu-Si states"
    }
  }
}
```

**Create Unit Test:**
```python
# tests/test_seasons_wang_map_policy.py

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

@pytest.fixture
def policy():
    policy_path = Path(__file__).parent.parent / "policy" / "seasons_wang_map_v2.json"
    with open(policy_path) as f:
        return json.load(f)

@pytest.fixture
def schema():
    schema_path = Path(__file__).parent.parent / "schema" / "seasons_wang_map.schema.json"
    with open(schema_path) as f:
        return json.load(f)

def test_schema_validation(policy, schema):
    """Test policy validates against schema."""
    try:
        validate(instance=policy, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")

def test_all_seasons_present(policy):
    """Test all 4 seasons are defined."""
    seasons = policy["seasons"]
    assert "spring" in seasons
    assert "summer" in seasons
    assert "autumn" in seasons
    assert "winter" in seasons

def test_all_elements_in_each_season(policy):
    """Test each season has all 5 elements."""
    elements = ["wood", "fire", "earth", "metal", "water"]
    for season_name, season_data in policy["seasons"].items():
        for elem in elements:
            assert elem in season_data, f"{season_name} missing {elem}"

def test_valid_wang_states(policy):
    """Test all states are valid Wang-Xiang-Xiu-Qiu-Si values."""
    valid_states = {"旺", "相", "休", "囚", "死"}
    for season_name, season_data in policy["seasons"].items():
        for elem, state in season_data.items():
            assert state in valid_states, f"Invalid state {state} in {season_name}.{elem}"

def test_signature_present(policy):
    """Test policy has signature."""
    assert "policy_signature" in policy
    assert len(policy["policy_signature"]) == 64  # SHA-256 hex
```

#### 2-4. Repeat for Other 3 Policies

**Similar pattern for:**
- `strength_grading_tiers_v1.json` - Maps buckets to tier labels
- `yongshin_dual_policy_v1.json` - Dual yongshin selection logic
- `zanggan_table.json` - Hidden stems (地支藏干) mapping

*(Detailed schemas omitted for brevity - follow same structure)*

### Testing Strategy

**Run All Tests:**
```bash
pytest tests/test_seasons_wang_map_policy.py -v
pytest tests/test_strength_grading_tiers_policy.py -v
pytest tests/test_yongshin_dual_policy.py -v
pytest tests/test_zanggan_table_policy.py -v
```

### Risk Assessment

**Technical Risks:**
- ⚠️ **LOW:** Schema may be too restrictive
  - **Mitigation:** Start permissive, tighten incrementally
- ⚠️ **LOW:** Policies may have undocumented fields
  - **Mitigation:** Inspect actual usage before finalizing schema

**Impact:**
- **Medium:** Prevents policy corruption
- **Low:** Catches schema drift early

### Effort Estimate

- **4 schemas × 30 min each:** 2 hours
- **4 test files × 30 min each:** 2 hours
- **Total:** 4 hours

---

## Task #15: Complete Skeleton Services or Mark as WIP (MEDIUM PRIORITY)

### Current State Analysis

**Skeleton Services:**
1. `services/api-gateway/app/main.py` - Only health endpoint
2. `services/llm-polish/app/main.py` - Only health endpoint
3. `services/llm-checker/app/main.py` - Only health endpoint

**Status:**
- ✅ Basic FastAPI structure
- ✅ Health metadata working
- ❌ No business logic routes
- ❌ No tests

### Solution Strategy

**Option A: Mark as WIP (Recommended - 1 minute)**
- Add `WIP` markers in deployment configs
- Add TODO comments in code
- Document what needs implementation

**Option B: Implement Minimal Routes (4-6 hours)**
- Add basic routing logic
- Add stub response handlers
- Add minimal tests

**Recommendation:** Option A - Focus on fixing bugs before adding features

### Implementation (Option A)

#### 1. Update Service Files

**api-gateway/app/main.py:**
```python
"""
API Gateway skeleton for 사주 앱 v1.4.

⚠️ WIP: This service is not production-ready
TODO:
- [ ] Add routing to analysis-service
- [ ] Add routing to llm-polish
- [ ] Add authentication/authorization
- [ ] Add rate limiting
- [ ] Add request logging
"""

from __future__ import annotations

from services.common import create_service_app

APP_META = {
    "app": "saju-api-gateway",
    "version": "0.1.0-WIP",  # ✅ Add -WIP suffix
    "rule_id": "KR_classic_v1.4",
}

app = create_service_app(
    app_name=APP_META["app"],
    version=APP_META["version"],
    rule_id=APP_META["rule_id"],
)

# TODO: Add routes
# @app.post("/analyze")
# def route_to_analysis_service(...): pass
```

#### 2. Update Deployment Configs

**docker-compose.yml (if exists):**
```yaml
services:
  api-gateway:
    image: saju-api-gateway:0.1.0-WIP
    environment:
      - DEPLOYMENT_STAGE=WIP  # ✅ Mark as WIP
    labels:
      - "com.saju.status=WIP"
      - "com.saju.ready=false"
```

#### 3. Add README

**services/api-gateway/README.md:**
```markdown
# API Gateway (WIP)

⚠️ **Status:** Work in Progress - Not Production Ready

## Current State
- ✅ Health endpoint functional
- ❌ Business routes not implemented
- ❌ No tests

## TODO
1. Implement routing to downstream services
2. Add authentication/authorization
3. Add rate limiting
4. Add comprehensive tests
5. Add request/response logging

## Estimated Effort
4-6 hours to reach MVP status
```

### Risk Assessment

**Technical Risks:**
- ✅ **NONE:** No code changes, just documentation

**Impact:**
- **Low:** Makes WIP status explicit
- **Low:** Prevents accidental deployment

### Effort Estimate

- **Update 3 service files:** 3 minutes
- **Add 3 README files:** 6 minutes
- **Update deployment configs:** 1 minute
- **Total:** 10 minutes

---

## Task #16: Package services.common Properly (LOW PRIORITY)

### Current State Analysis

**Problem:**
14+ files use `sys.path.insert()` to access `services.common`, indicating packaging debt.

**Example:**
```python
# services/analysis-service/app/core/relations.py:13
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[4] / "services" / "common"))
from saju_common import Evidence, Metadata  # After path hack
```

**Root Cause:**
`services.common` is a directory but not a proper Python package with setup.py/pyproject.toml.

### Solution Strategy

**Convert to Editable Package:**
1. Create `pyproject.toml` for services.common
2. Install as editable package: `pip install -e services/common`
3. Remove all `sys.path.insert()` hacks
4. Update imports to use package name

### Implementation

#### Step 1: Create pyproject.toml

**services/common/pyproject.toml:**
```toml
[project]
name = "saju-common"
version = "1.0.0"
description = "Common utilities and protocols for Saju microservices"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["saju_common"]
```

#### Step 2: Install as Editable Package

```bash
cd /Users/yujumyeong/coding/\ projects/사주
source .venv/bin/activate
pip install -e services/common
```

#### Step 3: Remove sys.path.insert() Hacks

**Create Script:**
```python
# tools/remove_syspath_hacks.py

#!/usr/bin/env python3
"""Remove sys.path.insert() hacks from codebase."""

import re
from pathlib import Path

def remove_syspath_from_file(file_path: Path):
    """Remove sys.path.insert lines from a Python file."""
    with open(file_path) as f:
        content = f.read()

    # Pattern: sys.path.insert(0, ...)
    pattern = r'^\s*sys\.path\.insert\(0,\s*str\(.*?services.*?common.*?\)\)\s*\n'

    new_content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Also remove now-unused sys and Path imports if they're only for path hacking
    if 'sys.path.insert' not in new_content:
        # Remove 'import sys' if no other sys usage
        if 'sys.' not in new_content:
            new_content = re.sub(r'^\s*import sys\s*\n', '', new_content, flags=re.MULTILINE)

        # Remove Path import if only used for path hacking
        if '_Path(__file__)' not in new_content and 'Path(__file__)' not in new_content:
            new_content = re.sub(
                r'^\s*from pathlib import Path as _Path\s*\n',
                '',
                new_content,
                flags=re.MULTILINE
            )

    if content != new_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Cleaned {file_path}")
        return True
    return False

def main():
    root = Path(__file__).parent.parent / "services"

    # Find all Python files with sys.path.insert
    files_to_clean = []
    for py_file in root.rglob("*.py"):
        with open(py_file) as f:
            if 'sys.path.insert' in f.read():
                files_to_clean.append(py_file)

    print(f"Found {len(files_to_clean)} files to clean")

    cleaned = 0
    for file_path in files_to_clean:
        if remove_syspath_from_file(file_path):
            cleaned += 1

    print(f"\n✅ Cleaned {cleaned} files")

if __name__ == "__main__":
    main()
```

**Run:**
```bash
.venv/bin/python3 tools/remove_syspath_hacks.py
```

#### Step 4: Verify Imports Still Work

**Run All Tests:**
```bash
env PYTHONPATH="." pytest services/analysis-service/tests/ -v
env PYTHONPATH="." pytest services/pillars-service/tests/ -v
env PYTHONPATH="." pytest services/common/tests/ -v
```

### Risk Assessment

**Technical Risks:**
- ⚠️ **MEDIUM:** May break imports if package structure is wrong
  - **Mitigation:** Test thoroughly before committing, keep git branch
- ⚠️ **LOW:** CI/CD may need PYTHONPATH updates
  - **Mitigation:** Document new installation step

**Impact:**
- **High:** Cleaner codebase, proper packaging
- **Medium:** Easier dependency management

### Effort Estimate

- **Create pyproject.toml:** 30 minutes
- **Install and test:** 30 minutes
- **Write cleanup script:** 1 hour
- **Run and validate:** 30 minutes
- **Total:** 2.5 hours

---

## Task #17: Fix Hardcoded tzdb_version (LOW PRIORITY)

### Current State Analysis

**File:** `services/tz-time-service/app/api/routes.py:22`

**Current Code:**
```python
def get_converter(
    detector: TimeEventDetector = Depends(get_event_detector),
) -> TimezoneConverter:
    """Return the converter bound to the current tzdb metadata."""
    return TimezoneConverter(tzdb_version="2025a", event_detector=detector)  # ❌ Hardcoded
```

**Problem:**
- tzdb version should match system's installed tzdata
- Hardcoding will become outdated

### Solution Strategy

**Option A: Introspect from zoneinfo (Recommended)**
```python
import zoneinfo

def get_tzdb_version() -> str:
    """Get installed tzdb version."""
    try:
        return zoneinfo.TZDATA_VERSION
    except AttributeError:
        # Fallback for Python < 3.9 or if unavailable
        return "unknown"
```

**Option B: Read from Config**
```python
# config.py
TZDB_VERSION = os.getenv("TZDB_VERSION", "2025a")
```

**Recommendation:** Option A - Always accurate

### Implementation

**Update routes.py:**
```python
# services/tz-time-service/app/api/routes.py

import zoneinfo

def get_tzdb_version() -> str:
    """Get installed tzdb version from zoneinfo."""
    try:
        return zoneinfo.TZDATA_VERSION
    except AttributeError:
        # Python < 3.9 or tzdata not available
        import importlib.metadata
        try:
            version = importlib.metadata.version("tzdata")
            return version
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

def get_converter(
    detector: TimeEventDetector = Depends(get_event_detector),
) -> TimezoneConverter:
    """Return the converter bound to the current tzdb metadata."""
    return TimezoneConverter(
        tzdb_version=get_tzdb_version(),  # ✅ Dynamic
        event_detector=detector
    )
```

### Testing Strategy

**Unit Test:**
```python
def test_tzdb_version_introspection():
    """Test tzdb version is detected."""
    version = get_tzdb_version()
    assert version != "unknown"
    assert version.startswith("20")  # Year 20xx
```

### Risk Assessment

**Technical Risks:**
- ⚠️ **LOW:** zoneinfo.TZDATA_VERSION not available
  - **Mitigation:** Fallback to importlib.metadata

**Impact:**
- **Low:** Trace metadata always accurate
- **Low:** No manual updates needed

### Effort Estimate

- **Implement:** 15 minutes
- **Test:** 15 minutes
- **Total:** 30 minutes

---

## Execution Plan & Priority Order

### Recommended Sequence

**Phase 1: Quick Wins (1 hour total)**
1. Task #17: Fix tzdb_version (30 min) ⚡
2. Task #15: Mark skeleton services as WIP (10 min) ⚡
3. Task #11: Fix EngineSummaries confidences (2 hours)

**Phase 2: High Priority (4 hours total)**
4. Task #6: Replace TimezoneConverter stub (4 hours) 🔴

**Phase 3: Medium Priority (8.5 hours total)**
5. Task #12: Fix golden test skips (2.5 hours)
6. Task #14: Add support policy validation (4 hours)

**Phase 4: Low Priority Refactoring (2.5 hours total)**
7. Task #16: Package services.common (2.5 hours)

**Total Estimated Time:** 13.5 hours

### Dependency Graph

```
No blocking dependencies between tasks!
All can be done in parallel or any order.

Suggested grouping by developer:
- Backend Dev: Task #6 (TimezoneConverter) + Task #17 (tzdb)
- Test Engineer: Task #12 (golden tests) + Task #14 (policy tests)
- DevOps: Task #15 (WIP markers) + Task #16 (packaging)
- Data Scientist: Task #11 (confidence calculations)
```

---

## Risk Matrix

| Task | Technical Risk | Impact | Effort |
|------|---------------|--------|--------|
| #6   | Medium        | High   | 4h     |
| #11  | Low           | Medium | 2h     |
| #12  | Low           | Medium | 2.5h   |
| #14  | Low           | Medium | 4h     |
| #15  | None          | Low    | 10min  |
| #16  | Medium        | High   | 2.5h   |
| #17  | Low           | Low    | 30min  |

---

## Success Criteria

**Task #6:**
- [ ] Delta-T calculation implemented and tested
- [ ] LMT adjustments calculated correctly
- [ ] TimezoneConverter returns real metadata
- [ ] Unit tests pass (5+ tests)

**Task #11:**
- [ ] Strength confidence calculated dynamically
- [ ] Relation weights loaded from policy
- [ ] Yongshin confidence calculated
- [ ] No hardcoded 0.8/0.75/0.7 values remain

**Task #12:**
- [ ] All 4 pytest.skip() removed
- [ ] Golden cases have Stage-3 expectations
- [ ] All tests pass (35+ tests)

**Task #14:**
- [ ] 4 JSON Schemas created
- [ ] 4 test files created
- [ ] All tests pass (20+ tests)

**Task #15:**
- [ ] WIP markers added to 3 services
- [ ] README files created
- [ ] Deployment configs updated

**Task #16:**
- [ ] pyproject.toml created
- [ ] Package installed as editable
- [ ] All sys.path.insert() removed (14+ files)
- [ ] All tests still pass

**Task #17:**
- [ ] tzdb_version introspected dynamically
- [ ] Hardcoded "2025a" removed
- [ ] Unit test passes

---

## Conclusion

All 7 remaining tasks are well-understood and have clear implementation paths. No blocking dependencies exist, allowing parallel execution.

**Key Insights:**
1. Task #6 (TimezoneConverter) is the most complex but highest impact
2. Tasks #15 and #17 are trivial (< 1 hour combined) and should be done immediately
3. Task #11 improves ML/LLM decision quality significantly
4. Task #16 (packaging) provides long-term maintainability benefits

**Estimated Total Completion Time:** 13.5-19.5 hours (depending on testing depth)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Author:** Claude (Sonnet 4.5)
**Status:** Ready for Implementation
