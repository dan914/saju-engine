# 📘 실행 프롬프트 — 연운/월운 계산기 스펙 v1.0

**버전**: v1.0
**날짜**: 2025-10-07 KST
**경로 권장**: `docs/policy-prompts/20_policy-engines/annual_monthly_luck_prompt.md`

---

## ROLE
너는 KO-first 정책/엔진 아키텍트다. 설명 대신 **결정적 산출물**만 출력한다.

## GOAL
**2개 엔진**의 완전한 사양을 산출한다:
1. **AnnualLuckCalculator** (연운: 년주 + 대운 조합, 십신/12운성/태세)
2. **MonthlyLuckCalculator** (월운: 월주 + 길흉일 계산, 7일 티저)

각 엔진별 **I/O JSON Schema, 결정 규칙, 의사코드, 캐시 전략, 엣지 케이스, 단위 테스트 명세**를 포함한다.

## CONTEXT (고정 사실)
- **연운 (Annual Luck)**: 현재 대운 + 해당 년주 → 십신/12운성/태세(太歲)/길흉 종합
- **월운 (Monthly Luck)**: 해당 월주 + 일별 길흉 → good_days/caution_days (1~31일)
- **대운 (Decades Luck)**: 이미 LuckCalculator에서 계산됨 (`luck.decades.pillars[]`, `start_age`, `direction`)
- **캐시**: 연운 365일 TTL, 월운 30일 TTL (RFC-8785 서명 기반)
- **API 엔드포인트**: `POST /api/v1/luck/annual`, `POST /api/v1/luck/monthly`
- KO-first 라벨: `*_ko` 병행

## OUTPUT ORDER (반드시 이 순서)
1) 문서 헤더 (제목/버전/날짜)
2) **AnnualLuckCalculator 사양** (I/O Schema, 결정 규칙, 의사코드, 캐시, 엣지 케이스, 테스트)
3) **MonthlyLuckCalculator 사양** (I/O Schema, 결정 규칙, 의사코드, 캐시, 엣지 케이스, 테스트)
4) **API 엔드포인트 스키마** (요청/응답 JSON Schema draft-2020-12)
5) **캐시 전략** (키 구조, TTL, 무효화 규칙)
6) **통합 체크리스트** (엔진 구현/API 통합/테스트)

---

## 1. AnnualLuckCalculator 사양

### 1.1 I/O JSON Schema

**Input:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "year": 2025,
  "birth_data": {
    "day_stem": "乙",
    "gender": "male",
    "birth_dt": "2000-09-14T10:00:00+09:00"
  },
  "current_decade": {
    "pillar": "甲申",
    "start_age": 7.98,
    "direction": "reverse"
  }
}
```

**Output:**
```json
{
  "year": 2025,
  "year_pillar": {
    "stem": "乙",
    "branch": "巳",
    "sexagenary": "乙巳",
    "stem_ko": "을",
    "branch_ko": "사",
    "sexagenary_ko": "을사"
  },
  "ten_god": "比肩",
  "ten_god_ko": "비견",
  "life_stage": "病",
  "life_stage_ko": "병",
  "tai_sui": {
    "branch": "巳",
    "element": "火",
    "conflict_with_birth": ["巳亥沖"]
  },
  "annual_score": 68.5,
  "tags": ["比肩年", "巳亥沖", "자시전환주의"],
  "summary": {
    "strength": "neutral",
    "fortune": "caution",
    "key_months": ["2025-03", "2025-09"]
  }
}
```

### 1.2 결정 규칙

**연운 계산 흐름:**
1. **년주 조회**: 해당 년도의 천간/지지 결정 (예: 2025년 = 乙巳)
2. **십신 계산**: 일간 vs 년간 → 십신 (예: 乙일간 vs 乙년간 = 比肩)
3. **12운성 계산**: 일간 + 년지 → 12운성 (TwelveStageCalculator 사용)
4. **태세 (太歲)**: 년지의 원소 + 본명과의 충/형/해 관계
5. **연운 점수**: 십신 강약 + 12운성 + 대운 조합 → 0~100 점수
6. **태그 생성**: ["比肩年", "巳亥沖", "자시전환주의"] 등
7. **주요 월 추천**: 연운 기반 유리한/주의할 월 (예: 3월, 9월)

**연운 점수 공식:**
```python
score = (
    ten_god_weight * 30 +      # 십신 가중치
    life_stage_weight * 25 +   # 12운성 가중치
    decade_harmony * 20 +      # 대운 조화도
    tai_sui_impact * 15 +      # 태세 영향
    relation_boost * 10        # 합충형파해 보정
)
```

**십신 가중치 (예시):**
- 比肩/劫財: 중립 (50)
- 食神/傷官: 긍정 (70)
- 正財/偏財: 긍정 (75)
- 正官/偏官: 중립 (55)
- 正印/偏印: 긍정 (65)

### 1.3 의사코드

```python
def calculate_annual_luck(
    profile_id: str,
    year: int,
    birth_data: dict,
    current_decade: dict
) -> dict:
    """
    연운 계산: 년주 + 대운 조합 → 십신/12운성/태세/점수
    """
    # 1. 년주 조회 (60갑자 순환)
    year_pillar = get_year_pillar(year)  # 예: 2025 → 乙巳

    # 2. 십신 계산
    ten_god = calculate_ten_god(birth_data["day_stem"], year_pillar["stem"])
    ten_god_ko = TEN_GOD_KO_MAP[ten_god]

    # 3. 12운성 계산
    life_stage = TwelveStageCalculator.calculate(
        day_stem=birth_data["day_stem"],
        branch=year_pillar["branch"]
    )

    # 4. 태세 (년지의 원소 + 본명과의 관계)
    tai_sui = {
        "branch": year_pillar["branch"],
        "element": BRANCH_TO_ELEMENT[year_pillar["branch"]],
        "conflict_with_birth": check_tai_sui_conflict(
            year_branch=year_pillar["branch"],
            birth_pillars=birth_data["pillars"]
        )
    }

    # 5. 연운 점수
    score = calculate_annual_score(
        ten_god=ten_god,
        life_stage=life_stage["stage"],
        decade_pillar=current_decade["pillar"],
        tai_sui=tai_sui
    )

    # 6. 태그 생성
    tags = generate_tags(ten_god, tai_sui["conflict_with_birth"])

    # 7. 주요 월 추천
    key_months = recommend_key_months(year, score, tai_sui)

    return {
        "year": year,
        "year_pillar": year_pillar,
        "ten_god": ten_god,
        "ten_god_ko": ten_god_ko,
        "life_stage": life_stage["stage"],
        "life_stage_ko": life_stage["stage_ko"],
        "tai_sui": tai_sui,
        "annual_score": score,
        "tags": tags,
        "summary": {
            "strength": classify_strength(score),
            "fortune": classify_fortune(score),
            "key_months": key_months
        }
    }

def get_year_pillar(year: int) -> dict:
    """
    년도 → 년주 60갑자 (1900년 기준 甲子 시작)
    """
    base_year = 1900
    base_index = 36  # 1900 = 庚子 (36번째)
    offset = (year - base_year) % 60
    index = (base_index + offset) % 60

    SIXTY_JIAZI = [
        "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
        "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
        # ... 60개
    ]
    sexagenary = SIXTY_JIAZI[index]
    stem = sexagenary[0]
    branch = sexagenary[1]

    return {
        "stem": stem,
        "branch": branch,
        "sexagenary": sexagenary,
        "stem_ko": STEM_KO_MAP[stem],
        "branch_ko": BRANCH_KO_MAP[branch],
        "sexagenary_ko": SIXTY_JIAZI_KO_MAP[sexagenary]
    }

def check_tai_sui_conflict(year_branch: str, birth_pillars: dict) -> list:
    """
    태세와 본명 기둥의 충/형/해 검사
    """
    conflicts = []
    birth_branches = [p["branch"] for p in birth_pillars.values()]

    for birth_branch in birth_branches:
        if (year_branch, birth_branch) in CHONG_PAIRS:
            conflicts.append(f"{year_branch}{birth_branch}沖")
        elif (year_branch, birth_branch) in XING_PAIRS:
            conflicts.append(f"{year_branch}{birth_branch}刑")
        elif (year_branch, birth_branch) in HAI_PAIRS:
            conflicts.append(f"{year_branch}{birth_branch}害")

    return conflicts
```

### 1.4 엣지 케이스

1. **윤년 처리**: 2월 29일 출생자의 연운 계산 (2월 28일로 처리)
2. **자시 전환**: 년 경계 (12/31 23:00~1/1 01:00) 태어난 경우 년주 결정 주의
3. **대운 전환기**: 연 중간에 대운이 바뀌는 경우 (예: 7.98세 → 2025년 중 8세 도달)
4. **태세 충**: 년지와 일지 충 (犯太歲) → 주의 태그 강조

### 1.5 단위 테스트

```python
def test_annual_luck_calculator():
    # Case 1: 2025년 연운 (乙巳년, 乙일간)
    result = calculate_annual_luck(
        profile_id="550e8400-e29b-41d4-a716-446655440000",
        year=2025,
        birth_data={
            "day_stem": "乙",
            "gender": "male",
            "birth_dt": "2000-09-14T10:00:00+09:00",
            "pillars": {
                "year": {"branch": "辰"},
                "month": {"branch": "酉"},
                "day": {"branch": "亥"},
                "hour": {"branch": "巳"}
            }
        },
        current_decade={"pillar": "甲申", "start_age": 7.98, "direction": "reverse"}
    )

    assert result["year"] == 2025
    assert result["year_pillar"]["sexagenary"] == "乙巳"
    assert result["ten_god"] == "比肩"
    assert result["life_stage"] == "病"
    assert "巳亥沖" in result["tai_sui"]["conflict_with_birth"]
    assert 60 <= result["annual_score"] <= 75

    # Case 2: 2026년 연운 (丙午년)
    result2 = calculate_annual_luck(
        profile_id="550e8400-e29b-41d4-a716-446655440000",
        year=2026,
        birth_data={"day_stem": "乙", "pillars": {...}},
        current_decade={"pillar": "甲申"}
    )
    assert result2["year_pillar"]["sexagenary"] == "丙午"
    assert result2["ten_god"] == "傷官"
```

---

## 2. MonthlyLuckCalculator 사양

### 2.1 I/O JSON Schema

**Input:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "month": "2025-10",
  "birth_data": {
    "day_stem": "乙",
    "pillars": {...}
  },
  "annual_luck": {
    "year_pillar": "乙巳",
    "annual_score": 68.5
  }
}
```

**Output:**
```json
{
  "month": "2025-10",
  "month_pillar": {
    "stem": "丙",
    "branch": "戌",
    "sexagenary": "丙戌",
    "stem_ko": "병",
    "branch_ko": "술",
    "sexagenary_ko": "병술"
  },
  "ten_god": "傷官",
  "ten_god_ko": "상관",
  "life_stage": "墓",
  "life_stage_ko": "묘",
  "monthly_score": 72.3,
  "good_days": [3, 8, 13, 18, 23, 28],
  "caution_days": [5, 14, 19, 27],
  "daily_snippet": {
    "range": "D+1~D+7",
    "highlights": [
      {"date": "2025-10-03", "tag": "문서정리", "score": 85},
      {"date": "2025-10-08", "tag": "계약유리", "score": 82}
    ]
  },
  "summary": {
    "theme": "정리·지출관리",
    "recommendation": "문서 정리 유리, 계약은 22일 이후",
    "caution": "5일, 14일 갈등 주의"
  }
}
```

### 2.2 결정 규칙

**월운 계산 흐름:**
1. **월주 조회**: 해당 월의 천간/지지 결정 (예: 2025-10 = 丙戌)
2. **십신 계산**: 일간 vs 월간 → 십신
3. **12운성 계산**: 일간 + 월지 → 12운성
4. **월운 점수**: 십신 + 12운성 + 연운 조합 → 0~100
5. **길일/흉일 계산**: 일별 천간/지지 조합 → good_days/caution_days (1~31)
6. **7일 티저**: D+1~D+7 상세 일정 (채팅 응답용)

**길일/흉일 판단 기준:**
- **길일**: 일간과 합/생조 관계, 12운성 강함 (長生/帝旺/臨官)
- **흉일**: 일간과 충/극 관계, 12운성 약함 (死/墓/絶)

**월주 계산 (절기 기반):**
- 입춘(立春) ~ 경칩(驚蟄): 寅월 (인월, 1절기)
- 경칩 ~ 청명(清明): 卯월 (묘월, 2절기)
- ... 12개월 순환

### 2.3 의사코드

```python
def calculate_monthly_luck(
    profile_id: str,
    month: str,  # "YYYY-MM"
    birth_data: dict,
    annual_luck: dict
) -> dict:
    """
    월운 계산: 월주 + 길흉일 → 십신/12운성/good_days/caution_days
    """
    # 1. 월주 조회 (절기 기반)
    month_pillar = get_month_pillar(month)  # 예: 2025-10 → 丙戌

    # 2. 십신 계산
    ten_god = calculate_ten_god(birth_data["day_stem"], month_pillar["stem"])

    # 3. 12운성 계산
    life_stage = TwelveStageCalculator.calculate(
        day_stem=birth_data["day_stem"],
        branch=month_pillar["branch"]
    )

    # 4. 월운 점수
    score = calculate_monthly_score(
        ten_god=ten_god,
        life_stage=life_stage["stage"],
        annual_score=annual_luck["annual_score"]
    )

    # 5. 길일/흉일 계산 (1~31일)
    good_days, caution_days = calculate_daily_luck(
        month=month,
        day_stem=birth_data["day_stem"],
        month_pillar=month_pillar
    )

    # 6. 7일 티저 생성
    daily_snippet = generate_daily_snippet(
        month=month,
        good_days=good_days[:7],
        ten_god=ten_god
    )

    # 7. 요약
    summary = {
        "theme": infer_theme(ten_god, life_stage["stage"]),
        "recommendation": generate_recommendation(good_days),
        "caution": generate_caution(caution_days)
    }

    return {
        "month": month,
        "month_pillar": month_pillar,
        "ten_god": ten_god,
        "ten_god_ko": TEN_GOD_KO_MAP[ten_god],
        "life_stage": life_stage["stage"],
        "life_stage_ko": life_stage["stage_ko"],
        "monthly_score": score,
        "good_days": good_days,
        "caution_days": caution_days,
        "daily_snippet": daily_snippet,
        "summary": summary
    }

def get_month_pillar(month: str) -> dict:
    """
    월 → 월주 60갑자 (절기 기준)
    """
    year, month_num = month.split("-")
    year = int(year)
    month_num = int(month_num)

    # 절기 기반 월지 결정
    MONTH_BRANCHES = [
        "寅", "卯", "辰", "巳", "午", "未",
        "申", "酉", "戌", "亥", "子", "丑"
    ]
    branch = MONTH_BRANCHES[month_num - 1]

    # 월간 결정 (년간 기준 순환)
    year_stem = get_year_pillar(year)["stem"]
    month_stem = calculate_month_stem(year_stem, month_num)

    sexagenary = month_stem + branch

    return {
        "stem": month_stem,
        "branch": branch,
        "sexagenary": sexagenary,
        "stem_ko": STEM_KO_MAP[month_stem],
        "branch_ko": BRANCH_KO_MAP[branch],
        "sexagenary_ko": SIXTY_JIAZI_KO_MAP.get(sexagenary, sexagenary)
    }

def calculate_month_stem(year_stem: str, month_num: int) -> str:
    """
    년간 + 월 → 월간 (오호기법)
    """
    MONTH_STEM_TABLE = {
        "甲": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
        "乙": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
        "丙": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
        "丁": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
        "戊": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"],
        "己": ["丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁"],
        "庚": ["戊", "己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己"],
        "辛": ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"],
        "壬": ["壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
        "癸": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"]
    }
    return MONTH_STEM_TABLE[year_stem][month_num - 1]

def calculate_daily_luck(month: str, day_stem: str, month_pillar: dict) -> tuple:
    """
    일별 길흉 계산 (1~31일)
    """
    year, month_num = map(int, month.split("-"))
    days_in_month = get_days_in_month(year, month_num)

    good_days = []
    caution_days = []

    for day in range(1, days_in_month + 1):
        day_pillar = get_day_pillar(year, month_num, day)
        score = calculate_day_score(day_stem, day_pillar, month_pillar)

        if score >= 75:
            good_days.append(day)
        elif score <= 40:
            caution_days.append(day)

    return good_days, caution_days
```

### 2.4 엣지 케이스

1. **절기 경계**: 월 초/말 절기 전환 시 월주 변경 (예: 10/8 한로 이후 戌월)
2. **2월 일수**: 윤년/평년 구분 (28일/29일)
3. **길일 없음**: 월운 점수가 낮아 good_days가 0개인 경우 → "신중한 월" 태그
4. **7일 티저**: 월 말일 경우 D+1~D+7이 다음 월로 넘어감 → 다음 월 데이터 필요

### 2.5 단위 테스트

```python
def test_monthly_luck_calculator():
    # Case 1: 2025-10 월운 (丙戌월, 乙일간)
    result = calculate_monthly_luck(
        profile_id="550e8400-e29b-41d4-a716-446655440000",
        month="2025-10",
        birth_data={"day_stem": "乙", "pillars": {...}},
        annual_luck={"year_pillar": "乙巳", "annual_score": 68.5}
    )

    assert result["month"] == "2025-10"
    assert result["month_pillar"]["sexagenary"] == "丙戌"
    assert result["ten_god"] == "傷官"
    assert result["life_stage"] == "墓"
    assert len(result["good_days"]) >= 3
    assert len(result["caution_days"]) >= 2
    assert result["daily_snippet"]["range"] == "D+1~D+7"

    # Case 2: 2월 윤년 처리
    result2 = calculate_monthly_luck(
        profile_id="550e8400-e29b-41d4-a716-446655440000",
        month="2024-02",  # 윤년
        birth_data={"day_stem": "乙"},
        annual_luck={"annual_score": 70}
    )
    assert 29 in result2["good_days"] or 29 in result2["caution_days"]  # 2월 29일 포함

    # Case 3: 길일 없음 (저조한 월)
    result3 = calculate_monthly_luck(
        profile_id="test",
        month="2025-11",
        birth_data={"day_stem": "甲"},
        annual_luck={"annual_score": 35}
    )
    if len(result3["good_days"]) == 0:
        assert "신중" in result3["summary"]["theme"]
```

---

## 3. API 엔드포인트 스키마

### 3.1 POST /api/v1/luck/annual

**Request Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/luck_annual_request_v1.schema.json",
  "type": "object",
  "required": ["profile_id", "year"],
  "properties": {
    "profile_id": {
      "type": "string",
      "format": "uuid",
      "description": "저장된 프로필 ID"
    },
    "year": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2100,
      "description": "조회 년도 (YYYY)"
    }
  }
}
```

**Response Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/luck_annual_response_v1.schema.json",
  "type": "object",
  "required": ["year", "year_pillar", "ten_god", "life_stage", "annual_score", "summary"],
  "properties": {
    "year": {"type": "integer"},
    "year_pillar": {"$ref": "#/$defs/Pillar"},
    "ten_god": {"type": "string", "enum": ["比肩", "劫財", "食神", "傷官", "正財", "偏財", "正官", "偏官", "正印", "偏印"]},
    "ten_god_ko": {"type": "string"},
    "life_stage": {"type": "string", "enum": ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絶", "胎", "養"]},
    "life_stage_ko": {"type": "string"},
    "tai_sui": {
      "type": "object",
      "properties": {
        "branch": {"type": "string"},
        "element": {"type": "string"},
        "conflict_with_birth": {"type": "array", "items": {"type": "string"}}
      }
    },
    "annual_score": {"type": "number", "minimum": 0, "maximum": 100},
    "tags": {"type": "array", "items": {"type": "string"}},
    "summary": {
      "type": "object",
      "properties": {
        "strength": {"type": "string", "enum": ["strong", "neutral", "weak"]},
        "fortune": {"type": "string", "enum": ["excellent", "good", "neutral", "caution", "difficult"]},
        "key_months": {"type": "array", "items": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"}}
      }
    },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
      }
    }
  }
}
```

### 3.2 POST /api/v1/luck/monthly

**Request Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/luck_monthly_request_v1.schema.json",
  "type": "object",
  "required": ["profile_id", "month"],
  "properties": {
    "profile_id": {
      "type": "string",
      "format": "uuid"
    },
    "month": {
      "type": "string",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])$",
      "description": "조회 월 (YYYY-MM)"
    }
  }
}
```

**Response Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/luck_monthly_response_v1.schema.json",
  "type": "object",
  "required": ["month", "month_pillar", "ten_god", "life_stage", "monthly_score", "good_days", "caution_days", "summary"],
  "properties": {
    "month": {"type": "string", "pattern": "^\\d{4}-(0[1-9]|1[0-2])$"},
    "month_pillar": {"$ref": "#/$defs/Pillar"},
    "ten_god": {"type": "string"},
    "ten_god_ko": {"type": "string"},
    "life_stage": {"type": "string"},
    "life_stage_ko": {"type": "string"},
    "monthly_score": {"type": "number", "minimum": 0, "maximum": 100},
    "good_days": {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 31}},
    "caution_days": {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 31}},
    "daily_snippet": {
      "type": "object",
      "properties": {
        "range": {"type": "string"},
        "highlights": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "date": {"type": "string", "format": "date"},
              "tag": {"type": "string"},
              "score": {"type": "number"}
            }
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "theme": {"type": "string"},
        "recommendation": {"type": "string"},
        "caution": {"type": "string"}
      }
    },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
      }
    }
  }
}
```

---

## 4. 캐시 전략

### 4.1 캐시 키 구조

**연운 캐시:**
```
cache_key = f"luck:annual:{profile_id}:{year}"
ttl = 365 days
```

**월운 캐시:**
```
cache_key = f"luck:monthly:{profile_id}:{month}"
ttl = 30 days
```

**RFC-8785 서명:**
```python
canonical = canonicalize(response_data)  # RFC-8785
sha256 = hashlib.sha256(canonical).hexdigest()
response["signatures"] = {"sha256": sha256}
```

### 4.2 무효화 규칙

**연운 무효화:**
- 프로필 수정 시 (pillars/birth_dt 변경)
- 대운 재계산 시 (LuckCalculator 호출)

**월운 무효화:**
- 프로필 수정 시
- 연운 재계산 시 (연운 점수가 월운에 영향)

**프리페치:**
- 현재 년도 ±1년 연운 미리 계산 (배경 작업)
- 현재 월 ±1개월 월운 미리 계산

### 4.3 캐시 검증

```python
def get_annual_luck_cached(profile_id: str, year: int) -> dict:
    cache_key = f"luck:annual:{profile_id}:{year}"
    cached = redis.get(cache_key)

    if cached:
        data = json.loads(cached)
        # RFC-8785 서명 검증
        canonical = canonicalize({k: v for k, v in data.items() if k != "signatures"})
        computed_hash = hashlib.sha256(canonical).hexdigest()
        if computed_hash == data["signatures"]["sha256"]:
            return data

    # 캐시 미스 → 계산
    result = calculate_annual_luck(profile_id, year, ...)
    redis.setex(cache_key, 365 * 86400, json.dumps(result))
    return result
```

---

## 5. 통합 체크리스트

### Phase 1: 엔진 구현
- [ ] AnnualLuckCalculator 구현 (년주 조회/십신/12운성/태세/점수)
- [ ] MonthlyLuckCalculator 구현 (월주 조회/일별 길흉/7일 티저)
- [ ] get_year_pillar() 구현 (60갑자 순환)
- [ ] get_month_pillar() 구현 (절기 기반 월주)
- [ ] calculate_day_score() 구현 (일별 점수)

### Phase 2: API 통합
- [ ] POST /api/v1/luck/annual 엔드포인트 구현
- [ ] POST /api/v1/luck/monthly 엔드포인트 구현
- [ ] 캐시 레이어 통합 (Redis)
- [ ] RFC-8785 서명 생성/검증

### Phase 3: 테스트
- [ ] test_annual_luck_calculator.py (4 케이스)
- [ ] test_monthly_luck_calculator.py (5 케이스)
- [ ] 통합 테스트: API → 엔진 → 캐시 플로우
- [ ] 성능 테스트: P95 <500ms (캐시 히트), <2s (캐시 미스)

### Phase 4: 채팅 통합
- [ ] /chat/send에서 luck_snippet 카드 생성 (MonthlyLuckCalculator.daily_snippet 사용)
- [ ] intent=month/year 시 연/월운 데이터 로드
- [ ] next_cta에 "이번 달 달력 보기", "연운 타임라인" 추가

### Phase 5: 문서화
- [ ] luck_pillars_policy.json 확장 (연/월운 점수 공식)
- [ ] localization_ko_v1.json 태그 추가 (예: "比肩年", "巳亥沖")
- [ ] API 문서 업데이트 (OpenAPI 스펙)

---

**Version:** v1.0 (2025-10-07 KST)
**Maintainer:** Core Architects (Policy/Engine/Data)
