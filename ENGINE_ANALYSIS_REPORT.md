# 신약/용신 계산 엔진 분석 보고서

**Date:** 2025-10-11 KST
**Engines Analyzed:** StrengthEvaluator, YongshinSelector

---

## 1. StrengthEvaluator (신약 판정 엔진)

### 위치
`services/analysis-service/app/core/strength.py`

### 정책 파일
```
- strength_adjust_v1_3.json
- seasons_wang_map_v2.json
- root_seal_policy_v2_3.json
- zanggan_table.json
```

### 점수 계산 요소

#### 1. month_state (월지 왕상휴수사)
```python
def score_month_state(self, month_branch: str, day_stem: str) -> int:
    """
    일간이 월지에서 받는 세력 판정
    - 旺: +30
    - 相: +15
    - 休: 0
    - 囚: -15
    - 死: -30
    """
```

**1963-12-13 예시:**
- 일간: 庚金
- 월지: 子 (겨울, 水旺)
- 금은 수를 생(金生水) → 囚(갇힘)
- 점수: **-15**

#### 2. branch_root (지지 통근)
```python
def score_branch_roots(self, day_stem: str, day_branch: str,
                      other_branches: Iterable[str]) -> int:
    """
    지장간(支藏干)에서 일간 찾기
    - main (주기): 5점
    - sub (중기): 3점
    - minor (여기): 0점
    - month_bonus: +2점 (월지일 경우)
    """
```

**1963-12-13 예시:**
- 일간: 庚
- 지지: 卯(甲乙), 子(癸), 寅(甲丙戊), 戌(戊辛丁)
- 戌에 辛(sub) 있음: 3점
- 총점: **3**

#### 3. stem_visible (천간 투출)
```python
def score_stem_visible(self, visible_counts: Dict[str, int]) -> int:
    """
    천간에 나타난 십성별 가중치
    - 印(인성): 10점
    - 比劫(비겁): 8점
    - 食傷(식상): 6점
    - 財(재성): 6점
    - 官(관성): 6점
    """
```

#### 4. combo_clash (합충형파해)
```python
def score_combo_clash(self, combos: Dict[str, int]) -> int:
    """
    관계가 강약에 미치는 영향
    - 삼합(sanhe): +6
    - 육합(liuhe): +4
    - 충(chong): -8
    - 형(xing): -4
    - 파(po): -4
    - 해(hai): -4
    """
```

#### 5. season_adjust (계절 조정)
- 계절별 오행 보정 (미구현 상태로 보임)

#### 6. month_stem_effect (월간 효과)
```python
def calculate_month_stem_effect(self, month_stem_relation: str,
                                base_score: int) -> int:
    """
    월간이 일간과의 관계
    - counter (극): -15%
    - leak (설): -10%
    - assist (돕): +10%
    - none: 0%
    """
```

#### 7. wealth_location_bonus (재성 위치 보너스)
- 재성이 특정 위치에 있을 때 보너스

### 최종 등급 판정

```python
def determine_grade(self, total: float) -> tuple[str, str]:
    """
    점수를 등급으로 변환

    등급 체계 (grading_tiers):
    - 80~100: 신강 (또는 극신강)
    - 60~79:  편강
    - 40~59:  중화
    - 20~39:  편약
    - 0~19:   신약 (또는 극신약)
    """
    # Clamp to [0, 100]
    clamped = max(0, min(100, total))

    for tier in self.grading_tiers:
        if clamped >= tier["min"]:
            return tier["name"], tier["name"]

    return "신약", "신약"
```

### 1963-12-13 계산 결과

```
month_state:    -15 (囚)
branch_root:     +3 (戌中辛)
stem_visible:    ? (십성 계산 필요)
combo_clash:     ? (관계 계산 필요)
season_adjust:   0
month_stem_effect: ?
wealth_bonus:    0

총점: 15.0

등급 판정:
- 15점 → 0~19 범위
- grading_tiers에서 매칭
- 결과: "신약" (실제로는 극신약에 가까움)
```

### 문제점

**15점이 "신약"으로 표시되는 이유:**
1. `determine_grade()` 함수는 정책 파일의 `grading_tiers`를 순회
2. 15점은 0~19 범위에 해당
3. **정책 파일이 0~19를 "신약"으로 정의했을 가능성**
4. **또는 "극신약" 티어가 정책에 없을 가능성**

**포스텔러 "태약"과의 차이:**
- 포스텔러: 5단계 체계 (추정) - 극신강/신강/중화/신약/**태약**
- 우리: 5단계 체계 - 극신강/신강/중화/신약/극신약
- **15점은 "극신약"이 맞지만 "신약"으로 표시됨**

---

## 2. YongshinSelector (용신 선택 엔진)

### 위치
`services/analysis-service/app/core/yongshin_selector.py`

### 정책 파일
`policy/yongshin_selector_policy_v1.json`

### 알고리즘 (통합 접근)

```
1. Strength bin 판정 (weak/balanced/strong)
2. Base preferences 초기화
3. Relation bias 적용 (삼합/충/간합 등)
4. Climate bias 적용 (계절 영향)
5. Distribution bias 적용 (오행 과부족)
6. 정렬 후 yongshin/bojosin/gisin 결정
7. Confidence 계산
```

### 핵심 로직

#### 1. Base Preferences (강약 기반)

```python
def _apply_base_preferences(self, scores, day_element, strength_bin, rules_fired):
    """
    Base preferences:
    - weak (신약): ["resource", "companion"]  # 인성, 비겁
    - balanced (중화): ["resource", "output", "official"]
    - strong (신강): ["output", "wealth", "official"]  # 식상, 재성, 관성

    Bonuses:
    - resource (인성): +0.18
    - companion (비겁): +0.12
    - output (식상): +0.15
    - wealth (재성): +0.12
    - official (관성): +0.10
    """
```

**1963-12-13 예시 (신약 → weak bin):**
- 일간: 庚金
- resource (생我): 土生金 → 土 +0.18
- companion (同我): 金 → 金 +0.12

#### 2. Relation Bias (관계 영향)

```python
def _apply_relation_bias(self, scores, relation_summary, rules_fired):
    """
    관계가 용신에 미치는 영향:
    - sanhe → sanhe_element 강화
    - ganhe → ganhe_result 강화
    - chong → 완충 요소 필요
    - liuhe → 전체 완화
    """
```

#### 3. Climate Bias (계절 영향)

```python
def _apply_climate_bias(self, scores, day_element, climate, rules_fired):
    """
    계절 조화:
    - if_season_supports: +delta (계절이 도움)
    - if_season_conflicts: +delta (계절이 충돌)
    - support_labels: {"강함": +bonus, "약함": +penalty}
    """
```

**1963-12-13 예시:**
- 계절: 겨울 (水旺)
- 일간: 庚金 (金生水 → 설기)
- 문제: **조후 관점에서 火가 필요하지만, 이 로직은 火를 직접 선택하지 않음**

#### 4. Distribution Bias (오행 과부족)

```python
def _apply_distribution_bias(self, scores, elements_dist, rules_fired):
    """
    오행 균형 조정:
    - target_ratio: 0.20 (20% 목표)
    - deficit (부족): +gain (boost)
    - excess (과다): +penalty (penalize)
    """
```

**1963-12-13 예시:**
- 목: 33.3% → 과다 → 패널티
- 토: 8.3% → 부족 → 부스트

#### 5. Categorization (분류)

```python
def _categorize_elements(self, scores):
    """
    점수 정렬 후 분류:
    - yongshin: Top 1-2
    - bojosin: Middle 1-2
    - gisin: Bottom 1-2
    """
```

### 1963-12-13 계산 추정

```
초기 점수 (Base preferences - weak bin):
  土: +0.18 (resource)
  金: +0.12 (companion)
  목: 0.00
  화: 0.00
  수: 0.00

Distribution bias 적용:
  토: +0.18 + 부족보정(+) = 높음
  목: 0.00 + 과다패널티(-) = 낮음
  금: +0.12 = 중간
  수: 0.00 = 낮음
  화: 0.00 = 낮음

최종 정렬 (추정):
  1. 土 (가장 높음) → yongshin
  2. 金 (중간) → bojosin
  3. 목 (중간) → bojosin
  4. 화 (낮음) → gisin
  5. 수 (낮음) → gisin

결과:
  용신: [土]
  보조신: [金, 목]
  기신: [화, 수]
```

### 포스텔러와의 차이

| 측면 | 포스텔러 | 우리 (YongshinSelector) |
|------|----------|-------------------------|
| **철학** | 조후 + 억부 **분리** | 조후 + 억부 **통합** |
| **조후용신** | 火 (겨울 온난화) | ❌ 직접 선택 안 함 |
| **억부용신** | 金 (신약 돕기) | ✅ 土+金 (인성+비겁) |
| **결과** | 火 + 金 (이원화) | 土 (통합) |
| **전통성** | ✅ 더 전통적 | 🟡 현대적 해석 |

### 핵심 문제점

**YongshinSelector는 조후용신을 명시적으로 선택하지 않음!**

1. **Climate bias는 있지만:**
   - 계절 원소(水)에 대한 bonus/penalty만 적용
   - 조후 필요 원소(火)를 직접 선택하지 않음

2. **Base preferences가 지배적:**
   - weak bin → resource(土) + companion(金)
   - 이 점수가 climate bias보다 훨씬 큼

3. **결과:**
   - 土가 1순위 (억부 관점에서는 맞음)
   - 火는 base preference 점수가 낮아서 gisin으로 분류됨

**전통 사주학 관점:**
- 조후용신 우선 → 火 (겨울+庚金 → 따뜻함 필요)
- 억부용신 차순 → 金 또는 土 (신약 돕기)
- **둘 다 제시**하는 것이 정통

**우리 시스템:**
- 통합 점수로 하나만 선택
- 조후보다 억부(강약)가 지배적
- **土 단독 선택** (조후 무시됨)

---

## 3. 정책 파일 확인 필요

### strength_adjust_v1_3.json

```json
{
  "grading": {
    "tiers": [
      {"name": "???", "min": 80},
      {"name": "???", "min": 60},
      {"name": "???", "min": 40},
      {"name": "???", "min": 20},
      {"name": "신약", "min": 0}  // ← 15점이 여기 매칭?
    ]
  }
}
```

**확인 필요:**
- 0~19가 "신약" vs "극신약"?
- 20~39가 "편약" vs "신약"?

### yongshin_selector_policy_v1.json

```json
{
  "base_preferences": {
    "weak": ["resource", "companion"],    // 억부 중심
    "strong": ["output", "wealth", "official"]
  },
  "climate_bias": {
    "if_season_supports": 0.07,
    "if_season_conflicts": -0.05
  }
}
```

**문제:**
- climate_bias 값이 너무 작음 (0.07)
- base_preferences (0.18, 0.12)가 지배적
- **조후용신 명시적 선택 로직 없음**

---

## 4. 포스텔러 로직 추정

### 조후용신 선택 (1순위)

```
IF 계절 == 겨울 AND 일간 == 金:
    조후용신 = 火  // 온난화 필요

IF 계절 == 여름 AND 일간 == 火:
    조후용신 = 水  // 냉각 필요

... (계절별 규칙)
```

### 억부용신 선택 (2순위)

```
IF 신강/신약 == 태약:
    억부용신 = 生我(인성) OR 同我(비겁)

IF 신강/신약 == 극신강:
    억부용신 = 我生(식상) OR 我克(재성)
```

### 최종 결과

```
조후용신: 火
억부용신: 金 (또는 土)

→ 둘 다 제시
```

---

## 5. 결론

### StrengthEvaluator

**현재 상태:** ✅ 잘 작동하지만 등급 표시 개선 필요

**문제점:**
- 15점 → "신약" 표시 (실제로는 "극신약"에 가까움)
- 정책 파일의 grading_tiers 확인 필요

**해결 방안:**
1. `strength_adjust_v1_3.json`의 tiers 확인
2. 0~19를 "극신약"으로 재분류
3. 또는 "태약" 티어 추가

### YongshinSelector

**현재 상태:** ⚠️ 억부 중심, 조후 미흡

**문제점:**
1. 조후용신을 명시적으로 선택하지 않음
2. climate_bias가 너무 작아서 영향력 미미
3. base_preferences가 지배적
4. 통합 접근 → 하나만 선택

**해결 방안 옵션:**

#### 옵션 A: 조후 강화 (현재 구조 유지)
```python
# climate_bias 값을 크게 증가
"climate_bias": {
    "winter_needs_fire": 0.25,  # 기존 0.07에서 증가
    "summer_needs_water": 0.25
}
```

**장점:** 최소 변경
**단점:** 여전히 통합 방식, 전통과 다름

#### 옵션 B: 이원화 (전통 방식)
```python
def select(self, input_data):
    # 조후용신 먼저 선택
    climate_yongshin = self._select_climate_yongshin(...)

    # 억부용신 나중 선택
    strength_yongshin = self._select_strength_yongshin(...)

    return {
        "climate_yongshin": climate_yongshin,  # 火
        "strength_yongshin": strength_yongshin,  # 金 or 土
        "yongshin": [climate_yongshin, strength_yongshin]  # 둘 다
    }
```

**장점:** 전통 방식 정확히 구현
**단점:** 큰 구조 변경 필요

#### 옵션 C: 우선순위 체계
```python
# 1. 조후 우선 체크
if needs_climate_adjustment:
    primary_yongshin = climate_element
else:
    primary_yongshin = strength_element

# 2. 보조 용신
secondary_yongshin = other_element

return {
    "primary": primary_yongshin,
    "secondary": secondary_yongshin
}
```

**장점:** 중간 방식, 우선순위 명확
**단점:** 여전히 정책 수정 필요

---

## 6. 추천 액션

### 즉시 (High Priority)

1. **강약 등급 확인**
   - `strength_adjust_v1_3.json` 파일 읽기
   - grading_tiers의 0~19 범위가 "신약" vs "극신약" 확인
   - 필요시 정책 수정

2. **용신 정책 검토**
   - `yongshin_selector_policy_v1.json` 파일 읽기
   - climate_bias 값 확인
   - base_preferences와의 균형 검토

### 단기 (Medium Priority)

3. **조후용신 강화**
   - climate_bias 가중치 증가 (0.07 → 0.20+)
   - 겨울+金 → 火 선택 케이스 테스트

4. **검증 테스트**
   - 1963-12-13 케이스로 재테스트
   - 포스텔러와 비교

### 장기 (Low Priority)

5. **이원화 구조 검토**
   - 전통 방식(조후+억부 분리) 도입 여부 결정
   - API 변경 영향 검토
   - 하위 호환성 유지 방안

---

**보고서 작성:** Claude Code
**날짜:** 2025-10-11 KST
**분석 대상:** StrengthEvaluator, YongshinSelector
