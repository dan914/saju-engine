# Golden Set Generation Summary

**Date**: 2025-10-25
**Status**: ✅ CI GREEN - Ready to generate
**Test Suite**: 705/705 PASSING (100%)

---

## Executive Summary

All 705 tests are passing. We're ready to proceed with Section 13.3: Golden Set Coverage Expansion as outlined in task list.md (lines 160-163).

**Target from manifest_v2_6.json**: 240 total golden cases

---

## Current State

### Existing Golden Cases

**Location 1**: `tests/golden_cases/` (20 cases)
- Format: Stage-3 MVP engines (Climate Advice, Luck Flow, Gyeokguk, Pattern Profiler)
- Files: case_01.json through case_20.json
- Test: `tests/test_stage3_golden_cases.py`

**Location 2**: `saju_codex_batch_all_v2_6_signed/goldens/samples/` (2 samples)
- BOUNDARY_2025_LICHUN_PM1S.json - Boundary case (절입 경계)
- LEAP_2025_YUN6_CROSS.json - Leap month case (윤월)

### Target Distribution (from manifest_v2_6.json)

| Category | Target Count | Status |
|----------|--------------|--------|
| kr_core_regressions | 120 | 📝 TO GENERATE |
| school_profiles | 30 | 📝 TO GENERATE |
| five_he_struct_transform_lab | 50 | 📝 TO GENERATE |
| zongge_guard_cases | 40 | 📝 TO GENERATE |
| **TOTAL** | **240** | **0/240 (0%)** |

---

## Golden Case Format Analysis

### Format 1: Stage-3 MVP (existing tests/golden_cases/)

```json
{
  "id": "SPRING_WOOD_OVER_FIRE",
  "context": {
    "season": "봄",
    "year": 2026
  },
  "strength": {
    "phase": "왕",
    "elements": {...}
  },
  "relation": {"flags": []},
  "climate": {...},
  "yongshin": {"primary": "화"},
  "expect": {
    "climate_policy_id": "WOOD_OVER_FIRE_WEAK"
  }
}
```

### Format 2: Boundary/Regression (codex goldens/samples/)

```json
{
  "case_id": "BOUNDARY_2025_LICHUN_PM1S",
  "input": {
    "local_dt": "2025-02-04T00:00:00.000",
    "timezone": "Asia/Seoul",
    "location": "Seoul, KR"
  },
  "expected": {
    "flags": {"near_term_boundary": true},
    "badges": ["near_term_boundary"]
  },
  "tzdb_version": "2025a",
  "terms_dataset_version": "v1_2025",
  "deltaT_policy_version": "1.2"
}
```

---

## Generation Plan

### Phase 1: kr_core_regressions (120 cases)

**Categories**:
1. **Boundary Cases** (30 cases)
   - 절입 경계 (24절기 × 1-2 cases each)
   - 자시 경계 (子時 23:00-01:00)
   - 입춘 전후 연주 변경
   - 윤달 처리

2. **Timezone Variations** (20 cases)
   - 서울 (Asia/Seoul, LMT -32min)
   - 부산 (129.075°E, LMT -24min)
   - 광주 (126.853°E, LMT -36min)
   - 제주 (126.532°E, LMT -38min)
   - 평양 (125.754°E, LMT -40min)

3. **Era Variations** (20 cases)
   - 1600-1800 (historical ΔT)
   - 1800-1900 (industrial era)
   - 1900-2000 (modern era)
   - 2000-2100 (contemporary)
   - 2100-2200 (future projections)

4. **Strength Edge Cases** (25 cases)
   - 극신강 (score 80-100)
   - 신강 (score 60-79)
   - 중화 (score 40-59)
   - 신약 (score 20-39)
   - 극신약 (score 0-19)
   - Boundary scores (19, 20, 39, 40, 59, 60, 79, 80)

5. **Relationship Combinations** (15 cases)
   - 육합 (6 pairs)
   - 삼합 (4 trines)
   - 충 (6 clashes)
   - 형/파/해 combinations

6. **Structure Detection** (10 cases)
   - 정관격, 정재격, 식신격, 상관격
   - 편관격, 편재격, 편인격, 정인격
   - Special structures

**Format Template**:
```json
{
  "case_id": "kr_core_001",
  "category": "boundary",
  "description": "입춘 경계 +30분 - 년주 변경 확인",
  "input": {
    "birth_dt": "2025-02-04T00:30:00+09:00",
    "tz_str": "Asia/Seoul",
    "mode": "traditional_kr",
    "zi_hour_mode": "default"
  },
  "expected": {
    "pillars": {
      "year": "甲辰",
      "month": "戊寅",
      "day": "...",
      "hour": "..."
    },
    "strength": {
      "bucket": "중화",
      "score_range": [40, 59]
    },
    "relations": {
      "he6": [],
      "sanhe": [],
      "chong": []
    },
    "structure": {
      "primary": "정관격",
      "confidence": "high"
    },
    "metadata": {
      "lmt_offset": -32,
      "dst_applied": false,
      "zi_transition": false
    }
  },
  "metadata": {
    "tags": ["boundary", "lichun", "year_pillar"],
    "difficulty": "medium",
    "tzdb_version": "2025a",
    "terms_dataset_version": "v1_2025"
  }
}
```

### Phase 2: school_profiles (30 cases)

**Distribution**:
- Classic school: 10 cases
- Practical school: 10 cases
- Sanhe school: 10 cases

**Key Differences**:
- relation_caps (sanhe_transform enabled/disabled)
- five_he_scope (conservative/moderate/liberal)
- structure interpretation strictness

### Phase 3: five_he_struct_transform_lab (50 cases)

**Distribution**:
- 甲己合土: 10 cases
- 乙庚合金: 10 cases
- 丙辛合水: 10 cases
- 丁壬合木: 10 cases
- 戊癸合火: 10 cases

**Coverage**:
- Successful transformations
- Failed transformations (missing conditions)
- Seasonal factors
- Supporting element requirements
- Post-transformation effects

### Phase 4: zongge_guard_cases (40 cases)

**Distribution**:
- 從財格: 8 cases
- 從殺格: 8 cases
- 從兒格: 8 cases
- 從強格: 8 cases
- 從旺格: 8 cases

**Validation Tests**:
- Strength requirements (極弱/極強)
- Supporting element presence
- Absence of counter elements
- Seasonal appropriateness

---

## Directory Structure (Proposed)

```
tests/
└── golden_cases/
    ├── kr_core/
    │   ├── boundary/
    │   │   ├── kr_core_001_lichun_plus30m.json
    │   │   ├── kr_core_002_lichun_minus30m.json
    │   │   └── ... (30 total)
    │   ├── timezone/
    │   │   ├── kr_core_031_seoul_lmt.json
    │   │   ├── kr_core_032_busan_lmt.json
    │   │   └── ... (20 total)
    │   ├── era/
    │   │   ├── kr_core_051_era_1700.json
    │   │   └── ... (20 total)
    │   ├── strength/
    │   │   ├── kr_core_071_extreme_strong.json
    │   │   └── ... (25 total)
    │   ├── relations/
    │   │   ├── kr_core_096_he6_zi_chou.json
    │   │   └── ... (15 total)
    │   └── structure/
    │       ├── kr_core_111_zhengguan.json
    │       └── ... (10 total)
    ├── school_profiles/
    │   ├── classic/
    │   ├── practical/
    │   └── sanhe/
    ├── five_he_lab/
    │   ├── jia_ji/
    │   ├── yi_geng/
    │   ├── bing_xin/
    │   ├── ding_ren/
    │   └── wu_gui/
    └── zongge_guard/
        ├── cong_cai/
        ├── cong_sha/
        ├── cong_er/
        ├── cong_qiang/
        └── cong_wang/
```

---

## Test Runner Structure

### Test Files to Create

1. `tests/test_kr_core_golden.py` - Parametric test for 120 kr_core cases
2. `tests/test_school_profiles_golden.py` - Parametric test for 30 school cases
3. `tests/test_five_he_lab_golden.py` - Parametric test for 50 five_he cases
4. `tests/test_zongge_guard_golden.py` - Parametric test for 40 zongge cases

### Test Pattern (Example)

```python
import pytest
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "golden_cases" / "kr_core"
CASES = []

for category_dir in GOLDEN_DIR.iterdir():
    if category_dir.is_dir():
        for case_file in sorted(category_dir.glob("*.json")):
            with open(case_file) as f:
                case = json.load(f)
                case["_file"] = case_file.name
                CASES.append(case)

@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_kr_core_golden(case):
    """Test against kr_core golden case."""
    from app.core.engine import AnalysisEngine
    from app.models import AnalysisRequest

    # Build request from case input
    request = AnalysisRequest(
        pillars={...},  # Computed from birth_dt
        options=case["input"]
    )

    engine = AnalysisEngine()
    result = engine.analyze(request)

    # Validate expected results
    assert result.pillars == case["expected"]["pillars"]
    assert result.strength.bucket == case["expected"]["strength"]["bucket"]
    # ... more assertions
```

---

## Implementation Timeline

| Phase | Task | Cases | ETA |
|-------|------|-------|-----|
| 1a | kr_core boundary cases | 30 | 2h |
| 1b | kr_core timezone cases | 20 | 1.5h |
| 1c | kr_core era cases | 20 | 1.5h |
| 1d | kr_core strength cases | 25 | 2h |
| 1e | kr_core relations cases | 15 | 1h |
| 1f | kr_core structure cases | 10 | 1h |
| 2 | school_profiles cases | 30 | 2h |
| 3 | five_he_lab cases | 50 | 3h |
| 4 | zongge_guard cases | 40 | 2.5h |
| 5 | Test runners | 4 files | 1h |
| 6 | Validation & debugging | - | 2h |
| **TOTAL** | | **240** | **19h** |

---

## Next Steps

1. ✅ Create kr_core/boundary directory
2. ✅ Generate first 10 boundary cases
3. ✅ Create test runner prototype
4. ✅ Validate format and execution
5. ⏳ Scale to remaining 230 cases
6. ⏳ Integrate into CI workflow

---

**Status**: Ready to begin generation
**First Milestone**: 10 kr_core boundary cases (30 minutes)
