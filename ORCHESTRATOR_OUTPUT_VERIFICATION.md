# Orchestrator Output Verification - 2000-09-14 Test Case

**Date:** 2025-10-12 KST
**Test Case:** 2000-09-14, 10:00 AM Seoul, Male (庚辰 乙酉 乙亥 辛巳)

---

## ✅ WORKING FEATURES

### 1. 강약 (Strength) ✅
- **Raw Score:** -11.0
- **Normalized:** 31.05
- **Grade:** 신약
- **Phase:** 死
- **Status:** FIXED (was 극신약, now correct)

### 2. 공망 (Void/Kong) ✅
- **Policy Version:** void_calc_v1.1.0
- **Kong (空亡):** ['申', '酉']
- **Day Index:** 11 (乙亥)
- **Xun Start:** 10
- **Hit Branches:** ['酉'] ← 月支 has void!
- **Status:** WORKING

### 3. 원진 (Yuanjin) ✅
- **Policy Version:** yuanjin_v1.1.0
- **Present Branches:** ['辰', '酉', '亥', '巳']
- **Hits:** [] (none in this chart)
- **Pair Count:** 0
- **Status:** WORKING (correctly finds no yuanjin pairs)

### 4. 관계 (Relations) ✅
- **Priority Hit:** chong (충)
- **Transform To:** None
- **Notes:** ['chong:巳/亥'] ← Hour/Day clash detected
- **Status:** WORKING

### 5. 용신 (Yongshin) ✅
- **Policy Version:** yongshin_dual_v1
- **Primary:** 수 (Water, score: 0.42)
- **Secondary:** 목 (Wood, score: 0.15)
- **Confidence:** 0.87
- **Yongshin:** ['수']
- **Bojosin:** ['목']
- **Status:** WORKING

### 6. 대운 (Luck) ✅
- **Direction:** forward (순행)
- **Start Age:** 7.98 years
- **Method:** traditional_sex
- **Status:** WORKING (no longer hardcoded!)

### 7. 조후 (Climate) ✅
- **Temp Bias:** neutral
- **Humid Bias:** neutral
- **Advice Bucket:** []
- **Status:** WORKING

### 8. Stage 3 Engines ✅
All 4 engines running:

#### a) Luck Flow
- **Engine:** luck_flow
- **Policy:** luck_flow_policy_v1
- **Trend:** stable
- **Status:** WORKING

#### b) Gyeokguk (격국)
- **Engine:** gyeokguk_classifier
- **Policy:** gyeokguk_policy_v1
- **Type:** 정격 (standard structure)
- **Status:** WORKING

#### c) Climate Advice
- **Engine:** climate_advice
- **Policy:** climate_advice_policy_v1
- **Status:** WORKING

#### d) Pattern Profiler
- **Engine:** pattern_profiler
- **Policy:** pattern_profiler_policy_v1
- **Patterns Found:** 3
- **Status:** WORKING

### 9. Evidence System ✅
- **Evidence Version:** evidence_v1.0.0
- **Sections:** 3 (void, wuxing_adjust, yuanjin)
- **Status:** WORKING

### 10. Engine Summaries ✅
- **Strength Summary:** Present
- **Relation Summary:** Present
- **Yongshin Summary:** Present
- **Climate Summary:** Present
- **Status:** WORKING

### 11. Guards ✅
- **LLM Guard:** enabled: true, ready_for_llm: true
- **Text Guard:** enabled: true, guard_available: true
- **Status:** WORKING

---

## ⚠️ ISSUES FOUND

### Issue 1: 신살 (Shensha) - DISABLED
```json
{
  "enabled": false,
  "list": []
}
```

**Expected:** Should contain shensha items like:
- 천을귀인 (天乙貴人)
- 문창귀인 (文昌貴人)
- 역마 (驛馬)
- 도화 (桃花)
- etc.

**Status:** Feature is disabled (intentional?)

**Action Needed:** Check if shensha should be enabled by default

---

### Issue 2: Relations_weighted - Empty Items
```json
{
  "policy_version": "relation_weight_v1.0.0",
  "items": [],
  "summary": {
    "total": 0,
    "by_type": {
      "chong": {"count": 0, "avg_weight": 0.0}
    }
  }
}
```

**Expected:** Should contain the detected chong relationship:
```json
{
  "items": [
    {
      "type": "chong",
      "participants": ["巳", "亥"],
      "impact_weight": 0.90,
      "formed": true
    }
  ]
}
```

**Root Cause:** Relations detected (chong:巳/亥) but not being passed to RelationWeightEvaluator

**Status:** Integration issue between RelationTransformer and RelationWeightEvaluator

**Action Needed:** Check orchestrator integration logic

---

## SUMMARY

### Working (13/15) ✅
1. ✅ Strength evaluation (FIXED!)
2. ✅ Void/Kong (공망)
3. ✅ Yuanjin (원진)
4. ✅ Relations detection
5. ✅ Yongshin
6. ✅ Luck calculation
7. ✅ Climate evaluation
8. ✅ Luck Flow
9. ✅ Gyeokguk
10. ✅ Climate Advice
11. ✅ Pattern Profiler
12. ✅ Evidence system
13. ✅ Guards (LLM + Text)

### Issues (2/15) ⚠️
1. ⚠️ Shensha - Disabled
2. ⚠️ Relations_weighted - Items not populated

**Overall:** 87% working (13/15 features)

---

## COMPARISON TO ORIGINAL BUG REPORT

### From test_result_2000_09_14_detailed.json

#### BEFORE (Original Bug Report):
```json
{
  "strength": {
    "score_raw": -11.0,
    "score": 0.0,          ← WRONG (clamped)
    "grade_code": "극신약"  ← WRONG
  },
  "relations_weighted": {
    "items": []            ← WRONG (empty)
  },
  "shensha": {
    "enabled": false,
    "list": []             ← WRONG (empty)
  }
}
```

#### AFTER (Current Results):
```json
{
  "strength": {
    "score_raw": -11.0,
    "score": 31.05,        ← FIXED ✅
    "grade_code": "신약"   ← FIXED ✅
  },
  "relations_weighted": {
    "items": []            ← STILL EMPTY ⚠️
  },
  "shensha": {
    "enabled": false,
    "list": []             ← STILL EMPTY ⚠️
  }
}
```

**Progress:** 1 critical bug fixed, 2 integration issues remain

---

## RECOMMENDATIONS

### Priority 1: Relations_weighted Integration
The RelationWeightEvaluator exists and works, but isn't receiving the detected relations from RelationTransformer. Need to check the orchestrator's data flow between these engines.

**Location:** `services/analysis-service/app/core/saju_orchestrator.py`

### Priority 2: Shensha Enable Flag
Check if shensha should be enabled by default. The ShenshaCatalog exists and is integrated into the orchestrator.

**Location:** Check orchestrator initialization or configuration

### Priority 3: Verify All Edge Cases
Test with charts that have:
- Multiple yuanjin pairs
- Multiple relation types
- Different shensha combinations

---

**Report Generated:** 2025-10-12 KST
**Test Case:** 2000-09-14, 10:00 AM Seoul, Male
**Orchestrator Version:** 1.2.0
