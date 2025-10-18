# Missing Policies and Integrations - AI Handover Report

**Date**: 2025-10-05
**Purpose**: Complete handover documentation for AI assistants to implement missing policy files and engine integrations
**Context**: Saju (Four Pillars of Destiny) calculation engine codebase
**Status**: Production-ready architecture, missing specific policy files and integration code

---

## Executive Summary

The Saju calculation engine has a **policy-driven architecture** where all business logic is externalized to JSON policy files validated by JSON schemas. The core engine structure is complete, but **2 critical policy files** are missing, and **3 engine integrations** need to be updated to use the new v1.1 policies.

### Missing Components

#### 🔴 Critical (Blocking)
1. **sixty_jiazi.json** - 60-stem cycle policy (MISSING)
2. **branch_tengods_policy.json** - Branch Ten Gods logic policy (MISSING)

#### 🟡 Medium Priority (Integration)
3. **LuckCalculator** integration - Update to use luck_pillars_policy v1.1
4. **Elements calculation** integration - Use elements_distribution_criteria v1.1
5. **Lifecycle stages** integration - Use lifecycle_stages v1.1

---

## 🔴 MISSING POLICY #1: Sixty Jiazi (六十甲子)

### Overview

The 60-stem cycle (六十甲子) is fundamental to Chinese calendar and Saju calculations. It's a combination of 10 Heavenly Stems (天干) and 12 Earthly Branches (地支) creating a 60-year/60-day cycle.

### File Location

```
saju_codex_batch_all_v2_6_signed/policies/sixty_jiazi.json
```

### Schema Reference

Create matching schema at:
```
saju_codex_batch_all_v2_6_signed/schemas/sixty_jiazi.schema.json
```

### Required Structure

```json
{
  "version": "1.0",
  "generated_on": "2025-10-05T00:00:00+09:00",
  "source_refs": [
    "三命通會 (Sanming Tonghui), 中華書局",
    "子平真詮 (Ziping Zhenquan), 中華書局註解本"
  ],
  "cycle": [
    {
      "index": 0,
      "stem": "甲",
      "branch": "子",
      "name_zh": "甲子",
      "name_ko": "갑자",
      "name_en": "Jia Zi",
      "element_stem": "木",
      "element_branch": "水",
      "nayin": "海中金",
      "nayin_ko": "해중금",
      "nayin_en": "Gold in the Sea"
    },
    {
      "index": 1,
      "stem": "乙",
      "branch": "丑",
      "name_zh": "乙丑",
      "name_ko": "을축",
      "name_en": "Yi Chou",
      "element_stem": "木",
      "element_branch": "土",
      "nayin": "海中金",
      "nayin_ko": "해중금",
      "nayin_en": "Gold in the Sea"
    }
    // ... 58 more entries (total 60)
  ],
  "metadata": {
    "total_count": 60,
    "stem_cycle": 10,
    "branch_cycle": 12,
    "lcm": 60
  }
}
```

### Schema Requirements

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Sixty Jiazi Cycle Policy",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "generated_on": {
      "type": "string",
      "format": "date-time"
    },
    "source_refs": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1
    },
    "cycle": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "index": { "type": "integer", "minimum": 0, "maximum": 59 },
          "stem": { "type": "string", "enum": ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"] },
          "branch": { "type": "string", "enum": ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"] },
          "name_zh": { "type": "string" },
          "name_ko": { "type": "string" },
          "name_en": { "type": "string" },
          "element_stem": { "type": "string", "enum": ["木","火","土","金","水"] },
          "element_branch": { "type": "string", "enum": ["木","火","土","金","水"] },
          "nayin": { "type": "string" },
          "nayin_ko": { "type": "string" },
          "nayin_en": { "type": "string" }
        },
        "required": ["index", "stem", "branch", "name_zh", "name_ko", "name_en", "element_stem", "element_branch", "nayin", "nayin_ko", "nayin_en"]
      },
      "minItems": 60,
      "maxItems": 60
    },
    "metadata": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "total_count": { "type": "integer", "const": 60 },
        "stem_cycle": { "type": "integer", "const": 10 },
        "branch_cycle": { "type": "integer", "const": 12 },
        "lcm": { "type": "integer", "const": 60 }
      },
      "required": ["total_count", "stem_cycle", "branch_cycle", "lcm"]
    }
  },
  "required": ["version", "generated_on", "source_refs", "cycle", "metadata"]
}
```

### Data Generation Rules

#### Stem Progression (天干)
```
甲 → 乙 → 丙 → 丁 → 戊 → 己 → 庚 → 辛 → 壬 → 癸 → (repeat)
```

#### Branch Progression (地支)
```
子 → 丑 → 寅 → 卯 → 辰 → 巳 → 午 → 未 → 申 → 酉 → 戌 → 亥 → (repeat)
```

#### Combination Logic
Start with 甲子 (index 0):
- Stem advances by 1 (mod 10)
- Branch advances by 1 (mod 12)
- Continue for 60 cycles until returning to 甲子

#### Nayin (納音) Lookup Table

60甲子纳音表 (Nayin Five Elements):

| Jiazi Pairs | Nayin (納音) | Korean | English |
|-------------|--------------|--------|---------|
| 甲子, 乙丑 | 海中金 | 해중금 | Gold in the Sea |
| 丙寅, 丁卯 | 爐中火 | 노중화 | Fire in the Furnace |
| 戊辰, 己巳 | 大林木 | 대림목 | Big Forest Wood |
| 庚午, 辛未 | 路旁土 | 노방토 | Roadside Earth |
| 壬申, 癸酉 | 劍鋒金 | 검봉금 | Sword Edge Metal |
| 甲戌, 乙亥 | 山頭火 | 산두화 | Fire on Mountain Top |
| 丙子, 丁丑 | 澗下水 | 간하수 | Stream Water |
| 戊寅, 己卯 | 城頭土 | 성두토 | City Wall Earth |
| 庚辰, 辛巳 | 白蠟金 | 백랍금 | White Wax Metal |
| 壬午, 癸未 | 楊柳木 | 양류목 | Willow Wood |
| 甲申, 乙酉 | 泉中水 | 천중수 | Spring Water |
| 丙戌, 丁亥 | 屋上土 | 옥상토 | Roof Earth |
| 戊子, 己丑 | 霹靂火 | 벽력화 | Thunderbolt Fire |
| 庚寅, 辛卯 | 松柏木 | 송백목 | Pine Cypress Wood |
| 壬辰, 癸巳 | 長流水 | 장류수 | Long Flowing Water |
| 甲午, 乙未 | 砂中金 | 사중금 | Gold in Sand |
| 丙申, 丁酉 | 山下火 | 산하화 | Fire Under Mountain |
| 戊戌, 己亥 | 平地木 | 평지목 | Flat Land Wood |
| 庚子, 辛丑 | 壁上土 | 벽상토 | Wall Earth |
| 壬寅, 癸卯 | 金箔金 | 금박금 | Gold Foil Metal |
| 甲辰, 乙巳 | 覆燈火 | 복등화 | Covered Lamp Fire |
| 丙午, 丁未 | 天河水 | 천하수 | Heavenly River Water |
| 戊申, 己酉 | 大驛土 | 대역토 | Great Post Earth |
| 庚戌, 辛亥 | 釵釧金 | 차천금 | Hairpin Metal |
| 壬子, 癸丑 | 桑柘木 | 상자목 | Mulberry Wood |
| 甲寅, 乙卯 | 大溪水 | 대계수 | Big Stream Water |
| 丙辰, 丁巳 | 沙中土 | 사중토 | Sand Earth |
| 戊午, 己未 | 天上火 | 천상화 | Heavenly Fire |
| 庚申, 辛酉 | 石榴木 | 석류목 | Pomegranate Wood |
| 壬戌, 癸亥 | 大海水 | 대해수 | Great Sea Water |

**Note**: Each Nayin covers 2 consecutive Jiazi pairs.

### Validation Requirements

After creating the file:

1. **Schema Validation**:
```python
from jsonschema import validate
validate(policy, schema)  # Must pass
```

2. **Runtime Guards** (create in `app/core/policy_guards_luck.py`):
```python
def validate_jiazi_cycle(jiazi_policy: dict) -> None:
    """Validate 60 Jiazi cycle progression."""
    cycle = jiazi_policy.get("cycle", [])

    if len(cycle) != 60:
        raise LuckPolicyError("Sixty Jiazi cycle must have length 60.")

    # Check uniqueness
    names = [f"{x['stem']}{x['branch']}" for x in cycle]
    if len(set(names)) != 60:
        raise LuckPolicyError("Sixty Jiazi names must be unique.")

    # Check progression
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"

    for i in range(60):
        cur = cycle[i]
        nxt = cycle[(i + 1) % 60]

        if stems.index(nxt["stem"]) != (stems.index(cur["stem"]) + 1) % 10:
            raise LuckPolicyError(f"Stem progression broken at index {i}.")

        if branches.index(nxt["branch"]) != (branches.index(cur["branch"]) + 1) % 12:
            raise LuckPolicyError(f"Branch progression broken at index {i}.")
```

3. **Unit Tests** (create in `tests/test_jiazi_policy.py`):
```python
def test_jiazi_cycle_length():
    assert len(policy["cycle"]) == 60

def test_jiazi_cycle_starts_with_jiazi():
    first = policy["cycle"][0]
    assert first["stem"] == "甲"
    assert first["branch"] == "子"

def test_jiazi_cycle_ends_with_guihai():
    last = policy["cycle"][59]
    assert last["stem"] == "癸"
    assert last["branch"] == "亥"

def test_jiazi_nayin_coverage():
    # Each nayin should cover exactly 2 jiazi
    from collections import Counter
    nayin_counts = Counter([item["nayin"] for item in policy["cycle"]])
    for count in nayin_counts.values():
        assert count == 2
```

### Classical References

**Primary**:
- 三命通會 (Sanming Tonghui) - Complete 60 Jiazi table with Nayin
- 子平真詮 (Ziping Zhenquan) - Jiazi cycle usage in chart analysis

**Verification**:
- Cross-check with online Jiazi calculators
- Verify Nayin assignments against classical texts

---

## 🔴 MISSING POLICY #2: Branch Ten Gods Policy

### Overview

The Branch Ten Gods policy defines the **logic for calculating Ten Gods relationships** between Heavenly Stems. This is used by the Luck Pillars calculator to determine the Ten God for each luck pillar stem.

### File Location

```
saju_codex_batch_all_v2_6_signed/policies/branch_tengods_policy.json
```

### Schema Reference

Create matching schema at:
```
saju_codex_batch_all_v2_6_signed/schemas/branch_tengods_policy.schema.json
```

### Required Structure

```json
{
  "version": "1.1",
  "generated_on": "2025-10-05T00:00:00+09:00",
  "source_refs": [
    "子平真詮 (Ziping Zhenquan), 中華書局註解本",
    "滴天髓 (Di Tian Sui), 上海古籍"
  ],
  "disclaimer": "본 정책은 십신(十神) 관계 계산 로직을 정의합니다. 학파마다 명칭과 해석이 다를 수 있으나, 관계 로직은 동일합니다.",
  "stem_to_element": {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
  },
  "element_generates": {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木"
  },
  "element_controls": {
    "木": "土",
    "火": "金",
    "土": "水",
    "金": "木",
    "水": "火"
  },
  "ten_gods_matrix": {
    "same_element": {
      "same_polarity": "比肩",
      "opposite_polarity": "劫財"
    },
    "i_generate": {
      "same_polarity": "食神",
      "opposite_polarity": "傷官"
    },
    "i_control": {
      "same_polarity": "偏財",
      "opposite_polarity": "正財"
    },
    "controls_me": {
      "same_polarity": "偏官",
      "opposite_polarity": "正官"
    },
    "generates_me": {
      "same_polarity": "偏印",
      "opposite_polarity": "正印"
    }
  },
  "labels": {
    "zh": {
      "比肩": "比肩",
      "劫財": "劫財",
      "食神": "食神",
      "傷官": "傷官",
      "偏財": "偏財",
      "正財": "正財",
      "偏官": "偏官",
      "正官": "正官",
      "偏印": "偏印",
      "正印": "正印"
    },
    "ko": {
      "比肩": "비견",
      "劫財": "겁재",
      "食神": "식신",
      "傷官": "상관",
      "偏財": "편재",
      "正財": "정재",
      "偏官": "편관",
      "正官": "정관",
      "偏印": "편인",
      "正印": "정인"
    },
    "en": {
      "比肩": "Shoulder",
      "劫財": "Rob Wealth",
      "食神": "Eating God",
      "傷官": "Hurting Officer",
      "偏財": "Indirect Wealth",
      "正財": "Direct Wealth",
      "偏官": "Indirect Officer",
      "正官": "Direct Officer",
      "偏印": "Indirect Resource",
      "正印": "Direct Resource"
    }
  }
}
```

### Schema Requirements

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Branch Ten Gods Logic Policy",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "generated_on": {
      "type": "string",
      "format": "date-time"
    },
    "source_refs": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1
    },
    "disclaimer": {
      "type": "string"
    },
    "stem_to_element": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "甲": { "type": "string", "const": "木" },
        "乙": { "type": "string", "const": "木" },
        "丙": { "type": "string", "const": "火" },
        "丁": { "type": "string", "const": "火" },
        "戊": { "type": "string", "const": "土" },
        "己": { "type": "string", "const": "土" },
        "庚": { "type": "string", "const": "金" },
        "辛": { "type": "string", "const": "金" },
        "壬": { "type": "string", "const": "水" },
        "癸": { "type": "string", "const": "水" }
      },
      "required": ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    },
    "element_generates": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "木": { "type": "string", "const": "火" },
        "火": { "type": "string", "const": "土" },
        "土": { "type": "string", "const": "金" },
        "金": { "type": "string", "const": "水" },
        "水": { "type": "string", "const": "木" }
      },
      "required": ["木","火","土","金","水"]
    },
    "element_controls": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "木": { "type": "string", "const": "土" },
        "火": { "type": "string", "const": "金" },
        "土": { "type": "string", "const": "水" },
        "金": { "type": "string", "const": "木" },
        "水": { "type": "string", "const": "火" }
      },
      "required": ["木","火","土","金","水"]
    },
    "ten_gods_matrix": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "same_element": {
          "type": "object",
          "properties": {
            "same_polarity": { "type": "string", "const": "比肩" },
            "opposite_polarity": { "type": "string", "const": "劫財" }
          },
          "required": ["same_polarity", "opposite_polarity"]
        },
        "i_generate": {
          "type": "object",
          "properties": {
            "same_polarity": { "type": "string", "const": "食神" },
            "opposite_polarity": { "type": "string", "const": "傷官" }
          },
          "required": ["same_polarity", "opposite_polarity"]
        },
        "i_control": {
          "type": "object",
          "properties": {
            "same_polarity": { "type": "string", "const": "偏財" },
            "opposite_polarity": { "type": "string", "const": "正財" }
          },
          "required": ["same_polarity", "opposite_polarity"]
        },
        "controls_me": {
          "type": "object",
          "properties": {
            "same_polarity": { "type": "string", "const": "偏官" },
            "opposite_polarity": { "type": "string", "const": "正官" }
          },
          "required": ["same_polarity", "opposite_polarity"]
        },
        "generates_me": {
          "type": "object",
          "properties": {
            "same_polarity": { "type": "string", "const": "偏印" },
            "opposite_polarity": { "type": "string", "const": "正印" }
          },
          "required": ["same_polarity", "opposite_polarity"]
        }
      },
      "required": ["same_element", "i_generate", "i_control", "controls_me", "generates_me"]
    },
    "labels": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "zh": { "type": "object" },
        "ko": { "type": "object" },
        "en": { "type": "object" }
      },
      "required": ["zh", "ko", "en"]
    }
  },
  "required": ["version", "generated_on", "source_refs", "disclaimer", "stem_to_element", "element_generates", "element_controls", "ten_gods_matrix", "labels"]
}
```

### Calculation Logic

#### Algorithm

```python
def calculate_ten_god(day_stem: str, target_stem: str, policy: dict) -> str:
    """
    Calculate Ten God relationship from day_stem to target_stem.

    Args:
        day_stem: Day master stem (日干)
        target_stem: Target stem to compare
        policy: branch_tengods_policy dict

    Returns:
        Ten God name in Chinese (e.g., "比肩", "食神")
    """
    stem_to_elem = policy["stem_to_element"]
    elem_gen = policy["element_generates"]
    elem_ctrl = policy["element_controls"]
    matrix = policy["ten_gods_matrix"]

    # Get elements
    day_elem = stem_to_elem[day_stem]
    target_elem = stem_to_elem[target_stem]

    # Check polarity (陰陽)
    yang_stems = ["甲", "丙", "戊", "庚", "壬"]
    day_yang = day_stem in yang_stems
    target_yang = target_stem in yang_stems
    same_polarity = (day_yang == target_yang)

    # Determine relationship
    if day_elem == target_elem:
        # Same element
        if same_polarity:
            return matrix["same_element"]["same_polarity"]  # 比肩
        else:
            return matrix["same_element"]["opposite_polarity"]  # 劫財

    elif elem_gen[day_elem] == target_elem:
        # I generate target
        if same_polarity:
            return matrix["i_generate"]["same_polarity"]  # 食神
        else:
            return matrix["i_generate"]["opposite_polarity"]  # 傷官

    elif elem_ctrl[day_elem] == target_elem:
        # I control target
        if same_polarity:
            return matrix["i_control"]["same_polarity"]  # 偏財
        else:
            return matrix["i_control"]["opposite_polarity"]  # 正財

    elif elem_ctrl[target_elem] == day_elem:
        # Target controls me
        if same_polarity:
            return matrix["controls_me"]["same_polarity"]  # 偏官
        else:
            return matrix["controls_me"]["opposite_polarity"]  # 正官

    elif elem_gen[target_elem] == day_elem:
        # Target generates me
        if same_polarity:
            return matrix["generates_me"]["same_polarity"]  # 偏印
        else:
            return matrix["generates_me"]["opposite_polarity"]  # 正印

    else:
        raise ValueError(f"Invalid relationship: {day_stem} -> {target_stem}")
```

### Test Cases

```python
def test_ten_gods_calculation():
    """Test Ten Gods calculation with known examples."""
    # Day stem: 甲 (Yang Wood)
    assert calculate_ten_god("甲", "甲", policy) == "比肩"  # Same stem
    assert calculate_ten_god("甲", "乙", policy) == "劫財"  # Same element, opposite polarity
    assert calculate_ten_god("甲", "丙", policy) == "食神"  # I generate (Wood→Fire), same polarity
    assert calculate_ten_god("甲", "丁", policy) == "傷官"  # I generate, opposite polarity
    assert calculate_ten_god("甲", "戊", policy) == "偏財"  # I control (Wood→Earth), same polarity
    assert calculate_ten_god("甲", "己", policy) == "正財"  # I control, opposite polarity
    assert calculate_ten_god("甲", "庚", policy) == "偏官"  # Controls me (Metal→Wood), same polarity
    assert calculate_ten_god("甲", "辛", policy) == "正官"  # Controls me, opposite polarity
    assert calculate_ten_god("甲", "壬", policy) == "偏印"  # Generates me (Water→Wood), same polarity
    assert calculate_ten_god("甲", "癸", policy) == "正印"  # Generates me, opposite polarity
```

### Classical References

**Primary**:
- 子平真詮 (Ziping Zhenquan) - Ten Gods relationship definitions
- 滴天髓 (Di Tian Sui) - Yin/Yang polarity rules

---

## 🟡 INTEGRATION #1: LuckCalculator Update

### Overview

Update the existing `LuckCalculator` in `services/analysis-service/app/core/luck.py` to use the new `luck_pillars_policy.json` v1.1.

### Current Status

The `LuckCalculator` currently has hardcoded logic for:
- Start age calculation (3 days = 1 year rule)
- Solar term selection (hardcoded to specific terms)
- Direction determination (male/female × yin/yang)

### Required Changes

#### 1. Load Policy File

```python
# At top of luck.py
LUCK_POLICY_PATH = Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "luck_pillars_policy.json"

class LuckCalculator:
    def __init__(self) -> None:
        with LUCK_POLICY_PATH.open("r", encoding="utf-8") as f:
            self._luck_policy = json.load(f)
        # ... existing code
```

#### 2. Update Direction Logic

Replace hardcoded direction with policy matrix:

```python
def luck_direction(self, ctx: LuckContext) -> Dict[str, str | None]:
    """Determine luck direction from policy."""
    year_stem = ctx.year_stem  # Add to LuckContext
    gender = ctx.gender

    # Determine year stem polarity
    yang_stems = ["甲", "丙", "戊", "庚", "壬"]
    polarity = "yang" if year_stem in yang_stems else "yin"

    # Lookup from policy
    matrix = self._luck_policy["direction"]["matrix"]
    direction = matrix[gender][polarity]

    # Get labels
    labels = self._luck_policy["direction"]["labels"]

    return {
        "direction": direction,
        "label_ko": labels["ko"][direction],
        "label_en": labels["en"][direction]
    }
```

#### 3. Update Start Age Calculation

Use `reference.type` (jie/qi) from policy:

```python
def compute_start_age(self, ctx: LuckContext) -> Dict[str, float | str]:
    """Calculate start age using policy-driven solar term reference."""
    birth_utc, _ = self._resolver.resolve(ctx.local_dt, ctx.timezone)

    # Get reference type from policy
    ref_config = self._luck_policy["start_age"]["reference"]
    anchor_type = ref_config["type"]  # "jie" or "qi"

    # Get direction
    direction = self.luck_direction(ctx)["direction"]

    # Determine which boundary to use
    if direction == "forward":
        boundary_key = ref_config["forward"]  # "next"
        # TODO: Call astro-service to get next term of type=anchor_type
        boundary_dt = self._get_solar_term_boundary(
            birth_dt=birth_utc,
            term_type=anchor_type,
            direction="next"
        )
        elapsed_hours = (boundary_dt - birth_utc).total_seconds() / 3600.0
    else:  # backward
        boundary_key = ref_config["backward"]  # "prev"
        boundary_dt = self._get_solar_term_boundary(
            birth_dt=birth_utc,
            term_type=anchor_type,
            direction="prev"
        )
        elapsed_hours = (birth_utc - boundary_dt).total_seconds() / 3600.0

    # Convert using policy values
    conversion = self._luck_policy["start_age"]["conversion"]
    years = elapsed_hours / (conversion["hours_per_day"] * conversion["days_per_year"])

    # Round using policy settings
    rounding = self._luck_policy["start_age"]["rounding"]
    if rounding["mode"] == "half_up":
        start_age = round(years, rounding["decimals"])
    elif rounding["mode"] == "floor":
        start_age = int(years * (10 ** rounding["decimals"])) / (10 ** rounding["decimals"])
    elif rounding["mode"] == "ceil":
        import math
        start_age = math.ceil(years * (10 ** rounding["decimals"])) / (10 ** rounding["decimals"])

    return {
        "start_age": start_age,
        "reference_type": anchor_type,
        "boundary_datetime": boundary_dt.isoformat(),
        "elapsed_hours": elapsed_hours
    }
```

#### 4. Implement Astro-Service Integration

Add method to get solar term boundaries:

```python
def _get_solar_term_boundary(
    self,
    birth_dt: datetime,
    term_type: str,  # "jie" or "qi"
    direction: str   # "next" or "prev"
) -> datetime:
    """
    Get solar term boundary from astro-service.

    Args:
        birth_dt: Birth datetime (UTC)
        term_type: "jie" (節) or "qi" (氣)
        direction: "next" or "prev"

    Returns:
        Solar term boundary datetime (UTC)

    TODO: Replace with actual astro-service HTTP call
    """
    # PLACEHOLDER - Replace with actual astro-service integration
    # For now, use existing SimpleSolarTermLoader
    year = birth_dt.year
    terms = list(self._term_loader.load_year(year)) + list(
        self._term_loader.load_year(year + 1)
    )

    # Filter by type (this is a simplification - astro-service should do this)
    if term_type == "jie":
        # 節 terms: 立春, 驚蟄, 清明, 立夏, 芒種, 小暑, 立秋, 白露, 寒露, 立冬, 大雪, 小寒
        jie_terms = ["立春", "驚蟄", "清明", "立夏", "芒種", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]
        terms = [t for t in terms if t.term in jie_terms]
    elif term_type == "qi":
        # 氣 terms: 雨水, 春分, 穀雨, 小滿, 夏至, 大暑, 處暑, 秋分, 霜降, 小雪, 冬至, 大寒
        qi_terms = ["雨水", "春分", "穀雨", "小滿", "夏至", "大暑", "處暑", "秋分", "霜降", "小雪", "冬至", "大寒"]
        terms = [t for t in terms if t.term in qi_terms]

    if direction == "next":
        boundary = next((entry for entry in terms if entry.utc_time > birth_dt), None)
    else:  # prev
        boundary = None
        for entry in terms:
            if entry.utc_time <= birth_dt:
                boundary = entry
            else:
                break

    if not boundary:
        raise ValueError(f"No {term_type} term found in {direction} direction from {birth_dt}")

    return boundary.utc_time
```

#### 5. Update Luck Pillar Generation

Use policy for Ten God and Lifecycle annotations:

```python
def generate_luck_pillars(
    self,
    month_pillar: str,  # e.g., "丙寅"
    day_stem: str,      # e.g., "甲"
    direction: str,     # "forward" or "backward"
    start_age: float    # e.g., 3.2
) -> List[Dict]:
    """
    Generate 10-year luck pillars.

    Uses sixty_jiazi.json for progression.
    Uses branch_tengods_policy.json for Ten God calculation.
    Uses lifecycle_stages.json for lifecycle stage.
    """
    # Load dependencies (should be in __init__)
    jiazi_policy = self._load_sixty_jiazi()
    tengods_policy = self._load_tengods_policy()
    lifecycle_policy = self._load_lifecycle_policy()

    # Get generation config
    gen_config = self._luck_policy["generation"]
    age_series = gen_config["age_series"]

    # Find month pillar in jiazi cycle
    month_stem, month_branch = month_pillar[0], month_pillar[1]
    month_index = self._find_jiazi_index(month_stem, month_branch, jiazi_policy)

    # Start from next pillar after month
    if gen_config["start_from_next_after_month"]:
        start_index = (month_index + 1) % 60
    else:
        start_index = month_index

    # Generate pillars
    pillars = []
    for i in range(age_series["count"]):
        if direction == "forward":
            idx = (start_index + i) % 60
        else:  # backward
            idx = (start_index - i) % 60

        jiazi = jiazi_policy["cycle"][idx]
        pillar_stem = jiazi["stem"]
        pillar_branch = jiazi["branch"]
        pillar_name = f"{pillar_stem}{pillar_branch}"

        # Calculate age
        age = start_age + (i * age_series["step_years"])
        if age_series["display_round"] == "floor":
            display_age = int(age)
        elif age_series["display_round"] == "ceil":
            import math
            display_age = math.ceil(age)
        else:  # half_up
            display_age = round(age)

        # Calculate Ten God (if enabled)
        ten_god = None
        if gen_config["emit"]["ten_god_for_stem"]:
            ten_god_zh = self._calculate_ten_god(
                day_stem, pillar_stem, tengods_policy
            )
            ten_god = {
                "zh": ten_god_zh,
                "ko": tengods_policy["labels"]["ko"][ten_god_zh],
                "en": tengods_policy["labels"]["en"][ten_god_zh]
            }

        # Calculate Lifecycle (if enabled)
        lifecycle = None
        if gen_config["emit"]["lifecycle_for_branch"]:
            lifecycle_zh = lifecycle_policy["mappings"][day_stem][pillar_branch]
            lifecycle = {
                "zh": lifecycle_zh,
                "ko": lifecycle_policy["labels"]["ko"][lifecycle_policy["labels"]["zh"].index(lifecycle_zh)],
                "en": lifecycle_policy["labels"]["en"][lifecycle_policy["labels"]["zh"].index(lifecycle_zh)]
            }

        pillars.append({
            "pillar": pillar_name,
            "stem": pillar_stem,
            "branch": pillar_branch,
            "start_age": display_age,
            "ten_god": ten_god,
            "lifecycle": lifecycle
        })

    return pillars
```

### Testing Requirements

Create tests in `tests/test_luck_calculator_integration.py`:

```python
def test_luck_calculator_loads_policy():
    calc = LuckCalculator()
    assert calc._luck_policy["version"] == "1.1"

def test_luck_direction_from_policy():
    ctx = LuckContext(
        local_dt=datetime(1990, 1, 1),
        timezone="Asia/Seoul",
        year_stem="甲",
        gender="male"
    )
    result = calc.luck_direction(ctx)
    assert result["direction"] == "forward"  # Male + Yang = forward
    assert result["label_ko"] == "순행"

def test_start_age_uses_jie_type():
    # Mock astro-service response
    result = calc.compute_start_age(ctx)
    assert result["reference_type"] == "jie"
    assert "start_age" in result
```

---

## 🟡 INTEGRATION #2: Elements Distribution

### File

`services/analysis-service/app/core/elements.py` (NEW - needs to be created)

### Policy

Already exists: `saju_codex_batch_all_v2_6_signed/policies/elements_distribution_criteria.json` v1.1

### Implementation Required

Create `elements.py` with:

```python
from pathlib import Path
import json
from typing import Dict, List

ELEMENTS_POLICY_PATH = Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "elements_distribution_criteria.json"
ZANGGAN_PATH = Path(__file__).resolve().parents[4] / "rulesets" / "zanggan_table.json"

class ElementsCalculator:
    """Calculate five elements distribution using policy v1.1."""

    def __init__(self):
        with ELEMENTS_POLICY_PATH.open("r", encoding="utf-8") as f:
            self._policy = json.load(f)
        with ZANGGAN_PATH.open("r", encoding="utf-8") as f:
            self._zanggan = json.load(f)["data"]

    def calculate(
        self,
        stems: List[str],      # [year, month, day, hour]
        branches: List[str]    # [year, month, day, hour]
    ) -> Dict:
        """
        Calculate five elements distribution.

        Returns:
            {
                "percentages": {"木": 25.0, "火": 20.0, ...},
                "labels": {"木": {"zh": "發達", "ko": "발달", "en": "Developed"}, ...},
                "mode": "branch_plus_hidden",
                "evidence": {...}
            }
        """
        mode = self._policy["counting_method"]["mode"]
        weights = self._policy["counting_method"]

        # Count elements
        scores = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}

        # Stems
        stem_to_elem = {
            "甲": "木", "乙": "木",
            "丙": "火", "丁": "火",
            "戊": "土", "己": "土",
            "庚": "金", "辛": "金",
            "壬": "水", "癸": "水"
        }
        for stem in stems:
            elem = stem_to_elem[stem]
            scores[elem] += weights["stems"]["weight"]

        # Branches (if mode includes branch)
        if mode == "branch_plus_hidden":
            branch_to_elem = {
                "子": "水", "丑": "土", "寅": "木", "卯": "木",
                "辰": "土", "巳": "火", "午": "火", "未": "土",
                "申": "金", "酉": "金", "戌": "土", "亥": "水"
            }
            for branch in branches:
                elem = branch_to_elem[branch]
                scores[elem] += weights["branches"]["weight"]

        # Hidden stems
        for branch in branches:
            hidden = self._zanggan[branch]
            if len(hidden) >= 1:
                scores[stem_to_elem[hidden[0]]] += weights["hidden_stems"]["primary"]["weight"]
            if len(hidden) >= 2:
                scores[stem_to_elem[hidden[1]]] += weights["hidden_stems"]["secondary"]["weight"]
            if len(hidden) >= 3:
                scores[stem_to_elem[hidden[2]]] += weights["hidden_stems"]["tertiary"]["weight"]

        # Normalize
        total = sum(scores.values())
        percentages = {k: (v / total) * 100 for k, v in scores.items()}

        # Label (BEFORE rounding)
        from app.core.policy_guards import normalize_and_label
        label_keys = normalize_and_label(percentages, self._policy["thresholds"])

        # Build labels dict
        labels = {}
        for elem, label_key in label_keys.items():
            labels[elem] = {
                "zh": self._policy["labels"]["zh"][label_key],
                "ko": self._policy["labels"]["ko"][label_key],
                "en": self._policy["labels"]["en"][label_key]
            }

        # Round
        decimals = self._policy["counting_method"]["rounding"]["decimals"]
        rounded_pcts = {k: round(v, decimals) for k, v in percentages.items()}

        # Adjust sum to 100.00
        total_rounded = sum(rounded_pcts.values())
        if abs(total_rounded - 100.0) > 0.01:
            last_elem = list(rounded_pcts.keys())[-1]
            rounded_pcts[last_elem] += (100.0 - total_rounded)

        return {
            "percentages": rounded_pcts,
            "labels": labels,
            "mode": mode,
            "evidence": {
                "raw_scores": scores,
                "raw_percentages": percentages,
                "weights": weights,
                "zanggan_signature": self._policy["dependencies"]["zanggan_policy"]["signature"]
            }
        }
```

### Integration into AnalysisEngine

Update `services/analysis-service/app/core/engine.py`:

```python
from .elements import ElementsCalculator

@dataclass(slots=True)
class AnalysisEngine:
    # ... existing fields
    elements_calculator: ElementsCalculator = field(default_factory=ElementsCalculator)

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        # ... existing code

        # Calculate elements
        elements_result = self.elements_calculator.calculate(
            stems=parsed.stems,
            branches=parsed.branches
        )

        # ... build response
```

---

## 🟡 INTEGRATION #3: Lifecycle Stages

### File

`services/analysis-service/app/core/lifecycle.py` (NEW - needs to be created)

### Policy

Already exists: `saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json` v1.1

### Implementation Required

Create `lifecycle.py` with:

```python
from pathlib import Path
import json
from typing import Dict

LIFECYCLE_POLICY_PATH = Path(__file__).resolve().parents[4] / "saju_codex_batch_all_v2_6_signed" / "policies" / "lifecycle_stages.json"

class LifecycleCalculator:
    """Calculate 12 lifecycle stages using policy v1.1."""

    def __init__(self):
        with LIFECYCLE_POLICY_PATH.open("r", encoding="utf-8") as f:
            self._policy = json.load(f)

    def calculate(
        self,
        day_stem: str,
        branches: List[str]  # [year, month, day, hour]
    ) -> Dict:
        """
        Calculate lifecycle stages for all four pillars.

        Args:
            day_stem: Day master stem (日干)
            branches: Branches for year/month/day/hour

        Returns:
            {
                "year": {"zh": "墓", "ko": "묘", "en": "Tomb"},
                "month": {"zh": "絕", "ko": "절", "en": "Extinction"},
                "day": {"zh": "長生", "ko": "장생", "en": "Birth"},
                "hour": {"zh": "沐浴", "ko": "목욕", "en": "Bath"}
            }
        """
        mappings = self._policy["mappings"]
        labels_zh = self._policy["labels"]["zh"]
        labels_ko = self._policy["labels"]["ko"]
        labels_en = self._policy["labels"]["en"]

        result = {}
        pillar_names = ["year", "month", "day", "hour"]

        for i, branch in enumerate(branches):
            stage_zh = mappings[day_stem][branch]
            stage_index = labels_zh.index(stage_zh)

            result[pillar_names[i]] = {
                "zh": stage_zh,
                "ko": labels_ko[stage_index],
                "en": labels_en[stage_index]
            }

        return result
```

### Integration into AnalysisEngine

Update `services/analysis-service/app/core/engine.py`:

```python
from .lifecycle import LifecycleCalculator

@dataclass(slots=True)
class AnalysisEngine:
    # ... existing fields
    lifecycle_calculator: LifecycleCalculator = field(default_factory=LifecycleCalculator)

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        # ... existing code

        # Calculate lifecycle stages
        lifecycle_result = self.lifecycle_calculator.calculate(
            day_stem=parsed.day_stem,
            branches=parsed.branches
        )

        # ... build response
```

---

## Summary Checklist

### Missing Policy Files
- [ ] `sixty_jiazi.json` + schema
- [ ] `branch_tengods_policy.json` + schema

### Engine Integrations
- [ ] LuckCalculator update (use luck_pillars_policy v1.1)
- [ ] ElementsCalculator creation (use elements_distribution_criteria v1.1)
- [ ] LifecycleCalculator creation (use lifecycle_stages v1.1)

### After Completion
- [ ] Run `python devtools/sign_policies.py` to inject all signatures
- [ ] Run all tests: `pytest services/analysis-service/tests/test_*policy*.py`
- [ ] Verify policy signature validation passes
- [ ] Integration test with full analysis flow

---

## Contact & Questions

For questions or clarifications:
1. Check classical references in `design/references.md`
2. Review existing policy files in `saju_codex_batch_all_v2_6_signed/policies/`
3. Run schema validation tests to ensure compliance

**All policies must**:
- ✅ Pass JSON schema validation
- ✅ Include version, generated_on, source_refs, disclaimer
- ✅ Use ISO-8601 timestamps
- ✅ Include zh/ko/en labels where applicable
- ✅ Be UTF-8 encoded with no JSON comments
- ✅ Have corresponding unit tests

---

**End of Handover Report**
