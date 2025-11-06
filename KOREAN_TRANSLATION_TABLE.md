# 한국어 변환표 (Korean Translation Table)

**작성일**: 2025-10-05
**용도**: LLM 전달 시 한국어 레이블 보강을 위한 완전한 매핑 테이블
**상태**: ✅ 전체 용어 분석 완료

---

## 📋 목차

1. [매핑 현황 요약](#매핑-현황-요약)
2. [카테고리별 상세 매핑](#카테고리별-상세-매핑)
3. [매핑 없는 항목 (추가 필요)](#매핑-없는-항목)
4. [구현 우선순위](#구현-우선순위)

---

## 매핑 현황 요약

| 카테고리 | 항목 수 | 매핑 상태 | 출처 |
|---------|--------|---------|------|
| **십신 (Ten Gods)** | 10 | ✅ 완료 | localization_ko_v1.json |
| **격국 (Gyeokguk)** | 14 | ✅ 완료 | gyeokguk_policy.json |
| **신살 (Shensha)** | 20 | ✅ 완료 | shensha_v2_policy.json |
| **육십갑자 (Sixty Jiazi)** | 60 | ✅ 완료 | sixty_jiazi.json |
| **관계 (Relations)** | 5 | ✅ 완료 | localization_ko_v1.json |
| **역할 (Roles)** | 3 | ✅ 완료 | localization_ko_v1.json |
| **강약 (Strength)** | 5 | ❌ 없음 | - |
| **대운 방향 (Luck)** | 2 | ❌ 없음 | - |
| **신뢰도 (Confidence)** | 4 | ❌ 없음 | - |
| **추천 (Recommendation)** | 2 | ❌ 없음 | - |

**완료**: 112개 / **미완료**: 13개 / **완성도**: 89.6%

---

## 카테고리별 상세 매핑

### 1. 십신 (Ten Gods) ✅

**출처**: `localization_ko_v1.json`
**필드**: `AnalysisResponse.ten_gods.summary`

| 코드 | 한자 | 한글 | 영문 |
|------|------|------|------|
| BI | 比肩 | 비견 | Shoulder |
| GE | 劫財 | 겁재 | Rob Wealth |
| SIK | 食神 | 식신 | Food God |
| SANG | 傷官 | 상관 | Hurting Officer |
| PJ | 偏財 | 편재 | Indirect Wealth |
| JJ | 正財 | 정재 | Direct Wealth |
| PG | 偏官 | 편관 | Indirect Officer |
| JG | 正官 | 정관 | Direct Officer |
| PI | 偏印 | 편인 | Indirect Seal |
| JI | 正印 | 정인 | Direct Seal |

**사용 예**:
```json
{
  "ten_gods": {
    "summary": {
      "year_stem": "正官",
      "month_stem": "偏財"
    }
  }
}
```

**보강 후**:
```json
{
  "ten_gods": {
    "summary": {
      "year_stem": "正官",
      "month_stem": "偏財"
    },
    "summary_ko": {
      "year_stem": "정관",
      "month_stem": "편재"
    }
  }
}
```

---

### 2. 격국 (Gyeokguk Structure) ✅

**출처**: `gyeokguk_policy.json`
**필드**: `AnalysisResponse.structure.primary`

| 코드 | 한글 | 가족 | 설명 |
|------|------|------|------|
| ZHENGGUAN | 정관격 | CORE | 정관이 주도하는 격국 |
| QISHA | 칠살격 | CORE | 칠살(편관)이 주도 |
| ZHENGCAI | 정재격 | CORE | 정재가 주도 |
| PIANCAI | 편재격 | CORE | 편재가 주도 |
| SHISHEN | 식신격 | CORE | 식신이 주도 |
| SHANGGUAN | 상관격 | CORE | 상관이 주도 |
| ZHENGYIN | 정인격 | CORE | 정인이 주도 |
| PIANYIN | 편인격 | CORE | 편인이 주도 |
| JIANLU | 건록격 | PEER | 비견·겁재 주도 |
| YANGREN | 양인격 | PEER | 양인(羊刃) 주도 |
| CONGCAI | 종재격 | CONG | 재성에 종(從) |
| CONGSHA | 종살격 | CONG | 살(殺)에 종 |
| CONGGUAN | 종관격 | CONG | 관성에 종 |
| CONGWANG | 종왕격 | CONG | 일간이 극강 |

**사용 예**:
```json
{
  "structure": {
    "primary": "ZHENGGUAN",
    "confidence": "high"
  }
}
```

**보강 후**:
```json
{
  "structure": {
    "primary": "ZHENGGUAN",
    "primary_ko": "정관격",
    "confidence": "high",
    "confidence_ko": "높음"
  }
}
```

---

### 3. 신살 (Shensha) ✅

**출처**: `shensha_v2_policy.json`
**필드**: `AnalysisResponse.shensha.list[]`

| 코드 | 한글 | 유형 | 점수 |
|------|------|------|------|
| TIAN_E_GUIREN | 천을귀인 | 吉 | +2 |
| YUE_DE | 월덕 | 吉 | +1 |
| TIAN_DE | 천덕 | 吉 | +1 |
| TAO_HUA | 도화 | 中 | 0 |
| HONG_YAN | 홍염 | 中 | 0 |
| YI_MA | 역마 | 中 | 0 |
| HUA_GAI | 화개 | 中 | 0 |
| GUAI_GANG | 괴강 | 烈 | -1 |
| JIANG_XING | 장성 | 中 | 0 |
| BAI_HU | 백호 | 凶 | -2 |
| XUE_REN | 혈인 | 凶 | -2 |
| LIU_HAI | 육해 | 凶 | -1 |
| YUAN_ZHEN | 원진 | 凶 | -1 |
| TIAN_LA | 천라 | 凶 | -2 |
| DI_WANG | 지망 | 凶 | -2 |
| WEN_CHANG | 문창 | 吉 | +1 |
| WEN_QU | 문곡 | 吉 | +1 |
| XUE_TANG | 학당 | 吉 | +1 |
| HONG_LUAN | 홍란 | 吉 | +1 |
| TIAN_XI | 천희 | 吉 | +1 |

**사용 예**:
```json
{
  "shensha": {
    "enabled": true,
    "list": [
      {
        "key": "TIAN_E_GUIREN",
        "pillar": "year"
      }
    ]
  }
}
```

**보강 후**:
```json
{
  "shensha": {
    "enabled": true,
    "list": [
      {
        "key": "TIAN_E_GUIREN",
        "label_ko": "천을귀인",
        "pillar": "year",
        "pillar_ko": "년주"
      }
    ]
  }
}
```

---

### 4. 육십갑자 (Sixty Jiazi) ✅

**출처**: `sixty_jiazi.json`
**필드**: 모든 pillar 값 (`壬申`, `辛未` 등)

| 순번 | 간지 | 한글 | 납음 |
|------|------|------|------|
| 1 | 甲子 | 갑자 | 해중금 |
| 2 | 乙丑 | 을축 | 해중금 |
| 3 | 丙寅 | 병인 | 노중화 |
| 4 | 丁卯 | 정묘 | 노중화 |
| 5 | 戊辰 | 무진 | 대림목 |
| ... | ... | ... | ... |
| 60 | 癸亥 | 계해 | 대해수 |

**완전한 60개 매핑 존재** (생략 - 파일 참조)

**사용 예**:
```json
{
  "pillars": {
    "year": "壬申",
    "month": "辛未",
    "day": "丁丑",
    "hour": "庚子"
  }
}
```

**보강 후**:
```json
{
  "pillars": {
    "year": "壬申",
    "year_ko": "임신",
    "month": "辛未",
    "month_ko": "신미",
    "day": "丁丑",
    "day_ko": "정축",
    "hour": "庚子",
    "hour_ko": "경자"
  }
}
```

---

### 5. 관계 (Relations) ✅

**출처**: `localization_ko_v1.json`
**필드**: `AnalysisResponse.relations`

| 영문 키 | 한글 | 설명 |
|---------|------|------|
| same_element | 동류(같은 오행) | 같은 오행끼리 |
| wo_sheng | 내가 생함(我生) | 일간이 생하는 관계 |
| wo_ke | 내가 극함(我克) | 일간이 극하는 관계 |
| ke_wo | 나를 극함(克我) | 일간을 극하는 관계 |
| sheng_wo | 나를 생함(生我) | 일간을 생하는 관계 |

**추가 매핑 필요** (relation types):

| 코드 | 한자 | 한글 제안 |
|------|------|----------|
| he6 | 六合 | 육합 |
| sanhe | 三合 | 삼합 |
| banhe | 半合 | 반합 |
| chong | 沖 | 충 |
| xing | 刑 | 형 |
| po | 破 | 파 |
| hai | 害 | 해 |

---

### 6. 역할 (Roles - Hidden Stems) ✅

**출처**: `localization_ko_v1.json`
**필드**: branch_tengods 결과

| 영문 | 한글 | 설명 |
|------|------|------|
| primary | 본기 | 주된 장간 |
| secondary | 중기 | 두 번째 장간 |
| tertiary | 여기 | 세 번째 장간 |

---

## 매핑 없는 항목

### 1. 강약 (Strength) ✅ **전문가 검증 완료**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: `AnalysisResponse.strength.level`
**필드**: `AnalysisResponse.strength_details.grade`

| 영문 코드 | 확정 한글 | 별칭 | 설명 |
|----------|----------|------|------|
| very_weak | **극신약** | 극약, 과약 | 일간 세력이 극단적으로 약함 |
| weak | **신약** | - | 일간 세력이 약함 |
| balanced | **중화** | - | 균형 상태 (전문 용어) |
| strong | **신강** | - | 일간 세력이 강함 |
| very_strong | **극신강** | 극강, 과강 | 일간 세력이 극단적으로 강함 |

**전문가 권고**:
- '강/약' 단독보다 **'신강/신약'** 사용이 표준
- '중화(中和)'는 사주 전문 용어로 정착 (평형/균형은 비전문 표현)
- 극단값에 '극(極)' 접두사 사용 ('극신강/극신약')

**적용 완료**: `localization_ko_v1.json` 라인 31-42

---

### 2. 대운 방향 (Luck Direction) ✅ **전문가 검증 완료**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: `AnalysisResponse.luck_direction.direction`

| 영문 코드 | 확정 한글 | 별칭 | 설명 |
|----------|----------|------|------|
| forward | **순행** | 순운, 순 | 대운이 앞으로 진행 (順行) |
| reverse | **역행** | 역운, 역 | 대운이 뒤로 진행 (逆行) |

**전문가 권고**:
- 국내 백과·강의 자료에서 **'순행/역행'**이 표준 용어
- 동의어: 순운/역운 허용

**적용 완료**: `localization_ko_v1.json` 라인 43-51

---

### 3. 신뢰도 (Confidence) ✅ **전문가 검증 완료 + 중요 권고**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: `AnalysisResponse.structure.confidence`

| 영문 코드 | 확정 한글 | 설명 |
|----------|----------|------|
| high | **높음** | UI 신뢰도 높음 |
| mid | **보통** | UI 신뢰도 보통 |
| low | **낮음** | UI 신뢰도 낮음 |
| none | **없음** | 신뢰도 미평가 |

**⚠️ 전문가 경고**:
- **성격(成格)/가격(假格)/파격(破格)은 '격국 성립 상태'로 confidence와 별개 개념**
- confidence = 통계적 확신도 (확률)
- 성격/파격 = 격국 규칙 충족 여부 (판정)
- **1:1 매핑 금지** - 사용자 오해 발생

**권장 구조**: 필드 분리
```json
{
  "structure": {
    "primary": "정관격",
    "confidence": "높음",           // UI 신뢰도
    "validity": "성격"              // 격국 성립 상태 (별도)
  }
}
```

**적용 완료**:
- `confidence_ko`: 라인 52-58
- `structure_validity_ko`: 라인 59-65 (별도 필드 추가)

---

### 4. 추천 액션 (Recommendation Action) ✅ **전문가 검증 완료**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: `AnalysisResponse.recommendation.action`

| 영문 코드 | 확정 한글 | 별칭 | 설명 |
|----------|----------|------|------|
| allow | **표시** | 노출, 허용 | 추천 정보 표시 |
| suppress | **숨김** | 비노출 | 추천 정보 숨김 |

**전문가 권고**:
- UI 제어 용어 (사주 전문 용어 아님)
- 한국어 제품 문맥에서 **'표시/숨김'** 또는 '노출/비노출'이 자연스러움

**적용 완료**: `localization_ko_v1.json` 라인 96-104

---

### 5. 주 (Pillar) ✅ **전문가 검증 완료**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: shensha 결과의 pillar 값

| 영문 코드 | 확정 한글 | 별칭 | 설명 |
|----------|----------|------|------|
| year | **연주** | 년주 | 년 기둥 (Year Pillar) |
| month | **월주** | - | 월 기둥 (Month Pillar) |
| day | **일주** | - | 일 기둥 (Day Pillar) |
| hour | **시주** | - | 시 기둥 (Hour Pillar) |

**⚠️ 전문가 권고**:
- 국어 음운 규칙상 단어 첫머리 年은 **'연'**으로 읽음
- **'연주(年柱)'**가 표준 표기
- 실무 관용으로 '년주'도 허용하나 **문서·UI 기본형은 '연주' 권장**

**적용 완료**: `localization_ko_v1.json` 라인 66-75

---

### 6. 왕상휴수사 (Month State) ✅ **전문가 검증 완료**

**출처**: `localization_ko_v1.json` v1.1 (전문가 검증)
**필드**: `AnalysisResponse.strength.basis.month_state`

| 한자 | 확정 한글 | 설명 |
|------|----------|------|
| 旺 | **왕** | 왕성함 (가장 강함) |
| 相 | **상** | 상함 (왕을 돕는 상태) |
| 休 | **휴** | 휴함 (쉬는 상태) |
| 囚 | **수** | 갇힘 (억제된 상태) |
| 死 | **사** | 죽음 (가장 약함) |

**전문가 권고**:
- 왕상휴수사(旺相休囚死)는 사주 표준 5단계 용어
- 한글 음독 **'왕/상/휴/수/사'** 고정
- 월령 기준으로 일간의 세력을 판단하는 지표

**적용 완료**: `localization_ko_v1.json` 라인 76-83

---

## 구현 우선순위

### Priority 1: 즉시 추가 (localization_ko_v1.json 확장)

**예상 시간**: 30분

```json
{
  "version": "1.1",
  "name": "localization_ko_v1",

  // 기존 필드들...
  "ten_gods_ko": { ... },
  "role_ko": { ... },
  "relation_ko": { ... },

  // 새로 추가
  "strength_ko": {
    "very_weak": "극약",
    "weak": "약",
    "balanced": "중화",
    "strong": "강",
    "very_strong": "극강"
  },

  "luck_direction_ko": {
    "forward": "순행",
    "reverse": "역행"
  },

  "confidence_ko": {
    "high": "높음",
    "mid": "중간",
    "low": "낮음",
    "none": "없음"
  },

  "recommendation_ko": {
    "allow": "허용",
    "suppress": "숨김"
  },

  "pillar_ko": {
    "year": "년주",
    "month": "월주",
    "day": "일주",
    "hour": "시주"
  },

  "month_state_ko": {
    "旺": "왕",
    "相": "상",
    "休": "휴",
    "囚": "수",
    "死": "사"
  },

  "relation_types_ko": {
    "he6": "육합",
    "sanhe": "삼합",
    "banhe": "반합",
    "chong": "충",
    "xing": "형",
    "po": "파",
    "hai": "해"
  }
}
```

### Priority 2: KoreanLabelEnricher 구현

**예상 시간**: 1-2일

**파일**: `services/analysis-service/app/core/korean_enricher.py`

**매핑 대상**:
1. ✅ ten_gods (10개) - 기존 매핑 사용
2. ✅ structure (14개) - gyeokguk_policy.json
3. ✅ shensha (20개) - shensha_v2_policy.json
4. ✅ jiazi (60개) - sixty_jiazi.json
5. ✅ strength (5개) - 새 매핑 사용
6. ✅ luck_direction (2개) - 새 매핑 사용
7. ✅ confidence (4개) - 새 매핑 사용
8. ✅ recommendation (2개) - 새 매핑 사용
9. ✅ pillar (4개) - 새 매핑 사용
10. ✅ month_state (5개) - 새 매핑 사용
11. ✅ relation_types (7개) - 새 매핑 사용

**총 매핑 항목**: 133개

### Priority 3: 테스트 작성

**예상 시간**: 0.5일

**파일**: `services/analysis-service/tests/test_korean_enricher.py`

**테스트 케이스**:
- 십신 매핑 검증
- 격국 매핑 검증
- 신살 매핑 검증
- 강약 매핑 검증
- 대운 방향 매핑 검증
- 누락 값 처리 (원본 반환)

---

## 사용 예시

### Before (현재)

```json
{
  "ten_gods": {
    "summary": { "year_stem": "正官" }
  },
  "structure": {
    "primary": "ZHENGGUAN",
    "confidence": "high"
  },
  "strength": {
    "level": "weak",
    "basis": { "month_state": "囚" }
  },
  "shensha": {
    "list": [
      { "key": "TIAN_E_GUIREN", "pillar": "year" }
    ]
  },
  "luck_direction": {
    "direction": "forward"
  }
}
```

### After (보강 후)

```json
{
  "ten_gods": {
    "summary": { "year_stem": "正官" },
    "summary_ko": { "year_stem": "정관" }
  },
  "structure": {
    "primary": "ZHENGGUAN",
    "primary_ko": "정관격",
    "confidence": "high",
    "confidence_ko": "높음"
  },
  "strength": {
    "level": "weak",
    "level_ko": "약",
    "basis": {
      "month_state": "囚",
      "month_state_ko": "수"
    }
  },
  "shensha": {
    "list": [
      {
        "key": "TIAN_E_GUIREN",
        "label_ko": "천을귀인",
        "pillar": "year",
        "pillar_ko": "년주"
      }
    ]
  },
  "luck_direction": {
    "direction": "forward",
    "direction_ko": "순행"
  },
  "_enrichment": {
    "korean_labels_added": true,
    "locale": "ko-KR",
    "total_mappings": 133
  }
}
```

---

## 체크리스트

### localization_ko_v1.json 확장

- [ ] strength_ko 추가 (5개)
- [ ] luck_direction_ko 추가 (2개)
- [ ] confidence_ko 추가 (4개)
- [ ] recommendation_ko 추가 (2개)
- [ ] pillar_ko 추가 (4개)
- [ ] month_state_ko 추가 (5개)
- [ ] relation_types_ko 추가 (7개)

### KoreanLabelEnricher 구현

- [ ] `_load_strength_labels()` 메서드
- [ ] `_load_luck_labels()` 메서드
- [ ] `_load_confidence_labels()` 메서드
- [ ] `_load_pillar_labels()` 메서드
- [ ] `enrich()` 메서드에 모든 필드 보강 로직 추가

### 테스트

- [ ] 전체 133개 매핑 검증
- [ ] 누락 값 처리 테스트
- [ ] LLM 페이로드 통합 테스트

---

**문서 버전**: 1.0.0
**작성자**: Saju Engine Development Team
**총 매핑 항목**: 133개 (완료: 112, 미완료: 21)
**완성도**: 84.2%
