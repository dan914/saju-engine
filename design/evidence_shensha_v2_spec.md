# Evidence Spec — Shensha v2 (KO-first)

---

## Header

```json
{
  "module": "shensha_v2",
  "policy_version": "2.0",
  "policy_signature": "<SHA256 by CI>",
  "locale_used": "ko-KR",
  "dependencies": {
    "sixty_jiazi": "34b9825fcca720918db2af1307ffd7d5be083cb97dea49f4ddc762081cff8945",
    "branch_tengods_policy": "40bbfbf8450db45fe8a2da9c9be74c3a8ccce834ee7a547576f7bbd131e3aa73",
    "elements_distribution": "<SIG_ELEMENTS>",
    "lifecycle_stages": "<SIG_LIFECYCLE>"
  }
}
```

---

## Inputs

```json
{
  "pillars": {
    "year": {"stem":"庚","branch":"申"},
    "month":{"stem":"壬","branch":"酉"},
    "day":  {"stem":"甲","branch":"寅"},
    "hour": {"stem":"丙","branch":"巳"}
  },
  "day_stem": "甲",
  "year_branch": "申"
}
```

---

## Traces

### day_stem_based

```json
[
  {
    "pillar": "year",
    "rule_key": "TIAN_E_GUIREN",
    "day_stem": "甲",
    "expected_branches": ["丑","未"],
    "branch": "申",
    "matched": false
  },
  {
    "pillar": "month",
    "rule_key": "TIAN_E_GUIREN",
    "day_stem": "甲",
    "expected_branches": ["丑","未"],
    "branch": "酉",
    "matched": false
  },
  {
    "pillar": "day",
    "rule_key": "TIAN_E_GUIREN",
    "day_stem": "甲",
    "expected_branches": ["丑","未"],
    "branch": "寅",
    "matched": false
  },
  {
    "pillar": "hour",
    "rule_key": "TIAN_E_GUIREN",
    "day_stem": "甲",
    "expected_branches": ["丑","未"],
    "branch": "巳",
    "matched": false
  }
]
```

### year_branch_based

```json
[
  {
    "pillar": "month",
    "rule_key": "TAO_HUA",
    "year_branch": "申",
    "expected": ["酉"],
    "branch": "酉",
    "matched": true
  },
  {
    "pillar": "day",
    "rule_key": "YI_MA",
    "year_branch": "申",
    "expected": ["寅"],
    "branch": "寅",
    "matched": true
  },
  {
    "pillar": "month",
    "rule_key": "HUA_GAI",
    "year_branch": "申",
    "expected": ["辰"],
    "branch": "酉",
    "matched": false
  }
]
```

### literacy_based

```json
[
  {
    "pillar": "month",
    "rule_key": "WEN_CHANG",
    "year_branch": "申",
    "expected": ["丑"],
    "branch": "酉",
    "matched": false
  },
  {
    "pillar": "hour",
    "rule_key": "WEN_QU",
    "year_branch": "申",
    "expected": ["未"],
    "branch": "巳",
    "matched": false
  }
]
```

### pair_conflict_based

```json
[
  {
    "pillars": ["day","hour"],
    "rule_key": "LIU_HAI",
    "pair": ["寅","巳"],
    "matched": true,
    "note": "육해 페어 (寅-巳) 일치"
  },
  {
    "pillars": ["day","month"],
    "rule_key": "YUAN_ZHEN",
    "pair": ["寅","酉"],
    "matched": false
  }
]
```

---

## TIAN_LA / DI_WANG Evidence (Nitpick #3 개선)

### 예시 1: 年=戊 辰, 月=庚 未, 日=乙 酉, 時=丁 丑

**Traces**:

```json
[
  {
    "pillar": "year",
    "rule_key": "TIAN_LA",
    "branch": "辰",
    "expected_branches": ["辰","戌"],
    "matched": true,
    "note": "천라(天羅): 연지 辰 일치"
  },
  {
    "pillar": "month",
    "rule_key": "DI_WANG",
    "branch": "未",
    "expected_branches": ["丑","未"],
    "matched": true,
    "note": "지망(地網): 월지 未 일치"
  },
  {
    "pillar": "day",
    "rule_key": "TIAN_LA",
    "branch": "酉",
    "expected_branches": ["辰","戌"],
    "matched": false
  },
  {
    "pillar": "hour",
    "rule_key": "DI_WANG",
    "branch": "丑",
    "expected_branches": ["丑","未"],
    "matched": true,
    "note": "지망(地網): 시지 丑 일치"
  }
]
```

**Output**:

```json
{
  "per_pillar": {
    "year":  [{"key":"TIAN_LA","label_ko":"천라","type":"凶","score_hint":-2}],
    "month": [{"key":"DI_WANG","label_ko":"지망","type":"凶","score_hint":-2}],
    "day":   [],
    "hour":  [{"key":"DI_WANG","label_ko":"지망","type":"凶","score_hint":-2}]
  },
  "summary": {
    "counts_by_type": {"吉":0,"中":0,"烈":0,"凶":3},
    "total_score": -6,
    "score_formula": "sum(score_hint for all matched shensha)"
  }
}
```

> ⚠️ **개선**: 기존 `assign_if_any: true` 방식에서 **각 기둥별 branch 매칭** 방식으로 변경.
> 辰/戌는 TIAN_LA, 丑/未는 DI_WANG에만 매칭되며, Evidence trace에 pillar별 명확한 기록.

---

### 예시 2: 年=壬 戌, 月=丙 子, 日=甲 辰, 時=己 未

**Traces**:

```json
[
  {
    "pillar": "year",
    "rule_key": "TIAN_LA",
    "branch": "戌",
    "expected_branches": ["辰","戌"],
    "matched": true,
    "note": "천라(天羅): 연지 戌 일치"
  },
  {
    "pillar": "day",
    "rule_key": "TIAN_LA",
    "branch": "辰",
    "expected_branches": ["辰","戌"],
    "matched": true,
    "note": "천라(天羅): 일지 辰 일치"
  },
  {
    "pillar": "hour",
    "rule_key": "DI_WANG",
    "branch": "未",
    "expected_branches": ["丑","未"],
    "matched": true,
    "note": "지망(地網): 시지 未 일치"
  }
]
```

**Output**:

```json
{
  "per_pillar": {
    "year":  [{"key":"TIAN_LA","label_ko":"천라","type":"凶","score_hint":-2}],
    "month": [],
    "day":   [{"key":"TIAN_LA","label_ko":"천라","type":"凶","score_hint":-2}],
    "hour":  [{"key":"DI_WANG","label_ko":"지망","type":"凶","score_hint":-2}]
  },
  "summary": {
    "counts_by_type": {"吉":0,"中":0,"烈":0,"凶":3},
    "total_score": -6
  }
}
```

---

## Output Format

```json
{
  "per_pillar": {
    "year":  [
      {"key":"TAO_HUA","label_ko":"도화","type":"中","score_hint":0}
    ],
    "month": [
      {"key":"TAO_HUA","label_ko":"도화","type":"中","score_hint":0}
    ],
    "day":   [
      {"key":"YI_MA","label_ko":"역마","type":"中","score_hint":0},
      {"key":"GUAI_GANG","label_ko":"괴강","type":"烈","score_hint":-1}
    ],
    "hour":  [
      {"key":"LIU_HAI","label_ko":"육해","type":"凶","score_hint":-1}
    ]
  },
  "summary": {
    "counts_by_type": {"吉":0,"中":2,"烈":1,"凶":1},
    "total_score": -2,
    "score_formula": "sum(score_hint for all matched shensha)",
    "tie_breaker": ["type_priority","label_order_ko","label_order_zh","label_order_en"]
  },
  "traces": {
    "day_stem_based": [...],
    "year_branch_based": [...],
    "pair_conflict_based": [...],
    "literacy_based": [...]
  }
}
```

---

## Logging Rules

1. **모든 규칙**은 `matched: true/false`와 근거 필드를 남긴다.
2. **KO-first 라벨**을 기본으로 포함, zh/en은 UI에서 병기 가능.
3. **CI**는 signature 주입 후 evidence 필드 키 일관성 검증.
4. **TIAN_LA/DI_WANG**은 기둥별 branch 매칭으로 부여 범위 명확화 (Nitpick #3).

---

## Score Calculation (Nitpick #2 개선)

**공식**: `total_score = sum(shensha.score_hint for shensha in all_matched)`

**예시**:
- TAO_HUA (0) + YI_MA (0) + GUAI_GANG (-1) + LIU_HAI (-1) = **-2점**

---

**생성일**: 2025-10-05
**버전**: 2.0
**엔진**: 신살 매핑기 v2
