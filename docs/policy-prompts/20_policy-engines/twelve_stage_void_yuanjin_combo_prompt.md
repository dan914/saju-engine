# 📘 실행 프롬프트 — 12운성/공망/원진/합화오행 엔진 스펙 v1.0

**버전**: v1.0
**날짜**: 2025-10-07 KST
**경로 권장**: `docs/policy-prompts/20_policy-engines/twelve_stage_void_yuanjin_combo_prompt.md`

---

## ROLE
너는 KO-first 정책/엔진 아키텍트다. 설명 대신 **결정적 산출물**만 출력한다.

## GOAL
**4개 엔진**의 완전한 사양을 산출한다:
1. **TwelveStageCalculator** (12운성: 장생~양 12단계)
2. **VoidCalculator** (공망: 일간 기준 공망 지지)
3. **YuanjinDetector** (원진: 지지 원진 관계)
4. **CombinationElementTransformer** (합화오행: 합화 결과 원소)

각 엔진별 **I/O JSON Schema, 결정 규칙표, 의사코드, 엣지 케이스, 단위 테스트 명세**를 포함한다.

## CONTEXT (고정 사실)
- **12운성 (Twelve Life Stages)**: 일간 + 지지 → 장생/沐浴/冠帶/臨官/帝旺/衰/病/死/墓/絶/胎/養 (12단계)
- **공망 (Void/Empty)**: 일주 60갑자 → 해당 순환의 마지막 2지지가 공망 (예: 甲子순 → 戌亥공망)
- **원진 (Yuanjin/元辰)**: 지지 간 원진 관계 (子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌)
- **합화오행 (Combination Element)**: 천간 합 → 화합 원소 (甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火), 지지 삼합 → 국 형성 (申子辰水局 등)
- 기존 정책: `lifecycle_stages.json` (12운성 매핑 존재), `relation_policy.json` (원진/합화 확장 필요)
- KO-first 라벨: `*_ko` 병행 (예: `stage:"長生"`, `stage_ko:"장생"`)

## OUTPUT ORDER (반드시 이 순서)
1) 문서 헤더 (제목/버전/날짜)
2) **TwelveStageCalculator 사양** (I/O Schema, 결정 규칙표, 의사코드, 엣지 케이스, 테스트)
3) **VoidCalculator 사양** (I/O Schema, 공망표, 의사코드, 엣지 케이스, 테스트)
4) **YuanjinDetector 사양** (I/O Schema, 원진쌍, 의사코드, 엣지 케이스, 테스트)
5) **CombinationElementTransformer 사양** (I/O Schema, 합화 규칙표, 의사코드, 엣지 케이스, 테스트)
6) **relation_policy.json 확장 예시** (원진/합화 필드 추가)
7) **localization_ko_v1.json 확장** (라벨 20개+ 추가 목록)
8) **통합 체크리스트** (정책 파일/엔진 통합/테스트)

---

## 1. TwelveStageCalculator 사양

### 1.1 I/O JSON Schema

**Input:**
```json
{
  "day_stem": "乙",
  "branches": ["辰", "酉", "亥", "巳"]
}
```

**Output:**
```json
{
  "by_pillar": {
    "year": "墓",
    "month": "死",
    "day": "帝旺",
    "hour": "病"
  },
  "by_pillar_ko": {
    "year": "묘",
    "month": "사",
    "day": "제왕",
    "hour": "병"
  },
  "summary": {
    "strong_stages": ["帝旺"],
    "weak_stages": ["死", "病", "墓"],
    "balance": "weak_majority"
  }
}
```

### 1.2 결정 규칙표 (12운성)

**일간별 12운성 매핑 (lifecycle_stages.json 기반):**

| 일간 | 長生 | 沐浴 | 冠帶 | 臨官 | 帝旺 | 衰 | 病 | 死 | 墓 | 絶 | 胎 | 養 |
|------|------|------|------|------|------|-----|-----|-----|-----|-----|-----|-----|
| 甲 (양목) | 亥 | 子 | 丑 | 寅 | 卯 | 辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 |
| 乙 (음목) | 午 | 巳 | 辰 | 卯 | 寅 | 丑 | 子 | 亥 | 戌 | 酉 | 申 | 未 |
| 丙 (양화) | 寅 | 卯 | 辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 |
| 丁 (음화) | 酉 | 申 | 未 | 午 | 巳 | 辰 | 卯 | 寅 | 丑 | 子 | 亥 | 戌 |
| 戊 (양토) | 寅 | 卯 | 辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 |
| 己 (음토) | 酉 | 申 | 未 | 午 | 巳 | 辰 | 卯 | 寅 | 丑 | 子 | 亥 | 戌 |
| 庚 (양금) | 巳 | 午 | 未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 | 寅 | 卯 | 辰 |
| 辛 (음금) | 子 | 亥 | 戌 | 酉 | 申 | 未 | 午 | 巳 | 辰 | 卯 | 寅 | 丑 |
| 壬 (양수) | 申 | 酉 | 戌 | 亥 | 子 | 丑 | 寅 | 卯 | 辰 | 巳 | 午 | 未 |
| 癸 (음수) | 卯 | 寅 | 丑 | 子 | 亥 | 戌 | 酉 | 申 | 未 | 午 | 巳 | 辰 |

**강약 분류:**
- **강 (Strong)**: 長生, 冠帶, 臨官, 帝旺
- **중 (Neutral)**: 養, 沐浴
- **약 (Weak)**: 衰, 病, 死, 墓, 絶, 胎

### 1.3 의사코드

```python
def calculate_twelve_stage(day_stem: str, branch: str) -> dict:
    """
    일간 + 지지 → 12운성 단계
    """
    # lifecycle_stages.json 로드
    stages_map = load_policy("lifecycle_stages.json")

    # 일간별 12운성 순환 테이블 조회
    cycle = stages_map[day_stem]  # ['亥', '子', '丑', ...]

    # 지지 위치 찾기
    if branch not in cycle:
        return {"stage": None, "stage_ko": None}

    index = cycle.index(branch)
    stage_names = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絶", "胎", "養"]
    stage = stage_names[index]

    # 한국어 라벨
    stage_ko = STAGE_KO_MAP[stage]  # localization_ko_v1.json

    return {
        "stage": stage,
        "stage_ko": stage_ko,
        "strength": classify_strength(stage)  # strong/neutral/weak
    }

def calculate_all_pillars(day_stem: str, pillars: dict) -> dict:
    """
    4개 기둥에 대한 12운성 계산
    """
    result = {
        "by_pillar": {},
        "by_pillar_ko": {},
        "summary": {}
    }

    for pillar_name in ["year", "month", "day", "hour"]:
        branch = pillars[pillar_name]["branch"]
        stage_data = calculate_twelve_stage(day_stem, branch)
        result["by_pillar"][pillar_name] = stage_data["stage"]
        result["by_pillar_ko"][pillar_name] = stage_data["stage_ko"]

    # 요약
    all_stages = list(result["by_pillar"].values())
    strong = [s for s in all_stages if s in ["長生", "冠帶", "臨官", "帝旺"]]
    weak = [s for s in all_stages if s in ["衰", "病", "死", "墓", "絶", "胎"]]

    result["summary"] = {
        "strong_stages": strong,
        "weak_stages": weak,
        "balance": "strong_majority" if len(strong) > len(weak) else "weak_majority"
    }

    return result
```

### 1.4 엣지 케이스

1. **일간 음양 구분**: 乙(음목)과 甲(양목)은 순환 방향이 다름 → 테이블 정확성 검증 필수
2. **공망 지지**: 공망 지지도 12운성 계산 대상 (공망 여부는 VoidCalculator가 별도 처리)
3. **시간 미상 (unknown_hour)**: `pillars.hour = null` 시 해당 기둥 12운성도 null
4. **요약 balance**: 강약 동수일 때 "balanced" 처리

### 1.5 단위 테스트

```python
def test_twelve_stage_calculator():
    # Case 1: 乙木 + 亥 → 帝旺
    assert calculate_twelve_stage("乙", "亥") == {
        "stage": "帝旺",
        "stage_ko": "제왕",
        "strength": "strong"
    }

    # Case 2: 庚金 + 巳 → 長生
    assert calculate_twelve_stage("庚", "巳") == {
        "stage": "長生",
        "stage_ko": "장생",
        "strength": "strong"
    }

    # Case 3: 癸水 + 卯 → 長生
    assert calculate_twelve_stage("癸", "卯") == {
        "stage": "長生",
        "stage_ko": "장생",
        "strength": "strong"
    }

    # Case 4: 甲木 + 申 → 絶
    assert calculate_twelve_stage("甲", "申") == {
        "stage": "絶",
        "stage_ko": "절",
        "strength": "weak"
    }

    # Case 5: 4 pillars (乙亥, 庚辰, 乙酉, 辛巳)
    result = calculate_all_pillars("乙", {
        "year": {"branch": "辰"},
        "month": {"branch": "酉"},
        "day": {"branch": "亥"},
        "hour": {"branch": "巳"}
    })
    assert result["by_pillar"]["year"] == "墓"
    assert result["by_pillar"]["day"] == "帝旺"
    assert result["summary"]["balance"] == "weak_majority"
```

---

## 2. VoidCalculator 사양

### 2.1 I/O JSON Schema

**Input:**
```json
{
  "day_pillar": "乙亥"
}
```

**Output:**
```json
{
  "kong_wang": ["戌", "亥"],
  "kong_wang_ko": ["술", "해"],
  "affected_pillars": ["day"],
  "severity": "high"
}
```

### 2.2 공망표 (60갑자 순환)

**10개 순환 × 6회 = 60갑자:**

| 순환 | 갑자 범위 | 공망 지지 |
|------|-----------|----------|
| 1 | 甲子~癸酉 (10개) | 戌, 亥 |
| 2 | 甲戌~癸未 (10개) | 申, 酉 |
| 3 | 甲申~癸巳 (10개) | 午, 未 |
| 4 | 甲午~癸卯 (10개) | 辰, 巳 |
| 5 | 甲辰~癸丑 (10개) | 寅, 卯 |
| 6 | 甲寅~癸亥 (10개) | 子, 丑 |

**예시:**
- 甲子일주 → 1순환 → 戌亥공망
- 乙亥일주 → 1순환 → 戌亥공망
- 甲戌일주 → 2순환 → 申酉공망
- 甲午일주 → 4순환 → 辰巳공망

### 2.3 의사코드

```python
def calculate_void(day_pillar: str) -> dict:
    """
    일주 60갑자 → 공망 지지 2개
    """
    VOID_TABLE = {
        # 순환 1: 甲子~癸酉
        "甲子": ["戌", "亥"], "乙丑": ["戌", "亥"], "丙寅": ["戌", "亥"],
        "丁卯": ["戌", "亥"], "戊辰": ["戌", "亥"], "己巳": ["戌", "亥"],
        "庚午": ["戌", "亥"], "辛未": ["戌", "亥"], "壬申": ["戌", "亥"],
        "癸酉": ["戌", "亥"],

        # 순환 2: 甲戌~癸未
        "甲戌": ["申", "酉"], "乙亥": ["戌", "亥"], "丙子": ["戌", "亥"],
        # ... (전체 60갑자 매핑)
    }

    kong_wang = VOID_TABLE.get(day_pillar, [])
    kong_wang_ko = [BRANCH_KO_MAP[b] for b in kong_wang]

    return {
        "kong_wang": kong_wang,
        "kong_wang_ko": kong_wang_ko
    }

def check_void_in_pillars(day_pillar: str, pillars: dict) -> dict:
    """
    4개 기둥 중 공망 지지가 있는지 확인
    """
    void_data = calculate_void(day_pillar)
    kong_wang = set(void_data["kong_wang"])

    affected = []
    for pillar_name in ["year", "month", "day", "hour"]:
        branch = pillars[pillar_name]["branch"]
        if branch in kong_wang:
            affected.append(pillar_name)

    severity = "high" if "day" in affected or len(affected) >= 2 else "low"

    return {
        "kong_wang": void_data["kong_wang"],
        "kong_wang_ko": void_data["kong_wang_ko"],
        "affected_pillars": affected,
        "severity": severity
    }
```

### 2.4 엣지 케이스

1. **일주만 기준**: 공망은 일주 기준 (년/월/시주 무관)
2. **일주 자체가 공망**: 예: 乙亥일주 → 戌亥공망 → 일지 亥가 공망에 포함 (severity=high)
3. **60갑자 완전 매핑**: VOID_TABLE이 60개 전체 커버하는지 검증
4. **시간 미상**: `pillars.hour = null` 시 affected_pillars에서 hour 제외

### 2.5 단위 테스트

```python
def test_void_calculator():
    # Case 1: 甲子일주 → 戌亥공망
    assert calculate_void("甲子") == {
        "kong_wang": ["戌", "亥"],
        "kong_wang_ko": ["술", "해"]
    }

    # Case 2: 乙亥일주 → 戌亥공망 (일지 자체가 공망)
    result = check_void_in_pillars("乙亥", {
        "year": {"branch": "辰"},
        "month": {"branch": "酉"},
        "day": {"branch": "亥"},
        "hour": {"branch": "巳"}
    })
    assert result["affected_pillars"] == ["day"]
    assert result["severity"] == "high"

    # Case 3: 甲戌일주 → 申酉공망
    assert calculate_void("甲戌") == {
        "kong_wang": ["申", "酉"],
        "kong_wang_ko": ["신", "유"]
    }

    # Case 4: 공망 없음
    result = check_void_in_pillars("甲子", {
        "year": {"branch": "子"},
        "month": {"branch": "丑"},
        "day": {"branch": "寅"},
        "hour": {"branch": "卯"}
    })
    assert result["affected_pillars"] == []
    assert result["severity"] == "low"
```

---

## 3. YuanjinDetector 사양

### 3.1 I/O JSON Schema

**Input:**
```json
{
  "branches": ["辰", "酉", "亥", "巳"]
}
```

**Output:**
```json
{
  "yuanjin_pairs": [],
  "count": 0,
  "affected_pillars": []
}
```

### 3.2 원진쌍 (6쌍)

| 원진쌍 | 설명 |
|--------|------|
| 子 ↔ 未 | 자미원진 |
| 丑 ↔ 午 | 축오원진 |
| 寅 ↔ 巳 | 인사원진 |
| 卯 ↔ 辰 | 묘진원진 |
| 申 ↔ 亥 | 신해원진 |
| 酉 ↔ 戌 | 유술원진 |

**특징:**
- 원진은 **불화·마찰·장애** 의미 (충보다 약하지만 지속적)
- 지지 간 관계이므로 천간 무관

### 3.3 의사코드

```python
def detect_yuanjin(branches: list) -> dict:
    """
    지지 목록에서 원진 쌍 탐지
    """
    YUANJIN_PAIRS = {
        ("子", "未"), ("未", "子"),
        ("丑", "午"), ("午", "丑"),
        ("寅", "巳"), ("巳", "寅"),
        ("卯", "辰"), ("辰", "卯"),
        ("申", "亥"), ("亥", "申"),
        ("酉", "戌"), ("戌", "酉")
    }

    yuanjin_found = []
    pillar_names = ["year", "month", "day", "hour"]

    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            if (branches[i], branches[j]) in YUANJIN_PAIRS:
                yuanjin_found.append([branches[i], branches[j]])

    return {
        "yuanjin_pairs": yuanjin_found,
        "count": len(yuanjin_found),
        "affected_pillars": []  # TODO: 구체적 기둥 위치 추적
    }
```

### 3.4 엣지 케이스

1. **원진 중복**: 동일 지지 2개 이상 시 조합 수 증가 (예: 子子未 → 원진 2쌍)
2. **원진 + 충 동시**: 원진과 충이 같은 사주에 공존 가능 (예: 子未원진 + 巳亥충)
3. **시간 미상**: `pillars.hour = null` 시 3개 지지만 검사
4. **우선순위**: relation_policy.json에서 원진 우선순위는 충/형 다음

### 3.5 단위 테스트

```python
def test_yuanjin_detector():
    # Case 1: 子未 원진
    assert detect_yuanjin(["子", "未", "寅", "卯"]) == {
        "yuanjin_pairs": [["子", "未"]],
        "count": 1
    }

    # Case 2: 원진 없음
    assert detect_yuanjin(["辰", "酉", "亥", "巳"]) == {
        "yuanjin_pairs": [],
        "count": 0
    }

    # Case 3: 寅巳 원진
    assert detect_yuanjin(["寅", "巳", "申", "亥"]) == {
        "yuanjin_pairs": [["寅", "巳"], ["申", "亥"]],
        "count": 2
    }

    # Case 4: 卯辰 원진
    assert detect_yuanjin(["卯", "辰", "酉", "戌"]) == {
        "yuanjin_pairs": [["卯", "辰"], ["酉", "戌"]],
        "count": 2
    }
```

---

## 4. CombinationElementTransformer 사양

### 4.1 I/O JSON Schema

**Input:**
```json
{
  "stems": ["庚", "乙", "乙", "辛"],
  "branches": ["辰", "酉", "亥", "巳"]
}
```

**Output:**
```json
{
  "heavenly_combine": [
    {
      "pair": ["庚", "乙"],
      "result": "金",
      "pillars": ["year", "month"]
    }
  ],
  "earth_sanhe": [],
  "earth_he6": [
    {
      "pair": ["辰", "酉"],
      "result": "金",
      "pillars": ["year", "month"]
    }
  ],
  "boost_elements": ["金"]
}
```

### 4.2 합화 규칙표

**천간 합화 (5쌍):**

| 천간 쌍 | 화합 원소 | 조건 |
|---------|-----------|------|
| 甲 + 己 | 土 | 무조건 화합 |
| 乙 + 庚 | 金 | 무조건 화합 |
| 丙 + 辛 | 水 | 무조건 화합 |
| 丁 + 壬 | 木 | 무조건 화합 |
| 戊 + 癸 | 火 | 무조건 화합 |

**지지 삼합 (4국):**

| 삼합 | 화합 원소 | 조건 |
|------|-----------|------|
| 申子辰 | 水 | 3지지 모두 존재 |
| 亥卯未 | 木 | 3지지 모두 존재 |
| 寅午戌 | 火 | 3지지 모두 존재 |
| 巳酉丑 | 金 | 3지지 모두 존재 |

**지지 육합 (6쌍):**

| 육합 쌍 | 화합 원소 |
|---------|-----------|
| 子 + 丑 | 土 |
| 寅 + 亥 | 木 |
| 卯 + 戌 | 火 |
| 辰 + 酉 | 金 |
| 巳 + 申 | 水 |
| 午 + 未 | 火/土 (혼합) |

### 4.3 의사코드

```python
def transform_combination_elements(stems: list, branches: list) -> dict:
    """
    천간 합화 + 지지 삼합/육합 → 화합 원소
    """
    HEAVENLY_COMBINE = {
        frozenset(["甲", "己"]): "土",
        frozenset(["乙", "庚"]): "金",
        frozenset(["丙", "辛"]): "水",
        frozenset(["丁", "壬"]): "木",
        frozenset(["戊", "癸"]): "火"
    }

    EARTH_HE6 = {
        frozenset(["子", "丑"]): "土",
        frozenset(["寅", "亥"]): "木",
        frozenset(["卯", "戌"]): "火",
        frozenset(["辰", "酉"]): "金",
        frozenset(["巳", "申"]): "水",
        frozenset(["午", "未"]): "火"
    }

    EARTH_SANHE = {
        frozenset(["申", "子", "辰"]): "水",
        frozenset(["亥", "卯", "未"]): "木",
        frozenset(["寅", "午", "戌"]): "火",
        frozenset(["巳", "酉", "丑"]): "金"
    }

    result = {
        "heavenly_combine": [],
        "earth_sanhe": [],
        "earth_he6": [],
        "boost_elements": []
    }

    # 천간 합화
    for i in range(len(stems)):
        for j in range(i+1, len(stems)):
            pair_set = frozenset([stems[i], stems[j]])
            if pair_set in HEAVENLY_COMBINE:
                element = HEAVENLY_COMBINE[pair_set]
                result["heavenly_combine"].append({
                    "pair": [stems[i], stems[j]],
                    "result": element,
                    "pillars": [get_pillar_name(i), get_pillar_name(j)]
                })
                result["boost_elements"].append(element)

    # 지지 육합
    for i in range(len(branches)):
        for j in range(i+1, len(branches)):
            pair_set = frozenset([branches[i], branches[j]])
            if pair_set in EARTH_HE6:
                element = EARTH_HE6[pair_set]
                result["earth_he6"].append({
                    "pair": [branches[i], branches[j]],
                    "result": element,
                    "pillars": [get_pillar_name(i), get_pillar_name(j)]
                })
                result["boost_elements"].append(element)

    # 지지 삼합
    branch_set = frozenset(branches)
    for sanhe_set, element in EARTH_SANHE.items():
        if sanhe_set.issubset(branch_set):
            result["earth_sanhe"].append({
                "triple": list(sanhe_set),
                "result": element
            })
            result["boost_elements"].append(element)

    # 중복 제거
    result["boost_elements"] = list(set(result["boost_elements"]))

    return result
```

### 4.4 엣지 케이스

1. **午未 합**: 午未 합은 火/土 혼합 → 강한 쪽 선택 (컨텍스트 의존)
2. **삼합 불완전**: 申子 있지만 辰 없음 → 삼합 미성립, 육합만 검사
3. **합화 + 충 동시**: 辰酉합금 + 巳亥충 공존 시 우선순위는 충 (relation_policy.json)
4. **boost_elements**: 합화로 강화되는 오행 목록 (wuxing.adjusted.percent에 반영)

### 4.5 단위 테스트

```python
def test_combination_element_transformer():
    # Case 1: 乙庚合金 (천간)
    result = transform_combination_elements(
        stems=["庚", "乙", "乙", "辛"],
        branches=["辰", "酉", "亥", "巳"]
    )
    assert len(result["heavenly_combine"]) == 1
    assert result["heavenly_combine"][0]["result"] == "金"

    # Case 2: 辰酉合금 (육합)
    assert len(result["earth_he6"]) == 1
    assert result["earth_he6"][0]["result"] == "金"

    # Case 3: 申子辰 삼합수국
    result2 = transform_combination_elements(
        stems=["甲", "乙", "丙", "丁"],
        branches=["申", "子", "辰", "午"]
    )
    assert len(result2["earth_sanhe"]) == 1
    assert result2["earth_sanhe"][0]["result"] == "水"

    # Case 4: boost_elements 중복 제거
    assert "金" in result["boost_elements"]
    assert len(result["boost_elements"]) == 1  # 중복 제거
```

---

## 5. relation_policy.json 확장 예시

**기존 구조 + 원진/합화 추가:**

```json
{
  "version": "2.1",
  "heavenly": {
    "combine": [
      {
        "pair": ["甲", "己"],
        "result": "土",
        "priority": 1,
        "transform": true
      },
      {
        "pair": ["乙", "庚"],
        "result": "金",
        "priority": 1,
        "transform": true
      }
    ],
    "clash": [
      {
        "pair": ["甲", "庚"],
        "severity": "medium"
      }
    ]
  },
  "earth": {
    "he6": [
      {
        "pair": ["子", "丑"],
        "result": "土",
        "transform": true
      },
      {
        "pair": ["辰", "酉"],
        "result": "金",
        "transform": true
      }
    ],
    "sanhe": [
      {
        "triple": ["申", "子", "辰"],
        "result": "水",
        "transform": true
      },
      {
        "triple": ["亥", "卯", "未"],
        "result": "木",
        "transform": true
      }
    ],
    "chong": [
      {
        "pair": ["子", "午"],
        "severity": "high"
      }
    ],
    "xing": [
      {
        "triple": ["寅", "巳", "申"],
        "severity": "medium"
      }
    ],
    "po": [
      {
        "pair": ["子", "酉"],
        "severity": "low"
      }
    ],
    "hai": [
      {
        "pair": ["子", "未"],
        "severity": "low"
      }
    ],
    "yuanjin": [
      {
        "pair": ["子", "未"],
        "severity": "low",
        "description": "원진 (元辰) - 불화·장애"
      },
      {
        "pair": ["丑", "午"],
        "severity": "low"
      },
      {
        "pair": ["寅", "巳"],
        "severity": "low"
      },
      {
        "pair": ["卯", "辰"],
        "severity": "low"
      },
      {
        "pair": ["申", "亥"],
        "severity": "low"
      },
      {
        "pair": ["酉", "戌"],
        "severity": "low"
      }
    ]
  },
  "priority": ["sanhe", "he6", "chong", "xing", "po", "hai", "yuanjin"],
  "signature": {
    "sha256": "..."
  }
}
```

---

## 6. localization_ko_v1.json 확장

**추가 라벨 20개+:**

```json
{
  "version": "1.1",
  "locale": "ko",
  "mappings": {
    "twelve_stages": {
      "長生": "장생",
      "沐浴": "목욕",
      "冠帶": "관대",
      "臨官": "임관",
      "帝旺": "제왕",
      "衰": "쇠",
      "病": "병",
      "死": "사",
      "墓": "묘",
      "絶": "절",
      "胎": "태",
      "養": "양"
    },
    "void": {
      "kong_wang": "공망",
      "empty": "공허",
      "void_severity_high": "높음",
      "void_severity_low": "낮음"
    },
    "yuanjin": {
      "원진": "원진",
      "子未": "자미원진",
      "丑午": "축오원진",
      "寅巳": "인사원진",
      "卯辰": "묘진원진",
      "申亥": "신해원진",
      "酉戌": "유술원진"
    },
    "combination_elements": {
      "甲己合土": "갑기합토",
      "乙庚合金": "을경합금",
      "丙辛合水": "병신합수",
      "丁壬合木": "정임합목",
      "戊癸合火": "무계합화",
      "申子辰水局": "신자진수국",
      "亥卯未木局": "해묘미목국",
      "寅午戌火局": "인오술화국",
      "巳酉丑金局": "사유축금국"
    }
  },
  "signature": {
    "sha256": "..."
  }
}
```

---

## 7. 통합 체크리스트

### Phase 1: 정책 파일 확장
- [ ] relation_policy.json에 `yuanjin` 필드 추가 (6쌍)
- [ ] relation_policy.json에 `heavenly.combine.transform`, `earth.he6.transform` 필드 추가
- [ ] localization_ko_v1.json에 12운성/공망/원진/합화 라벨 20+ 추가
- [ ] lifecycle_stages.json 검증 (10간 × 12단계 매핑 완전성)

### Phase 2: 엔진 구현
- [ ] TwelveStageCalculator 구현 (lifecycle_stages.json 로드)
- [ ] VoidCalculator 구현 (60갑자 → 공망 테이블)
- [ ] YuanjinDetector 구현 (6쌍 검사)
- [ ] CombinationElementTransformer 구현 (천간 5쌍 + 지지 삼합/육합)

### Phase 3: AnalysisEngine 통합
- [ ] engine.py에 4개 엔진 임포트
- [ ] `analysis.life_stage` 필드 생성 (TwelveStageCalculator 호출)
- [ ] `analysis.void` 필드 생성 (VoidCalculator 호출)
- [ ] `analysis.relations.earth.yuanjin` 필드 생성 (YuanjinDetector 호출)
- [ ] `analysis.wuxing.adjusted.percent` 보정 (CombinationElementTransformer.boost_elements 반영)

### Phase 4: 테스트
- [ ] test_twelve_stage_calculator.py (4 케이스)
- [ ] test_void_calculator.py (4 케이스)
- [ ] test_yuanjin_detector.py (4 케이스)
- [ ] test_combination_element_transformer.py (4 케이스)
- [ ] 통합 테스트: AnalysisEngine → 4개 엔진 결과 검증

### Phase 5: KoreanLabelEnricher 통합
- [ ] 12운성 라벨 보강 (`life_stage.by_pillar.*_ko`)
- [ ] 공망 라벨 보강 (`void.kong_wang_ko`)
- [ ] 원진 라벨 보강 (필요 시)
- [ ] 합화 라벨 보강 (필요 시)

---

**Version:** v1.0 (2025-10-07 KST)
**Maintainer:** Core Architects (Policy/Engine/Data)
