# 신살 매핑기 v2 — Methodology (KO-first)

**엔진명(ko)**: 신살 매핑기 v2
**버전**: 2.0 · 생성일: 2025-10-05T00:00:00+09:00

---

## 1. 목적과 범위

12지·천간 조합 및 연지 기준 규칙으로 산출되는 **신살(神煞)**을 **각 기둥(year/month/day/hour)**에 부여합니다.

- 한국 사용자에게 익숙한 명칭/툴팁을 KO-first로 제공하며, zh/en 병기.
- 본 엔진은 보조 정보 제공을 목적으로 하며, 길흉의 단정적 해석은 금합니다.

---

## 2. 데이터 모델

### 2.1 카탈로그

`shensha_catalog[]` : 20개 이상의 신살 정의

```json
{
  "key": "TIAN_E_GUIREN",
  "labels": {"ko": "천을귀인", "zh": "天乙貴人", "en": "Heavenly Nobleman"},
  "type": "吉",
  "score_hint": 2
}
```

**타입 분류**:
- `吉` (길성): 완만한 길성
- `中` (중립): 상황 의존적
- `烈` (열성): 강성 변동성
- `凶` (흉성): 주의 필요

### 2.2 규칙 그룹

1. **day_stem_based**: 일간 기준(천을귀인, 괴강 등)
2. **year_branch_based**: 연지 기준(도화, 역마, 화개)
3. **pair_conflict_based**: 지지 간 조합(육해, 원진, 천라, 지망, 백호, 혈인)
4. **literacy_based**: 학업·문예 신살(문창, 문곡, 학당)

### 2.3 집계 방식

- **per_pillar_mode**: `"set"` (기둥별 중복 허용)
- **score_hint_mode**: `"sum_by_type"` (타입별 합산)
- **score_hint_formula**: `total_score = sum(shensha.score_hint for shensha in all_matched)`
- **score_hint_note_ko**: "매칭된 모든 신살의 score_hint를 합산하여 총점 계산. 吉은 양수, 凶은 음수로 설계됨."
- **tie_breaker**: `["type_priority", "label_order_ko", "label_order_zh", "label_order_en"]`
- **type_priority**: `{"吉":1, "中":2, "烈":3, "凶":4}`

---

## 3. 핵심 규칙 표

### 3.1 도화·역마·화개 (연지 기준)

#### 도화(桃花)
- 申子辰 → 酉
- 寅午戌 → 卯
- 巳酉丑 → 午
- 亥卯未 → 子

#### 역마(驛馬)
- 申子辰 → 寅
- 寅午戌 → 申
- 巳酉丑 → 亥
- 亥卯未 → 巳

#### 화개(華蓋)
- 申子辰 → 辰
- 寅午戌 → 戌
- 巳酉丑 → 丑
- 亥卯未 → 未

### 3.2 천을귀인 (일간 기준; 방위支)

| 일간 | 귀인 방위 |
|------|----------|
| 甲, 戊 | 丑, 未 |
| 乙, 丁 | 子, 申 |
| 丙, 己 | 亥, 酉 |
| 庚 | 丑, 巳 |
| 辛, 癸 | 寅, 午 |
| 壬 | 卯, 巳 |

### 3.3 문창·문곡·학당 (연지 기준)

#### 문창(文昌)
- 子→巳, 丑→午, 寅→未, 卯→申, 辰→酉, 巳→戌
- 午→亥, 未→子, 申→丑, 酉→寅, 戌→卯, 亥→辰

#### 문곡(文曲)
- 子→亥, 丑→子, 寅→丑, 卯→寅, 辰→卯, 巳→辰
- 午→巳, 未→午, 申→未, 酉→申, 戌→酉, 亥→戌

#### 학당(學堂)
- 寅→申, 卯→酉, 辰→戌, 巳→亥, 午→子, 未→丑
- 申→寅, 酉→卯, 戌→辰, 亥→巳, 子→午, 丑→未

### 3.4 간편 특례

#### 괴강(魁罡)
- 특정 강성 간(庚, 辛, 戊, 壬, 癸) + 辰 일지 결합

#### 백호(白虎)
- 일지 ∈ {寅, 午, 戌} (火국 삼합축)

#### 혈인(血刃)
- 일지 ∈ {巳, 酉, 丑} (金국 삼합축)

#### 육해(六害) 페어
- {子-未, 丑-午, 寅-巳, 卯-辰, 申-亥, 酉-戌}

#### 원진(怨嗔) 페어
- {子-丑, 寅-亥, 卯-辰, 巳-申, 午-未, 酉-戌}

#### 천라/지망
- **천라(天羅)**: 辰, 戌 지지를 가진 기둥에 부여
- **지망(地網)**: 丑, 未 지지를 가진 기둥에 부여

> ⚠️ **Nitpick #3 개선**: 기존 `assign_if_any: true` 방식에서 **기둥별 매칭 방식**으로 변경.
> 辰/戌/丑/未 지지를 가진 기둥에만 개별적으로 부여하여 Evidence trace 명확화.

---

## 4. 알고리즘 개요

### 입력
- 4기둥 간지 (year/month/day/hour)
- 일간(day_stem)
- 연지(year_branch)

### 규칙 적용

1. **day_stem_based**:
   - `by_day_stem_map[day_stem]`에 해당하는 지지와 pillar의 branch가 일치하면 부여

2. **year_branch_based**:
   - `by_year_branch_map[year_branch]` 포함 여부 확인

3. **pair_conflict_based**:
   - 지지 쌍/집합 포함 여부 확인
   - 천라/지망은 각 기둥의 branch가 해당 지지인지 확인

4. **literacy_based**:
   - `by_year_branch_map[year_branch]` 기준으로 문창/문곡/학당 매칭

### 집계

- 기둥별로 부여된 신살 set을 수집
- `type_priority`를 우선으로 정렬
- 정렬 순서: `type_priority` → `label_order_ko` → `label_order_zh` → `label_order_en`

### 점수 계산

**공식**: `total_score = sum(shensha.score_hint for shensha in all_matched)`

**예시**:
- 天乙貴人 (+2) + 文昌 (+1) + 桃花 (0) + 六害 (-1) = **+2점**

> ⚠️ **Nitpick #2 개선**: score_hint_formula 명시로 집계 로직 명확화.

---

## 5. Worked Examples

### 예시 A — 申年·甲日 / 年:申 月:酉 日:甲 寅 時:巳

**적용 규칙**:
1. 도화: 申年 도화=酉 → 월지 酉 일치 → `TAO_HUA(month)`
2. 역마: 申年 역마=寅 → 일지 寅 일치 → `YI_MA(day)`
3. 육해: (寅, 巳) 쌍 포함 → `LIU_HAI(day-hour)`

**출력 (정렬)**:
- 타입 우선: 吉 < 中 < 烈 < 凶
- 결과: `TAO_HUA(month, 中)`, `YI_MA(day, 中)`, `LIU_HAI(pair, 凶)`

**총점**: 0 + 0 + (-1) = **-1점**

---

### 예시 B — 亥年·庚日 / 年:亥 月:未 日:庚 辰 時:子

**적용 규칙**:
1. 화개: 亥年 화개=未 → `HUA_GAI(month)`
2. 괴강: 日支 辰 + 庚日 → `GUAI_GANG(day)`
3. 지망: 월지 未 → `DI_WANG(month)`
4. 천라: 일지 辰 → `TIAN_LA(day)`

**출력 (정렬)**:
- `HUA_GAI(month, 中)`, `GUAI_GANG(day, 烈)`, `DI_WANG(month, 凶)`, `TIAN_LA(day, 凶)`

**총점**: 0 + (-1) + (-2) + (-2) = **-5점**

---

### 예시 C — 子年·甲日 / 年:子 月:巳 日:甲 卯 時:未

**적용 규칙**:
1. 천을귀인: 甲日 귀인=丑/未 → 시지 未 일치 → `TIAN_E_GUIREN(hour)`
2. 문창: 子年 문창=巳 → 월지 巳 일치 → `WEN_CHANG(month)`

**출력 (정렬)**:
- `TIAN_E_GUIREN(hour, 吉)`, `WEN_CHANG(month, 吉)`

**총점**: +2 + 1 = **+3점**

---

## 6. KO-first UI

### 기본 로캘
- `ko-KR`

### 라벨
- 한국어 우선, zh/en 병기 가능
- 타입 설명: `ui_labels.ko.type_explain[type]` 사용

### Disclaimer
"신살은 보조 정보입니다. 단정적 해석을 지양하세요."

---

## 7. 검증 포인트

### CI Assertions (9개)

| ID | Expression | Purpose |
|----|------------|---------|
| CATALOG_MIN_18 | `len(shensha_catalog) >= 18` | 최소 18개 신살 포함 |
| LABELS_KO_REQUIRED | `for_each: labels.ko != ''` | 한국어 라벨 필수 |
| TYPE_ENUM | `type in ['吉','中','烈','凶']` | 타입 열거형 검증 |
| DEPENDENCIES_SIGNED | All dependency signatures non-empty | 의존성 서명 필수 |
| TIE_BREAKER_KO_FIRST | `tie_breaker[1]=='label_order_ko'` | KO-first 정렬 |
| DEFAULT_LOCALE_KO | `options.default_locale=='ko-KR'` | 기본 로캘 한국어 |
| SIGNATURE_MODE | `signature_mode=='sha256_auto_injected'` | 서명 자동 주입 |
| SCORE_FORMULA_EXISTS | `score_hint_formula != ''` | 점수 공식 존재 (Nitpick #2) |
| LITERACY_RULES_NONEMPTY | `len(literacy_based.rules) > 0` | 문예 규칙 비어있지 않음 (Nitpick #1) |

### Evidence Trace

- 모든 규칙은 `matched: true/false`와 근거 필드를 남긴다.
- KO-first 라벨을 기본으로 포함, zh/en은 UI에서 병기 가능.
- CI는 signature 주입 후 evidence 필드 키 일관성 검증.

---

## 8. 개선 사항 (v2.0)

### Nitpick #1: literacy_based 규칙 그룹 채움
- 문창/문곡/학당 규칙을 `year_branch_based`에서 `literacy_based`로 이동
- 문서와 구현 일치, 확장성 향상

### Nitpick #2: score_hint_mode 명확화
- `score_hint_formula` 필드 추가: `"total_score = sum(shensha.score_hint for shensha in all_matched)"`
- `score_hint_note_ko` 필드 추가: 집계 로직 한국어 설명

### Nitpick #3: TIAN_LA/DI_WANG 의미 명확화
- 기존 `assign_if_any: true` 방식 제거
- 각 기둥의 지지가 辰/戌/丑/未인지 확인하여 개별 부여
- Evidence trace에서 부여 범위 명확화

---

## 9. 참고 문헌

- 三命通會
- 淵海子平
- 神煞總論(현대 실무 편람)
- Modern Saju Practice

---

**생성일**: 2025-10-05
**버전**: 2.0
**엔진명(ko)**: 신살 매핑기 v2
