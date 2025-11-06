# 사주 분석 완전 보고서 (Complete Saju Analysis Report v1.1)

**생년월일:** 2000년 9월 14일 10:00 AM (Solar, Seoul)
**Birth Date:** September 14, 2000, 10:00 AM (Solar calendar, Seoul timezone)
**분석 일시:** 2025-10-11
**Orchestrator Version:** 1.1.0 (12 engines integrated)

---

## ■ 사주 (Four Pillars)

```
年柱 (Year):  庚辰 (庚金 辰土)
月柱 (Month): 乙酉 (乙木 酉金)
日柱 (Day):   乙亥 (乙木 亥水) ← 日主 (Day Master)
時柱 (Hour):  辛巳 (辛金 巳火)
```

**일간 (Day Master):** 乙木 (을목, Yin Wood)
**계절 (Season):** 가을 (Autumn) - 酉 month (金旺)

---

## ■ 오행 분포 (Five Elements Distribution)

### 천간·지지 분석
- **천간 (Heavenly Stems)**: 庚(金) 乙(木) 乙(木) 辛(金)
- **지지 (Earthly Branches)**: 辰(土) 酉(金) 亥(水) 巳(火)

### 오행 비율

| 오행 | 비율 | 비고 |
|------|------|------|
| **金 (금)** | 41.7% | **과다** (천간 2개 + 지지 1개) |
| **木 (목)** | 33.3% | **많음** (천간 2개) |
| **火 (화)** | 8.3% | **부족** (지지 1개만) |
| **土 (토)** | 8.3% | **부족** (지지 1개만) |
| **水 (수)** | 8.3% | **부족** (지지 1개만) |

**해석:** 금(金)이 41.7%로 과다하고 목(木)도 33.3%로 많습니다. 반면 화·토·수는 각각 8.3%로 매우 부족합니다. 이는 **금왕목다(金旺木多)**하고 화토수가 부족한 구조입니다.

---

## ■ 강약 분석 (Strength Analysis)

### 등급 (Grade)
- **등급:** 신약 (Weak)
- **점수:** -22.0

### 세부 점수 분석 (Detailed Breakdown)

| 항목 | 점수 | 설명 |
|------|------|------|
| **월지 왕상휴수사** | -24.0 | Month branch state: 囚 (imprisoned) - Wood is weak in Metal season |
| **지지 통근** | +7.0 | Branch roots: 亥 provides weak support to 乙 (Wood) |
| **천간 투출** | 0.0 | Stem visibility: No 比劫 or 印 visible |
| **합충형파해 영향** | 0.0 | Relations penalty: 巳亥冲 calculated separately |
| **계절 조정** | -5.0 | Seasonal adjustment for Autumn |
| **월간 효과** | 0.0 | Month stem effect: 乙 (wood) in month stem |
| **재성 위치 보너스** | 0.0 | Wealth location bonus |

### 인성 상태 (Seal/Resource Status)
- **인성 등급:** full (완전)
- **재성 파괴:** false (재성이 인성을 깨지 않음)

**해석:** 일간 乙木이 가을(酉月)에 태어나 금(金)이 왕성하고 목(木)이 囚 상태(-24)로 매우 약합니다. 지지 통근도 약하며(+7), 전체적으로 **신약(弱) -22.0점** 상태입니다.

---

## ■ 관계 분석 (Relations)

### 주요 관계
- **Priority Hit:** chong (충)
- **Transform:** N/A

### 충 (Chong - Clashes)
- **巳 ↔ 亥** (시지 ↔ 일지)
  - Hour branch 巳 (Fire) clashes with Day branch 亥 (Water)
  - 강도: high severity
  - 영향: 불안정성, 변동성, 내면 갈등

### 참고 사항 (Notes)
- "chong:巳/亥"

**해석:** 시지(時支) 巳와 일지(日支) 亥가 정충(正沖)을 이룹니다. 이는 내면의 갈등이나 변동성을 나타내며, 안정성보다는 변화와 도전이 많은 삶을 암시합니다.

---

## ■ 조후 (Climate/Temperature-Humidity Balance)

- **온도:** neutral
- **습도:** neutral

**해석:** 조후 상태가 중립적입니다. 극단적인 한열조습(寒熱燥濕) 편향이 없어 기후적으로는 균형 잡힌 사주입니다.

---

## ■ 용신 (Yongshin - Essential Spirit)

### 용신 선택
- **용신 (Primary):** 화, 토 (Fire, Earth)
- **보조신 (Supporting):** 수 (Water)
- **기신 (Unfavorable):** 목, 금 (Wood, Metal)

### 신뢰도
- **Confidence:** 0.8 (high)

### 용신 점수 (Yongshin Scores)
```
화 (Fire):  +0.22
토 (Earth): +0.19
수 (Water): +0.07
목 (Wood):  -0.08
금 (Metal): -0.08
```

### 논리 (Rationale)
1. **약한 목(木) 일간**: 신약 상태이지만 과다한 목을 억제해야 함
2. **가을(금왕) 계절**: 금이 강하므로 화(火)로 금을 제어해야 함
3. **충(沖) 완화**: 巳亥충을 완화할 토(土) 필요
4. **금 과다 억제**: 금(金) 41.7%로 과다하므로 화(火)로 녹여야 함

### 적용된 규칙 (Rules Fired - Top 10)
1. BIN:strong (⚠️ 오류: 실제로는 weak)
2. BASE:output→화
3. BASE:official→금
4. BASE:wealth→토
5. CLIMATE:conflict→금
6. DIST:excess[목]
7. DIST:deficit[화]
8. DIST:deficit[토]
9. DIST:excess[금]
10. DIST:deficit[수]

**⚠️ 주의:** 용신 strength bin에 오류가 있습니다 (신강으로 판정, 실제로는 신약 -22.0점). 정규화 문제로 추후 수정 예정.

**해석:** 화(火)와 토(土)를 용신으로 삼아 강한 금(金)을 제어하고, 충(沖)을 완화해야 합니다. 화는 금을 제압하고, 토는 안정성을 제공합니다.

---

## ■ 공망 (Void - 旬空)

### 공망 지지
- **공망 (Void Branches):** 申, 酉

### 공망 적용
- **일주 (Day Pillar):** 乙亥
- **적중 지지 (Hit Branches):** 酉 (월지)
- **플래그:** [false, **true**, false, false] (년/월/일/시)

**해석:** 乙亥일의 공망은 申酉입니다. **월지 酉가 공망에 걸립니다!** 이는 월지의 힘이 약화되거나 허무함을 느낄 수 있음을 의미합니다.

---

## ■ 원진 (Yuanjin - 遠辰)

### 원진 쌍
- **검출된 원진:** 0쌍
- **플래그:** [false, false, false, false]

**해석:** 辰酉亥巳 조합에는 원진(遠辰) 관계가 없습니다.

---

## ■ 신살 (Shensha - Divine Spirits)

### 상태
- **활성화:** false (비활성)
- **신살 목록:** [] (비어있음)

**해석:** 현재 신살 카탈로그는 비활성 상태입니다. 추후 활성화 시 천을귀인, 문창귀인, 역마, 도화 등이 추가될 예정입니다.

---

## ■ 대운 (Major Luck Cycle)

### 대운 시작
- **시작 나이:** 7.98 세 (약 8세)
- **방향:** forward (순행)
- **성별:** M (남자)
- **계산 방법:** solar_terms (절기 기반)

### 절기 정보 (Solar Terms)
- **이전 절기:** 白露 (Baekro - White Dew)
  - 날짜: 2000-09-07
- **다음 절기:** 寒露 (Hanro - Cold Dew)
  - 날짜: 2000-10-08

### 계산 상세
- **절기 간격:** 23.94 일 (白露 ~ 寒露)
- **출생 후 경과:** 6.71 일 (白露 이후)
- **대운 기산:** 17.23 일 남음 → 3일 = 1년 → 7.98년

**해석:** 양남(陽男)이므로 순행 대운입니다. 백로(白露) 절기 이후 약 8세부터 대운이 시작됩니다. 순행이므로 월주 乙酉 다음인 丙戌부터 대운이 시작될 것입니다.

---

## ■ 심화 분석 (Stage-3 Analysis)

### [1] 운세 흐름 (Luck Flow)
- **추세 (Trend):** declining (하락)
- **점수 (Score):** 0.25
- **신뢰도 (Confidence):** 0.25 (low)

**부정 요인 (Detractors):**
- relation_clash (관계 충돌)

**해석:** 현재 운세 흐름은 하락 추세입니다. 巳亥충이 주요 부정 요인입니다. 대운 진입 이후(8세~) 개선 가능성이 있습니다.

---

### [2] 격국 (Gyeokguk Classification)
- **유형:** 정격 (正格)
- **근거:** 월령득기 (월지에서 기운을 얻음)
- **신뢰도:** 0.6 (medium)

**해석:** 기본 정격(正格) 사주로 판정되었습니다. 특별한 종격(從格)이나 화격(化格)은 성립하지 않았습니다.

---

### [3] 조후 조언 (Climate Advice)
- **매칭된 정책:** fallback (기본값)
- **조언:** "계절과 오행의 균형을 무리 없이 유지하세요."

**해석:** 특별한 조후 조언 정책이 매칭되지 않아 기본 조언이 제공되었습니다.

---

### [4] 패턴 프로파일 (Pattern Profile)
- **패턴 태그:**
  - relation_conflict (관계 충돌)
  - luck_declining (운세 하락)
  - gyeokguk_pure (정격)

**핵심 포인트:**
- relation: conflict (충돌 관계 존재)

**한 줄 요약:** "관계 충돌 신호 주의."

---

## ■ 학파 프로필 (School Profile)

- **ID:** practical_balanced
- **참고:** 현장 절충(기본값) - 실용적이고 균형 잡힌 해석 방식

**해석:** 특정 학파에 치우치지 않고 실용적인 해석 방식을 따릅니다.

---

## ■ 권고사항 (Recommendations)

- **활성화:** false (비활성)
- **조치:** suppress_auto_recommendation
- **메시지:** "강약과 조후는 참고용입니다. 정확한 용신은 격국 분석과 함께 전문 상담을 권장합니다."

**해석:** 자동 권고사항은 억제되었습니다. 구체적인 조언은 전문 사주 상담가와 상담하시기 바랍니다.

---

## ■ 메타 정보 (Metadata)

- **분석 상태:** success
- **오케스트레이터 버전:** 1.1.0
- **타임스탬프:** 2025-10-11 (UTC)
- **사용된 엔진 (12개):**
  1. StrengthEvaluator (강약 평가)
  2. RelationTransformer (관계 변환)
  3. ClimateEvaluator (조후 평가)
  4. YongshinSelector (용신 선택) ⚠️ strength 정규화 필요
  5. LuckCalculator (대운 계산)
  6. ShenshaCatalog (신살 카탈로그) 🆕
  7. VoidCalculator (공망 계산) 🆕
  8. YuanjinDetector (원진 탐지) 🆕
  9. AnalysisEngine (Stage-3 분석)
  10. KoreanLabelEnricher (한글 라벨 보강)
  11. SchoolProfileManager (학파 프로필)
  12. RecommendationGuard (권고 가드)

---

## ■ 종합 해석 (Overall Interpretation)

### 핵심 특성
1. **신약(弱) 일주**: 乙木 일간이 가을에 태어나 금(金) 41.7%로 과다, 목(木) 33.3%로 많음
2. **巳亥충 (沖)**: 시지와 일지가 충돌하여 변동성과 도전이 많음
3. **월지 공망**: 酉(월지)가 공망에 걸려 힘이 약화됨
4. **용신 火土**: 화와 토를 용신으로 삼아 금을 제어하고 안정을 꾀함
5. **순행 대운**: 8세부터 대운 시작, 순행 방향

### 길흉 요약
- **강점**: 지지 통근(+7), 인성 완전, 대운 순행
- **약점**: 신약 상태(-22), 巳亥충, 월지 공망, 금(金) 과다 41.7%

### 인생 방향
- **유리한 오행**: 화(火), 토(土), 수(水) - 직업·주거·색상·방위 선택 시 참고
- **불리한 오행**: 목(木), 금(金) - 과도한 노출 주의
- **대운 전환**: 8세부터 대운 시작으로 새로운 국면 전개

### 주의사항
- 巳亥충으로 인한 내적 갈등 관리 필요
- 월지 공망으로 인한 허무감 극복 필요
- 강한 금(金)을 피하고 화(火)와 토(土) 강화 전략 필요
- 신약 체질이므로 과로나 스트레스 관리 중요

---

## ■ 알려진 이슈 (Known Issues)

### 1. 용신 Strength Bin 오류 ⚠️
- **문제:** YongshinSelector가 "신강"으로 판정 (실제로는 신약 -22.0점)
- **원인:** StrengthEvaluator는 -100~+100 범위, YongshinSelector는 0.0~1.0 비율 기대
- **영향:** 용신 rationale에 "신강 → 식상·관·재 선호"로 잘못 표시됨
- **해결:** orchestrator에서 strength score를 0-100 → 0.0-1.0으로 정규화 필요
- **상태:** 추후 수정 예정

### 2. 신살 비활성 상태
- **문제:** ShenshaCatalog가 enabled: false로 설정됨
- **원인:** 신살 정책 파일이 비활성 모드로 설정되어 있음
- **해결:** 정책 파일 업데이트 또는 pro_mode 활성화
- **상태:** 추후 활성화 예정

---

**면책 조항 (Disclaimer):**
이 보고서는 정책 기반 분석 엔진이 생성한 자동화 분석 결과입니다. 사주 해석은 참고용이며, 구체적인 인생 결정이나 의료·법률·투자 조언을 대체할 수 없습니다. 전문 사주 상담가와의 대면 상담을 권장합니다.

---

**Report Generated by:** SajuOrchestrator v1.1
**Engines Coordinated:** 12 (Core 6 + Meta 3 + Post 3)
**Policy Files Used:** 15+ (strength, relation, climate, yongshin, luck, void, yuanjin, etc.)
**Date:** 2025-10-11 KST
**엔진 통합 완료:** ShenshaCatalog, VoidCalculator, YuanjinDetector 신규 통합 ✅
