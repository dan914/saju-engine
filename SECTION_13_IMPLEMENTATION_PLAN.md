# Section 13: Analysis API Integration - Implementation Plan

**Date**: 2025-10-25
**Status**: ✅ CI GREEN - Ready to proceed
**Test Suite**: 705/705 PASSING (100%)

---

## Overview

Section 13 from task list.md (lines 152-163) covers Analysis API Integration. This document outlines the implementation plan for the remaining tasks.

---

## Task Breakdown

### ✅ Task 13.1: AnalysisResponse 스키마 확장 (COMPLETE)

**Status**: COMPLETE ✅

**What was done**:
- Orchestrator output fields already reflected in response schema
- `_map_to_response` updated to pass-through engine results (services/analysis-service/app/core/engine.py)
- Placeholders removed
- Full payload includes: relations_weighted, relations_extras.banhe_groups, ten_gods, twelve_stages, stage3, evidence, engine_summaries, void, yuanjin
- `/analyze` response_model and LLM Guard hooks verified

**Verification**:
```
test_analyze_returns_sample_response PASSED
```

---

### 🔄 Task 13.2: 정책 및 테스트 실거래화 (Policy and Test Realization)

**Status**: IN PROGRESS

#### 13.2.1 Policy Path Audit

**Current State**:
- 35 policy files in `saju_codex_batch_all_v2_6_signed/policies/`
- 13 files have signature verification
- All policy tests passing (no skipped tests found)

**Action Items**:
1. ✅ Audit all policy file paths (COMPLETE)
2. ⏳ Verify signature validation is active
3. ⏳ Check for any hardcoded policy paths that need updating
4. ⏳ Ensure all tests reference policies from correct bundle location

#### 13.2.2 Test Reactivation

**Current State**:
- NO skipped tests found in test suite
- All 705 tests active and passing

**Verification Command**:
```bash
grep -r "pytest.skip\|@pytest.mark.skip\|skipif" services/analysis-service/tests/
# Result: No output (no skipped tests)
```

**Status**: ✅ COMPLETE - No tests to reactivate

---

### 📊 Task 13.3: 골든셋 커버리지 상승 (Golden Set Coverage Expansion)

**Status**: PLANNING

#### Current Golden Set Status

**Existing Golden Tests**:
1. `tests/test_stage3_golden_cases.py` - Stage-3 MVP engines (Climate, Luck Flow, Gyeokguk, Pattern Profiler)
2. `services/analysis-service/tests/test_strength_normalization_regression.py` - Strength calculation regression cases

**Required Golden Cases** (from task list):
- [ ] kr_core_regressions (+118 cases)
- [ ] school_profiles test cases
- [ ] five_he_lab test cases
- [ ] zongge_guard test cases

#### 13.3.1 Generate kr_core_regressions (+118 cases)

**Purpose**: Core regression test suite for Korean saju analysis

**Coverage Requirements**:
- Boundary cases (절입 ±1h, 자시 경계)
- Timezone variations (서울, 부산, 광주, etc.)
- Era variations (1600-2200)
- ΔT edge cases
- LMT vs STD time basis
- Strength calculation edge cases (극신강 ~ 극신약)
- Relationship combinations (육합, 삼합, 충, 형, 파, 해)
- Structure detection (정관격, 정재격, etc.)

**Format**:
```json
{
  "case_id": "kr_core_001",
  "description": "절입 경계 케이스 - 입춘 +30분",
  "input": {
    "birth_dt": "2000-02-04T07:30:00+09:00",
    "tz_str": "Asia/Seoul",
    "mode": "traditional_kr"
  },
  "expect": {
    "pillars": {"year": "庚辰", "month": "戊寅", "day": "乙亥", "hour": "庚辰"},
    "strength": {"bucket": "신약", "score_range": [20, 39]},
    "relations": {"he6": [...], "sanhe": [...], "chong": [...]},
    "structure": {"primary": "정관격", "confidence": "mid"}
  },
  "metadata": {
    "category": "boundary",
    "tags": ["절입", "입춘", "경계"]
  }
}
```

**Implementation**:
1. Create `tests/golden_cases/kr_core/` directory
2. Generate 118 test case JSON files
3. Create parametric test file: `tests/test_kr_core_regressions.py`
4. Verify all cases pass with current implementation

#### 13.3.2 Generate school_profiles Test Cases

**Purpose**: Test school-specific interpretation profiles

**School Profiles** (from claude.md):
- classic: Traditional interpretation
- practical: Modern practical approach
- sanhe: Focus on sanhe (three-harmony) relationships

**Required Cases**: ~30 cases

**Format**:
```json
{
  "case_id": "school_classic_001",
  "description": "Classic school - 정관격 판정",
  "input": {
    "pillars": {...},
    "school_profile": "classic"
  },
  "expect": {
    "structure": {"primary": "정관격"},
    "relation_caps": {"sanhe_transform": false},
    "five_he_scope": "conservative"
  }
}
```

**Implementation**:
1. Create `tests/golden_cases/school_profiles/` directory
2. Generate 30 test cases (10 per school type)
3. Create test file: `tests/test_school_profiles_golden.py`

#### 13.3.3 Generate five_he_lab Test Cases

**Purpose**: Test five-element harmony transformation logic (Lab/Pro feature)

**Required Cases**: ~20 cases

**Coverage**:
- 甲己合土 transformations
- 乙庚合金 transformations
- 丙辛合水 transformations
- 丁壬合木 transformations
- 戊癸合火 transformations
- Transformation conditions (strength, seasonal, supporting elements)

**Format**:
```json
{
  "case_id": "five_he_lab_001",
  "description": "甲己合土 - 변환 성립",
  "input": {
    "pillars": {"year": "甲申", "month": "己巳", "day": "戊辰", "hour": "甲寅"},
    "mode": "lab_transform"
  },
  "expect": {
    "five_he": {
      "pair": ["甲", "己"],
      "result_element": "土",
      "transform_success": true,
      "post_effects": {"day_stem_boosted": true}
    }
  }
}
```

#### 13.3.4 Generate zongge_guard Test Cases

**Purpose**: Test special structure (從格) validation logic

**Required Cases**: ~15 cases

**Types of 從格**:
- 從財格 (following wealth)
- 從殺格 (following officer)
- 從兒格 (following output)
- 從強格 (following strength)
- 從旺格 (following prosperity)

**Format**:
```json
{
  "case_id": "zongge_001",
  "description": "從財格 - 일간 극약 + 財星 강성",
  "input": {
    "pillars": {...},
    "strength": {"bucket": "극신약", "score": 5}
  },
  "expect": {
    "structure": {"primary": "從財格"},
    "zongge_guard": {
      "type": "從財",
      "validation": "pass",
      "conditions_met": ["극신약", "財星강성", "무印比"]
    }
  }
}
```

---

## Implementation Timeline

### Phase 1: Policy Audit (Current)
- [x] Audit policy file paths
- [ ] Verify signature validation
- [ ] Document policy loading patterns
- **ETA**: 1 hour

### Phase 2: Generate Golden Cases
- [ ] kr_core_regressions (+118 cases)
  - **ETA**: 4-6 hours
- [ ] school_profiles cases (30 cases)
  - **ETA**: 2 hours
- [ ] five_he_lab cases (20 cases)
  - **ETA**: 2 hours
- [ ] zongge_guard cases (15 cases)
  - **ETA**: 1.5 hours
- **Total ETA**: 9.5-11.5 hours

### Phase 3: CI Integration
- [ ] Create CI workflow for golden set execution
- [ ] Add regression test job to GitHub Actions
- [ ] Set up failure alerts
- **ETA**: 2 hours

---

## Directory Structure

```
tests/
├── golden_cases/
│   ├── kr_core/
│   │   ├── case_kr_core_001.json
│   │   ├── case_kr_core_002.json
│   │   └── ... (118 total)
│   ├── school_profiles/
│   │   ├── case_classic_001.json
│   │   ├── case_practical_001.json
│   │   ├── case_sanhe_001.json
│   │   └── ... (30 total)
│   ├── five_he_lab/
│   │   ├── case_jia_ji_001.json
│   │   ├── case_yi_geng_001.json
│   │   └── ... (20 total)
│   └── zongge_guard/
│       ├── case_cong_cai_001.json
│       ├── case_cong_sha_001.json
│       └── ... (15 total)
├── test_kr_core_regressions.py
├── test_school_profiles_golden.py
├── test_five_he_lab_golden.py
└── test_zongge_guard_golden.py
```

---

## Success Criteria

### Phase 1 (Policy Audit)
- ✅ All policy paths verified and documented
- ✅ Signature validation active and working
- ✅ All tests reference correct policy bundle

### Phase 2 (Golden Cases)
- ✅ 183 new golden test cases generated (118+30+20+15)
- ✅ All golden tests passing
- ✅ Cases cover all critical scenarios
- ✅ JSON schema validation for all cases

### Phase 3 (CI Integration)
- ✅ Golden set runs in CI pipeline
- ✅ Regression failures block deployment
- ✅ Test coverage report includes golden set

---

## Next Actions

1. ✅ Complete policy path audit
2. ⏳ Start generating kr_core_regressions (first 20 cases)
3. ⏳ Create test infrastructure for golden sets
4. ⏳ Validate test format and execution
5. ⏳ Scale to full 183 cases
6. ⏳ Integrate into CI workflow

---

**Status**: Ready to proceed with golden case generation
**Blockers**: None - CI is green, all infrastructure ready
