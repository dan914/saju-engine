# Missing Features - Detailed Report

**Date:** 2025-10-12 KST
**Test Case:** 2000-09-14, 10:00 AM Seoul, Male (庚辰 乙酉 乙亥 辛巳)
**Orchestrator Version:** 1.2.0

---

## Executive Summary

Out of **22 expected major features**, **13 are working (59%)** and **9 have issues (41%)**:

- ✅ **Working:** 13 features
- ⚠️ **Integration Issues:** 2 features (engines exist but not connected)
- ❌ **Missing/Disabled:** 7 features (not implemented or disabled)

---

## Category 1: Integration Issues (Engines Exist, Not Connected)

### 🔴 CRITICAL #1: Relations_weighted - Empty Items

**Status:** Engine exists, policy exists, but not receiving data

**What's Wrong:**
```json
// Current output:
{
  "relations": {
    "priority_hit": "chong",
    "notes": ["chong:巳/亥"]  ← Detected!
  },
  "relations_weighted": {
    "items": [],              ← Empty!
    "summary": {"total": 0}
  }
}
```

**Expected Output:**
```json
{
  "relations_weighted": {
    "policy_version": "relation_weight_v1.0.0",
    "items": [
      {
        "type": "chong",
        "participants": ["巳", "亥"],
        "positions": [3, 2],  // hour, day
        "impact_weight": 0.90,
        "formed": true,
        "hua": false,
        "element": null
      }
    ],
    "summary": {
      "total": 1,
      "by_type": {
        "chong": {"count": 1, "avg_weight": 0.90}
      }
    }
  }
}
```

**Root Cause:**
- RelationTransformer detects: `chong:巳/亥`
- RelationWeightEvaluator exists and works (tested independently)
- **BUT**: Orchestrator not passing detected relations to evaluator

**Files Involved:**
- ✅ `services/analysis-service/app/core/relations.py` (RelationTransformer)
- ✅ `services/analysis-service/app/core/relation_weight.py` (RelationWeightEvaluator)
- ❌ `services/analysis-service/app/core/saju_orchestrator.py` (integration missing)

**Fix Required:**
```python
# In saju_orchestrator.py, around line 200-250
relations_output = self.relation_transformer.transform(pillars)

# Add this:
if relations_output:
    # Extract detected relations from RelationTransformer output
    detected_relations = []
    for rel_type in ['he6', 'sanhe', 'chong', 'xing', 'po', 'hai']:
        if rel_type in relations_output:
            for item in relations_output[rel_type]:
                detected_relations.append({
                    'type': rel_type,
                    'participants': item.get('pair', []),
                    **item
                })

    # Pass to RelationWeightEvaluator
    weighted = self.relation_weight_evaluator.evaluate(detected_relations)
    result['relations_weighted'] = weighted
```

**Priority:** 🔴 HIGH (working engine not utilized)

---

### 🟡 MEDIUM #2: Shensha - Disabled

**Status:** Engine exists, policy exists, but disabled by flag

**What's Wrong:**
```json
{
  "shensha": {
    "enabled": false,  ← Disabled!
    "list": []
  }
}
```

**Expected Output:**
```json
{
  "shensha": {
    "enabled": true,
    "policy_version": "shensha_v2_policy",
    "list": [
      {
        "name": "천을귀인",
        "name_ko": "天乙貴人",
        "category": "noble",
        "pillar": "day",
        "branch": "酉",
        "description": "Noble person star - brings helpful people"
      },
      {
        "name": "역마",
        "name_ko": "驛馬",
        "category": "movement",
        "pillar": "year",
        "branch": "巳",
        "description": "Traveling horse - indicates movement and change"
      }
      // ... more shensha items
    ]
  }
}
```

**Root Cause:**
- ShenshaCatalog exists in `services/analysis-service/app/core/luck.py`
- Policy file exists: `shensha_v2_policy.json`
- **BUT**: `enabled: false` flag set somewhere

**Files Involved:**
- ✅ `services/analysis-service/app/core/luck.py` (ShenshaCatalog)
- ✅ `saju_codex_batch_all_v2_6_signed/policies/shensha_v2_policy.json`
- ❓ Orchestrator or config setting `enabled: false`

**Expected Shensha for Test Case:**

For 庚辰 乙酉 乙亥 辛巳, should include:
- **천을귀인 (天乙貴人):** Year stem 庚 → 丑/未
- **문창귀인 (文昌貴人):** Day stem 乙 → 午
- **역마 (驛馬):** Year branch 辰 → 寅
- **도화 (桃花):** Year branch 辰 → 酉 ✓ (month has it!)
- **화개 (華蓋):** Day branch 亥 → 未

**Fix Required:**
```python
# Find where shensha is initialized in orchestrator
# Change from:
shensha_result = {"enabled": false, "list": []}

# To:
shensha_result = self.shensha_catalog.evaluate(pillars)
shensha_result["enabled"] = True
```

**Priority:** 🟡 MEDIUM (feature exists but disabled - might be intentional)

---

## Category 2: Missing Core Features (Not Implemented)

### 🔴 CRITICAL #3: Ten Gods (十神)

**Status:** Completely missing from output

**What's Wrong:**
- No `ten_gods` key in result
- No summary of ten gods per pillar
- No ten god relationships

**Expected Output:**
```json
{
  "ten_gods": {
    "policy_version": "branch_tengods_policy",
    "by_pillar": {
      "year": {
        "stem": "庚",
        "vs_day": "正官",  // 庚 vs 乙
        "branch": "辰",
        "hidden": {
          "戊": "偏財",
          "乙": "比肩",
          "癸": "偏印"
        }
      },
      "month": {
        "stem": "乙",
        "vs_day": "比肩",  // 乙 vs 乙
        "branch": "酉",
        "hidden": {
          "辛": "正官"
        }
      },
      "day": {
        "stem": "乙",
        "vs_day": "日主",
        "branch": "亥",
        "hidden": {
          "壬": "正印",
          "甲": "劫財"
        }
      },
      "hour": {
        "stem": "辛",
        "vs_day": "正官",  // 辛 vs 乙
        "branch": "巳",
        "hidden": {
          "丙": "傷官",
          "戊": "偏財",
          "庚": "正官"
        }
      }
    },
    "summary": {
      "比肩": 2,
      "劫財": 1,
      "食神": 0,
      "傷官": 1,
      "偏財": 2,
      "正財": 0,
      "偏官": 0,
      "正官": 4,  // 庚, 辛 (stems) + 辛 (hidden)
      "偏印": 1,
      "正印": 1
    },
    "dominant": ["正官", "比肩"],
    "missing": ["食神", "正財", "偏官"]
  }
}
```

**Files Involved:**
- ❓ No dedicated ten gods engine found
- ✅ Policy exists: `branch_tengods_policy.json`
- ❓ TenGodsCalculator mentioned in CLAUDE.md but not found

**Implementation Needed:**
1. Create `services/analysis-service/app/core/ten_gods.py`
2. Implement TenGodsCalculator class
3. Calculate stem-to-stem relationships (vs day master)
4. Calculate hidden stems from branches (zanggan)
5. Aggregate summary and dominant types

**Priority:** 🔴 HIGH (fundamental feature for saju analysis)

---

### 🔴 CRITICAL #4: Twelve Stages / Lifecycle (12운성)

**Status:** Policy exists but not integrated

**What's Wrong:**
- No `lifecycle` or `twelve_stages` key in result
- Policy file exists: `lifecycle_stages.json`
- Not calculated or returned

**Expected Output:**
```json
{
  "twelve_stages": {
    "policy_version": "lifecycle_stages_v1",
    "by_pillar": {
      "year": {
        "stem": "庚",
        "branch": "辰",
        "stage": "養",
        "stage_ko": "양",
        "strength": "weak",
        "description": "Nourishment stage"
      },
      "month": {
        "stem": "乙",
        "branch": "酉",
        "stage": "死",
        "stage_ko": "사",
        "strength": "extremely_weak",
        "description": "Death stage - weakest position"
      },
      "day": {
        "stem": "乙",
        "branch": "亥",
        "stage": "長生",
        "stage_ko": "장생",
        "strength": "strong",
        "description": "Birth/longevity stage"
      },
      "hour": {
        "stem": "辛",
        "branch": "巳",
        "stage": "胎",
        "stage_ko": "태",
        "strength": "weak",
        "description": "Embryo stage"
      }
    },
    "day_master_stage": {
      "stage": "長生",
      "at_pillar": "day",
      "meaning": "Day master 乙木 in 亥水 is at birth stage - very favorable"
    }
  }
}
```

**12 Stages Reference:**
1. 長生 (장생) - Birth/Longevity - Strong
2. 沐浴 (목욕) - Bathing - Moderate
3. 冠帶 (관대) - Capping - Moderate
4. 臨官 (임관) - Official - Strong
5. 帝旺 (제왕) - Emperor - Strongest
6. 衰 (쇠) - Decline - Weak
7. 病 (병) - Illness - Weak
8. 死 (사) - Death - Very weak
9. 墓 (묘) - Tomb - Very weak
10. 絕 (절) - Extinction - Weakest
11. 胎 (태) - Embryo - Moderate
12. 養 (양) - Nourishment - Moderate

**Files Involved:**
- ✅ Policy: `saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json`
- ❌ No engine implementation found
- ❓ Mentioned in CLAUDE.md as "not integrated"

**Implementation Needed:**
1. Create `services/analysis-service/app/core/lifecycle.py`
2. Implement TwelveStageCalculator class
3. Map each pillar stem to its stage in the branch
4. Calculate day master's stage (most important)
5. Integrate into orchestrator

**Priority:** 🔴 HIGH (fundamental for strength analysis)

---

### 🟡 MEDIUM #5: Luck Pillars (大運干支)

**Status:** Start age calculated, but no pillars generated

**What's Wrong:**
```json
{
  "luck": {
    "direction": "forward",
    "start_age": 7.9798,
    "method": "traditional_sex",
    "pillars": []  ← Empty!
  }
}
```

**Expected Output:**
```json
{
  "luck": {
    "direction": "forward",
    "start_age": 7.9798,
    "method": "traditional_sex",
    "pillars": [
      {
        "pillar": "甲申",
        "start_age": 7.98,
        "end_age": 17.98,
        "decade": 1
      },
      {
        "pillar": "癸未",
        "start_age": 17.98,
        "end_age": 27.98,
        "decade": 2
      },
      {
        "pillar": "壬午",
        "start_age": 27.98,
        "end_age": 37.98,
        "decade": 3
      },
      // ... 7 more decades
    ],
    "current_luck": {
      "pillar": "癸未",  // For 2025 (age 25)
      "decade": 2,
      "years_into_decade": 7
    }
  }
}
```

**Calculation Method:**
1. Start from month pillar: 乙酉
2. Direction: forward (male, yang year 庚)
3. Start age: 7.98
4. Generate next 10 pillars in sequence

**Files Involved:**
- ✅ `services/analysis-service/app/core/luck.py` (LuckCalculator)
- ✅ Policy: `luck_pillars_policy.json`
- ❓ Pillar generation logic might be incomplete

**Implementation Needed:**
1. Extend LuckCalculator to generate pillar sequence
2. Calculate 10 decades from month pillar
3. Determine current luck period based on birth date
4. Add pillars to output

**Priority:** 🟡 MEDIUM (start age works, just missing pillar list)

---

### 🟢 LOW #6: Nayin (納音)

**Status:** Completely missing

**What's Wrong:**
- No `nayin` key in result
- 60甲子 nayin not calculated

**Expected Output:**
```json
{
  "nayin": {
    "year": {
      "pillar": "庚辰",
      "nayin": "白蠟金",
      "nayin_en": "White Wax Metal",
      "element": "金",
      "description": "Refined metal, jewelry quality"
    },
    "month": {
      "pillar": "乙酉",
      "nayin": "泉中水",
      "nayin_en": "Spring Water",
      "element": "水",
      "description": "Spring water, clear and flowing"
    },
    "day": {
      "pillar": "乙亥",
      "nayin": "山頭火",
      "nayin_en": "Mountain Top Fire",
      "element": "火",
      "description": "Beacon fire on mountaintop"
    },
    "hour": {
      "pillar": "辛巳",
      "nayin": "白蠟金",
      "nayin_en": "White Wax Metal",
      "element": "金",
      "description": "Refined metal, jewelry quality"
    }
  }
}
```

**60甲子 Nayin Table:**
Each pair of pillars (e.g., 甲子乙丑) shares a nayin element:
- 甲子乙丑 → 海中金 (Sea Metal)
- 丙寅丁卯 → 爐中火 (Furnace Fire)
- 庚辰辛巳 → 白蠟金 (White Wax Metal) ✓
- etc. (30 pairs total)

**Files Involved:**
- ❓ No nayin calculator found
- ❓ No nayin policy file found
- Reference: `design/nayin_glossary_en.md` exists

**Implementation Needed:**
1. Create nayin lookup table (60甲子 → 30 nayin types)
2. Create `services/analysis-service/app/core/nayin.py`
3. Implement NayinCalculator class
4. Integrate into orchestrator

**Priority:** 🟢 LOW (supplementary feature, less critical)

---

### 🟢 LOW #7: Day Master Details

**Status:** Missing detailed analysis

**What's Wrong:**
- No `day_master` or `day_pillar_info` key
- No personality/characteristics analysis

**Expected Output:**
```json
{
  "day_master": {
    "pillar": "乙亥",
    "stem": "乙",
    "branch": "亥",
    "element": "木",
    "yin_yang": "陰",
    "animal": "豬",
    "characteristics": {
      "personality": "Flexible, gentle, artistic",
      "strengths": ["Adaptable", "Creative", "Diplomatic"],
      "challenges": ["Indecisive", "Overthinking", "Sensitive"],
      "career": "Arts, design, counseling, education",
      "health": "Liver, nervous system attention needed"
    },
    "stem_branch_relationship": {
      "type": "生",
      "description": "亥水 generates 乙木 - very favorable",
      "strength": "strong"
    }
  }
}
```

**Files Involved:**
- ❓ No day master analysis engine found
- Could leverage existing:
  - `sixty_jiazi.json` for pillar characteristics
  - Strength evaluation for power level
  - Ten gods for relationship dynamics

**Implementation Needed:**
1. Create day master characteristics database
2. Link to personality traits
3. Correlate with strength grade
4. Add career/health suggestions

**Priority:** 🟢 LOW (nice-to-have, interpretive content)

---

## Category 3: Expected Missing (Separate Endpoints)

### 🔵 INFO #8: Annual Luck (年運)

**Status:** Not expected in base analysis

**Note:** This is likely a separate API endpoint

**Expected Endpoint:**
```
POST /luck/annual
{
  "pillars": {...},
  "target_year": 2025
}
```

**Expected Output:**
```json
{
  "year": 2025,
  "year_pillar": "乙巳",
  "interactions": {
    "with_birth_chart": [...],
    "with_current_luck": [...]
  },
  "auspicious_months": [2, 5, 8, 11],
  "challenging_months": [4, 10],
  "overall_trend": "moderate"
}
```

**Priority:** 🔵 INFO (separate feature, documented as not implemented)

---

### 🔵 INFO #9: Monthly Luck (月運)

**Status:** Not expected in base analysis

**Note:** This is likely a separate API endpoint

**Expected Endpoint:**
```
POST /luck/monthly
{
  "pillars": {...},
  "year": 2025,
  "month": 10
}
```

**Priority:** 🔵 INFO (separate feature, documented as not implemented)

---

## Summary Table

| # | Feature | Status | Severity | Engine Exists | Policy Exists | Integrated |
|---|---------|--------|----------|---------------|---------------|------------|
| 1 | Relations_weighted | Integration issue | 🔴 CRITICAL | ✅ | ✅ | ❌ |
| 2 | Shensha | Disabled | 🟡 MEDIUM | ✅ | ✅ | ⚠️ Flag off |
| 3 | Ten Gods | Missing | 🔴 CRITICAL | ❌ | ✅ | ❌ |
| 4 | Twelve Stages | Missing | 🔴 CRITICAL | ❌ | ✅ | ❌ |
| 5 | Luck Pillars | Incomplete | 🟡 MEDIUM | ⚠️ Partial | ✅ | ⚠️ Partial |
| 6 | Nayin | Missing | 🟢 LOW | ❌ | ❌ | ❌ |
| 7 | Day Master Details | Missing | 🟢 LOW | ❌ | ⚠️ Partial | ❌ |
| 8 | Annual Luck | Expected missing | 🔵 INFO | ❌ | ❌ | N/A |
| 9 | Monthly Luck | Expected missing | 🔵 INFO | ❌ | ❌ | N/A |

---

## Priority Action Items

### 🔴 CRITICAL (Fix Immediately)

1. **Fix Relations_weighted Integration**
   - Effort: 1-2 hours
   - File: `saju_orchestrator.py`
   - Action: Connect RelationTransformer output to RelationWeightEvaluator

2. **Implement Ten Gods Calculator**
   - Effort: 4-6 hours
   - File: Create `ten_gods.py`
   - Action: Full implementation with policy integration

3. **Implement Twelve Stages**
   - Effort: 4-6 hours
   - File: Create `lifecycle.py`
   - Action: Full implementation with policy integration

### 🟡 MEDIUM (Fix Soon)

4. **Enable Shensha**
   - Effort: 30 minutes
   - Action: Find and toggle enabled flag

5. **Complete Luck Pillars Generation**
   - Effort: 2-3 hours
   - File: `luck.py`
   - Action: Add pillar sequence generation

### 🟢 LOW (Nice to Have)

6. **Implement Nayin**
   - Effort: 2-3 hours
   - Action: Create nayin calculator with 60甲子 table

7. **Add Day Master Details**
   - Effort: 3-4 hours
   - Action: Create characteristics database and analysis

---

## Comparison: Before vs After Strength Fix

### Before Strength Fix:
- 12/22 features working (55%)
- 1 critical bug (strength grading)

### After Strength Fix:
- 13/22 features working (59%)
- 0 critical bugs in working features
- 3 critical features missing (Ten Gods, Twelve Stages, Relations_weighted)

---

## Estimated Total Effort

| Priority | Features | Hours | Cumulative |
|----------|----------|-------|------------|
| 🔴 CRITICAL | 3 features | 9-14 hours | 9-14 hours |
| 🟡 MEDIUM | 2 features | 2.5-3.5 hours | 11.5-17.5 hours |
| 🟢 LOW | 2 features | 5-7 hours | 16.5-24.5 hours |
| **TOTAL** | **7 features** | **16.5-24.5 hours** | **~3 days** |

---

**Report Generated:** 2025-10-12 KST
**Test Case:** 2000-09-14, 10:00 AM Seoul, Male
**Next Action:** Fix Relations_weighted integration (1-2 hours, high impact)
