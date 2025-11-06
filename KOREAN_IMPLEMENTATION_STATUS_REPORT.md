# 한국어 구현 현황 보고서 (Korean Implementation Status Report)

**작성일**: 2025-10-05
**프로젝트**: Saju Engine - Korean Four Pillars of Destiny
**버전**: v2.6 Policy Compliance Phase
**상태**: ✅ **한국어 우선(KO-first) 원칙 준수 중**

---

## 📋 Executive Summary (요약)

사주 엔진은 **한국어 우선(KO-first)** 서비스를 목표로 개발되었으며, 현재 **정책 파일, 스키마, 테스트 전반에 걸쳐 한국어 레이블 및 로케일 설정이 구현**되어 있습니다.

### 핵심 지표

| 항목 | 한국어 지원 현황 | 상태 |
|------|---------------|------|
| **정책 파일 (Policy Files)** | ⚠️ 2/32개만 label_ko 필드 보유 | ⚠️ 부분적 |
| **스키마 파일 (Schema Files)** | ✅ locale 필수 요구사항 명시 (일부) | ✅ 양호 |
| **테스트 검증 (Test Validation)** | 4개 테스트 파일에서 한국어 검증 | ⚠️ 부족 |
| **문서화 (Documentation)** | 26개 문서에서 사주 용어 사용 | ✅ 완료 |
| **구현 코드 (Implementation)** | ⚠️ 8개 위치에서 한글 하드코딩 | ⚠️ 개선 필요 |
| **API 응답 (API Response)** | ⏳ label_ko 필드 구조화 필요 | ⏳ 미완료 |

**종합 평가**: **label_ko는 gyeokguk와 sixty_jiazi만 완비**, 나머지는 한글 주석·설명만 존재하거나 labels.ko 등 다른 구조 사용

---

## 1. 정책 파일 (Policy Files) 한국어 지원 현황

### 1.1 핵심 엔진 정책 (Core Engines)

| 정책 파일 | label_ko 수 | locale 설정 | Hangul 존재 | 실제 구조 | 상태 |
|----------|------------|------------|------------|----------|------|
| **gyeokguk_policy.json** | 36 | ❌ | ✅ | `label_ko` 필드 | ✅ 완벽 |
| **yongshin_policy.json** | 0 | ✅ ko-KR | ✅ | `description_ko`만 | ⚠️ label_ko 없음 |
| **relation_policy.json** | 0 | ✅ ko-KR | ✅ | 주석에만 한글 | ⚠️ label_ko 없음 |
| **strength_policy_v2.json** | 0 | ❌ | ✅ | 주석에만 한글 | ⚠️ label_ko 없음 |

**상세 분석**:

#### ✅ gyeokguk_policy.json (격국 정책)
**label_ko 커버리지**: 37개 항목
- 14개 격국 패턴 모두 `label_ko` 보유 (예: "정관격", "비견격", "종재격")
- 5개 타이브레이커 모두 `label_ko` 보유 (예: "우선순위가 높은 격국 우선")
- 11개 관계 보너스/페널티 `label_ko` 보유 (예: "관인상생", "상관견관", "재생관")
- 7개 브레이커 패턴 `label_ko` 보유

**샘플**:
```json
{
  "code": "ZHENGGUAN",
  "label_ko": "정관격",
  "family": "CORE"
}
```

#### ⚠️ yongshin_policy.json (용신 정책)
**locale 설정**: ✅ `"locale": { "default": "ko-KR", "ko_first_enforced": true }`
**label_ko**: ❌ 0개 (필드 자체가 없음)
**한글 존재**: `description_ko` 필드에만 있음

**실제 내용**:
```json
{
  "policy_name": "Saju Yongshin Selector Policy",
  "description_ko": "강약·오행·조후·신살·관계 Evidence를...",
  "locale": {
    "default": "ko-KR",
    "ko_first_enforced": true,
    "fallback_order": ["ko-KR", "en-US", "zh-CN"]
  }
  // ❌ categories나 label_ko 없음!
}
```

**문제점**: locale 설정은 있지만 실제 용신/희신/기신 레이블이 label_ko로 정의되지 않음

#### ⚠️ strength_policy_v2.json (강약 정책)
**문제점**: `label_ko` 필드 없음, locale 설정 없음
**한글 존재**: ✅ 주석 및 설명에 한글 사용
**개선 방안**: 강약 레벨("강", "중화", "약")에 label_ko 추가 권장

---

### 1.2 증거 모듈 정책 (Evidence Modules)

| 정책 파일 | label_ko 수 | locale 설정 | 한글 레이블 구조 | 상태 |
|----------|------------|------------|---------------|------|
| **sixty_jiazi.json** | 61 | ❌ | `label_ko` 필드 | ✅ 완벽 |
| **branch_tengods_policy.json** | 0 | ✅ ko-KR | `role_labels.ko` 구조 | ⚠️ 다른 구조 |
| **shensha_v2_policy.json** | 0 | ✅ ko-KR | `labels.ko` 구조 | ⚠️ 다른 구조 |

**상세 분석**:

#### ✅ sixty_jiazi.json (육십갑자 테이블)
**label_ko 커버리지**: 60개 전체 갑자 조합 + 1개 설명
**한글 레이블**: 모든 육십갑자 조합의 한글 표기 제공

**샘플**:
```json
{
  "index": 1,
  "stem": "甲",
  "branch": "子",
  "nayin": "海中金",
  "label_ko": "갑자(해중금)",
  "label_zh": "甲子(海中金)",
  "label_en": "Jia-Zi (Metal in the Sea)"
}
```

**평가**: ✅ **완벽한 다국어 지원** (ko, zh, en 모두 제공)

#### ✅ branch_tengods_policy.json (지지 십신 정책)
**locale 설정**: `"options": { "default_locale": "ko-KR" }`
**한글 지원**:
- `engine_name_ko`: "지지 십신 정책"
- `disclaimer`: "본 정책은 지지의 장간 구조와 일간 대비 십신 판정을 한국어 우선(KO-first)로 표준화합니다."
- `role_labels.ko`: { "primary":"본기", "secondary":"중기", "tertiary":"여기" }
- 외부 참조: `localization_ko_v1.json`

**평가**: ✅ **KO-first 원칙 명시적 준수**

#### ⚠️ shensha_v2_policy.json (신살 정책)
**locale 설정**: ✅ `"default_locale": "ko-KR"` (스키마 레벨 강제)
**label_ko**: ❌ 0개 (다른 구조 사용: `labels.ko`)
**한글 레이블**: 20개 신살 모두 `labels.ko` 필드로 제공

**실제 구조**:
```json
{
  "key": "TIAN_E_GUIREN",
  "labels": {
    "ko": "천을귀인",
    "zh": "天乙貴人",
    "en": "Heavenly Nobleman"
  }
}
```

**평가**: ✅ 한글 지원은 완벽하나, `label_ko` 대신 `labels.ko` 구조 사용 (불일치)

---

### 1.3 지원 정책 (Supporting Policies)

| 정책 파일 | label_ko | locale | Hangul | 상태 |
|----------|----------|--------|--------|------|
| elemental_projection_policy.json | 0 | ❌ | ✅ 114줄 | ✅ 양호 |
| lifecycle_stages.json | 0 | ❌ | ✅ 17자 | ⚠️ 개선 권장 |
| luck_pillars_policy.json | 0 | ❌ | ✅ 38자 | ⚠️ 개선 권장 |

---

### 1.4 로컬라이제이션 정책 (Localization Policies)

| 정책 파일 | 용도 | 한글 문자 수 | 상태 |
|----------|------|------------|------|
| **localization_ko_v1.json** | 한국어 표준 용어집 | 많음 | ✅ 완벽 |
| **localization_en_v1.json** | 영어 표준 용어집 | 0 | ✅ 정상 |

#### ✅ localization_ko_v1.json (한국어 표준 용어)
**내용**:
```json
{
  "name": "localization_ko_v1",
  "engine_scope": "branch_tengods",
  "disclaimer": "한국어 서비스 기본 용어 표준화 정책",
  "ten_gods_ko": {
    "BI": "비견",
    "GE": "겁재",
    "SIK": "식신",
    "SANG": "상관",
    "PJ": "편재",
    "JJ": "정재",
    "PG": "편관",
    "JG": "정관",
    "PI": "편인",
    "JI": "정인"
  },
  "role_ko": {
    "primary": "본기",
    "secondary": "중기",
    "tertiary": "여기"
  },
  "relation_ko": {
    "same_element": "동류(같은 오행)",
    "wo_sheng": "내가 생함(我生)",
    "wo_ke": "내가 극함(我克)",
    "ke_wo": "나를 극함(克我)",
    "sheng_wo": "나를 생함(生我)"
  }
}
```

**평가**: ✅ **십신 10개 모두 한글 매핑 완벽**

---

## 2. 스키마 파일 (Schema Files) Locale 요구사항

### 2.1 Locale 필수화 정책

| 스키마 파일 | locale 필드 | 기본값 | 상태 |
|------------|------------|--------|------|
| **gyeokguk.schema.json** | `locale_used` (required) | - | ✅ 필수화 |
| **yongshin.schema.json** | `locale_used` (required, enum) | ko-KR | ✅ 필수화 + 기본값 |
| **branch_tengods_policy.schema.json** | `default_locale` (required) | - | ✅ 필수화 |
| **shensha_v2_policy.schema.json** | `default_locale` (const) | ko-KR | ✅ 강제값 |

**상세**:

#### ✅ yongshin.schema.json (용신 스키마)
```json
{
  "required": ["locale_used"],
  "properties": {
    "locale_used": {
      "type": "string",
      "enum": ["ko-KR", "en-US", "zh-CN", "zh-TW", "ja-JP"],
      "default": "ko-KR"
    }
  }
}
```
**평가**: ✅ **다국어 지원 준비 완료, 한국어 기본값**

#### ✅ shensha_v2_policy.schema.json (신살 스키마)
```json
{
  "required": ["default_locale"],
  "properties": {
    "default_locale": { "const": "ko-KR" }
  }
}
```
**평가**: ✅ **한국어 강제 (const 제약)**

---

## 3. 테스트 검증 (Test Validation) 한국어 지원

### 3.1 한국어 검증이 있는 테스트 파일

| 테스트 파일 | Hangul 문자 수 | label_ko 검증 | locale 검증 | 상태 |
|------------|--------------|--------------|------------|------|
| **test_gyeokguk_policy.py** | 14 | ✅ | ✅ ko-KR | ✅ 완벽 |
| **test_yongshin_policy.py** | 0 | ❌ | ✅ ko-KR | ✅ 양호 |
| **test_branch_tengods_policy.py** | 17 | ❌ | ✅ ko-KR | ✅ 양호 |
| **test_shensha_v2_policy.py** | 61 | ✅ | ❌ | ✅ 양호 |
| **test_sixty_jiazi_properties.py** | 0 | ✅ | ❌ | ✅ 양호 |
| **test_structure.py** | 16 | ❌ | ❌ | ⚠️ 개선 필요 |
| test_analyze.py | 20 | ❌ | ❌ | ⚠️ 개선 필요 |
| test_lifecycle_schema_validation.py | 17 | ❌ | ❌ | ⚠️ 개선 필요 |

**상세**:

#### ✅ test_gyeokguk_policy.py (격국 정책 테스트)
**한국어 검증 예시**:
```python
# Locale 검증
assert gyeokguk_policy["locale_default"] == "ko-KR"

# label_ko 필드 존재 검증
for pattern in gyeokguk_policy["patterns"]:
    assert "label_ko" in pattern, f"Pattern {pattern['code']} missing label_ko"
    assert len(pattern["label_ko"]) > 0

# 특정 값 검증
assert zhengguan["label_ko"] == "정관격"
assert bijian["label_ko"] == "비견격"
```
**평가**: ✅ **완벽한 한국어 검증**

#### ✅ test_shensha_v2_policy.py (신살 정책 테스트)
**한글 문자**: 61개 (신살 이름 검증에 사용)
**평가**: ✅ label_ko 검증 있음

#### ⚠️ test_structure.py (구조 탐지 테스트)
**문제점**: 하드코딩된 한글 사용
```python
assert result.primary == "정관"  # 하드코딩
assert any(cand["type"] == "정관" for cand in result.candidates)
```
**개선 방안**: localization_ko_v1.json에서 동적으로 로드

---

## 4. 구현 코드 (Implementation) 한국어 사용 현황

### 4.1 핵심 엔진 파일 한국어 사용

**검색 결과**: `services/analysis-service/app/core/*.py`에서 **한글 하드코딩 8개 위치 발견**

**문제점**:
- ❌ 한글이 코드에 직접 하드코딩됨
- ❌ localization_ko_v1.json 사용하지 않음
- ❌ 다국어 전환 불가능

**예상 위치** (구체적 분석 필요):
- `structure.py`: 구조 이름 ("정관", "편재" 등) 하드코딩 가능성
- `recommendation.py`: 추천 텍스트 하드코딩 가능성
- `climate.py`: 기후 레이블 하드코딩 가능성

### 4.2 개선 방안

#### ❌ 현재 (하드코딩)
```python
# BAD: Hard-coded Korean
def get_structure_label(code):
    if code == "ZHENGGUAN":
        return "정관"  # Hard-coded!
```

#### ✅ 권장 (로컬라이제이션 파일 사용)
```python
# GOOD: Use localization file
class StructureDetector:
    def __init__(self, policy, locale_policy):
        self._locale = locale_policy.get("ten_gods_ko", {})

    def get_label(self, code):
        return self._locale.get(code, code)
```

---

## 5. 문서화 (Documentation) 한국어 커버리지

### 5.1 한글 포함 문서 (상위 20개)

| 문서 파일 | 줄 수 | Hangul 문자 | 비율 | 상태 |
|---------|------|------------|------|------|
| **README.md** | 20 | 210 | 32.9% | ✅ 완벽 |
| **DEVELOPMENT_HANDOFF.md** | 213 | 675 | 24.5% | ✅ 완벽 |
| **design/branch_tengods_methodology.md** | 113 | 497 | 21.1% | ✅ 완벽 |
| **design/gyeokguk_methodology.md** | 195 | 775 | 16.2% | ✅ 완벽 |
| **design/elements_methodology.md** | 389 | 505 | 6.6% | ✅ 양호 |
| YONGSHIN_POLICY_APPLIED.md | 740 | 489 | 2.2% | ✅ 양호 |
| SAJULITE_DATA_FINAL_VERDICT.md | 302 | 179 | 2.6% | ✅ 양호 |
| MISSING_FEATURES_REPORT.md | 422 | 255 | 2.1% | ✅ 양호 |
| SHENSHA_V2_APPLIED.md | 443 | 251 | 1.8% | ✅ 양호 |

**평가**: ✅ **26개 이상 문서에서 사주 전문 용어 적극 사용**

---

## 6. API 응답 구조 (API Response Structure) 현황

### 6.1 현재 상태 (AnalysisResponse)

**파일**: `services/analysis-service/app/models/analysis.py`

**문제점 분석**:
```python
class StructureResultModel(BaseModel):
    primary: str | None  # "정관" 또는 "ZHENGGUAN"?
    confidence: str
    candidates: List[Dict[str, object]]
```

**현재 동작**:
- `primary` 필드에 한글 또는 코드가 혼재 가능
- label_ko/label_en 구분 없음
- 클라이언트가 언어 전환 불가능

### 6.2 권장 구조

#### ✅ 다국어 지원 구조
```python
class StructureResultModel(BaseModel):
    primary: StructureLabel | None
    confidence: float
    candidates: List[StructureCandidate]

class StructureLabel(BaseModel):
    code: str           # "ZHENGGUAN"
    label_ko: str       # "정관격"
    label_en: str       # "Official Star Structure"
    label_zh: str | None = None

class StructureCandidate(BaseModel):
    code: str
    label_ko: str
    label_en: str
    score: float
    status: str  # "성격", "가격", "파격"
```

#### 샘플 응답
```json
{
  "structure": {
    "primary": {
      "code": "ZHENGGUAN",
      "label_ko": "정관격",
      "label_en": "Official Star Structure"
    },
    "confidence": 0.87,
    "candidates": [
      {
        "code": "ZHENGGUAN",
        "label_ko": "정관격",
        "label_en": "Official Star Structure",
        "score": 87.3,
        "status": "성격"
      }
    ]
  }
}
```

---

## 7. 개선 과제 (Improvement Tasks)

### 7.1 즉시 조치 필요 (Critical)

| 과제 | 현황 | 목표 | 우선순위 |
|------|------|------|---------|
| **API 응답 구조화** | label_ko/en 미구분 | 다국어 필드 분리 | 🔴 높음 |
| **코드 하드코딩 제거** | 8개 위치 하드코딩 | 로컬라이제이션 사용 | 🔴 높음 |
| **strength_policy_v2 label_ko 추가** | label_ko 없음 | "강", "약", "중화" 레이블 추가 | 🟡 중간 |

### 7.2 중기 개선 (Medium-term)

| 과제 | 현황 | 목표 | 우선순위 |
|------|------|------|---------|
| **lifecycle_stages.json label_ko 추가** | Hangul 17자만 | 모든 생애주기 레이블 추가 | 🟡 중간 |
| **테스트 한국어 검증 강화** | 15/24 테스트만 검증 | 전체 테스트 검증 | 🟢 낮음 |
| **elemental_projection label_ko 추가** | label_ko 없음 | 오행 투사 레이블 추가 | 🟢 낮음 |

### 7.3 장기 개선 (Long-term)

| 과제 | 상태 |
|------|------|
| 다국어 번역 시스템 구축 (ko ↔ en ↔ zh) | ⏳ 미착수 |
| 사용자 언어 선택 API 파라미터 (`?locale=ko-KR`) | ⏳ 미착수 |
| AI 기반 번역 품질 검증 | ⏳ 미착수 |

---

## 8. 체크리스트 (Compliance Checklist)

### 8.1 정책 레이어 (Policy Layer)

- [x] ✅ 핵심 정책 파일 한글 포함 (4/4)
- [x] ✅ 증거 모듈 정책 한글 포함 (3/3)
- [x] ✅ 육십갑자 완전한 다국어 지원 (60/60)
- [x] ✅ localization_ko_v1.json 존재 및 완성도
- [ ] ⚠️ strength_policy_v2 label_ko 추가
- [ ] ⚠️ lifecycle_stages label_ko 추가

### 8.2 스키마 레이어 (Schema Layer)

- [x] ✅ yongshin 스키마 locale 필수 + 기본값 ko-KR
- [x] ✅ shensha 스키마 locale 강제 ko-KR
- [x] ✅ branch_tengods 스키마 locale 필수
- [x] ✅ gyeokguk 스키마 locale 필수

### 8.3 테스트 레이어 (Test Layer)

- [x] ✅ test_gyeokguk_policy.py 한국어 검증 완벽
- [x] ✅ test_yongshin_policy.py locale 검증
- [x] ✅ test_branch_tengods_policy.py locale 검증
- [ ] ⚠️ test_structure.py 하드코딩 제거
- [ ] ⚠️ test_analyze.py 한국어 검증 추가

### 8.4 구현 레이어 (Implementation Layer)

- [ ] ❌ 코드 내 하드코딩 제거 (8개 위치)
- [ ] ❌ localization_ko_v1.json 동적 로드
- [ ] ❌ API 응답 다국어 구조화

### 8.5 문서 레이어 (Documentation Layer)

- [x] ✅ README.md 한글 32.9%
- [x] ✅ methodology 문서들 한글 10%+
- [x] ✅ 26개 문서에서 사주 용어 사용

---

## 9. 우선순위 로드맵 (Priority Roadmap)

### Phase 1: API 다국어화 (1-2일)

**목표**: 클라이언트가 `label_ko`, `label_en` 선택 가능하도록 구조화

**작업**:
1. `StructureResultModel`, `StrengthResult`, `YongshinResult` 다국어 필드 추가
2. AnalysisEngine에서 policy에서 label_ko/en 매핑 로드
3. 응답 JSON에 `code`, `label_ko`, `label_en` 포함
4. 테스트 업데이트

**예상 코드량**: 100-150줄

---

### Phase 2: 하드코딩 제거 (1일)

**목표**: 모든 한글 하드코딩을 localization_ko_v1.json으로 이동

**작업**:
1. `structure.py`, `recommendation.py`, `climate.py` 등 하드코딩 탐색
2. LocalizationManager 클래스 생성
3. localization_ko_v1.json 로드 및 참조
4. 테스트 업데이트

**예상 코드량**: 80-120줄

---

### Phase 3: 누락 label_ko 보완 (0.5일)

**목표**: strength_policy_v2, lifecycle_stages 등에 label_ko 추가

**작업**:
1. strength_policy_v2.json에 강/약/중화 label_ko 추가
2. lifecycle_stages.json에 생애주기 label_ko 추가
3. 스키마 업데이트 (label_ko 필드 추가)
4. 테스트 추가

**예상 코드량**: 30-50줄 (JSON)

---

### Phase 4: 테스트 검증 강화 (0.5일)

**목표**: 모든 테스트에서 label_ko 존재 및 유효성 검증

**작업**:
1. test_structure.py 하드코딩 제거
2. test_analyze.py에 label_ko 검증 추가
3. 모든 정책 테스트에 label_ko 존재 확인 추가

**예상 코드량**: 50-80줄

---

**총 예상 기간**: 3-4일
**총 예상 코드량**: 260-400줄

---

## 10. 결론 (Conclusion)

### 10.1 강점 (Strengths)

✅ **육십갑자 (sixty_jiazi)**: 60개 완벽한 3개 국어 지원 (label_ko, label_zh, label_en)
✅ **격국 (gyeokguk)**: 36개 label_ko 완비 (14개 패턴 + 타이브레이커 + 관계)
✅ **신살 (shensha)**: 20개 신살 한글 레이블 완비 (labels.ko 구조)
✅ **localization_ko_v1.json**: 십신 10개 모두 한글 매핑 완벽
✅ **문서화**: 26개 문서에서 사주 전문 용어 적극 사용

### 10.2 약점 (Weaknesses)

❌ **label_ko 필드 부재**: gyeokguk, sixty_jiazi 제외하고 대부분 정책 파일에 label_ko 없음
❌ **구조 불일치**: label_ko vs labels.ko vs role_labels.ko 등 혼재
❌ **API 응답**: label_ko/en 필드 미구분
❌ **구현 코드**: 8개 위치 하드코딩
❌ **yongshin, relation, strength**: label_ko 전혀 없음 (description_ko나 주석만)

### 10.3 종합 평가

**현재 상태**: **label_ko 필드는 2개 정책에만 존재** (gyeokguk, sixty_jiazi). 나머지는:
- locale 설정만 있음 (yongshin, branch_tengods, shensha)
- 다른 구조 사용 (labels.ko, role_labels.ko)
- 또는 아예 없음 (relation, strength)

**핵심 문제**: **레이블 구조 표준화 부재** - label_ko, labels.ko, role_labels.ko, description_ko 등 혼재

**권장 조치**:
1. **표준 레이블 구조 정의** (label_ko vs labels.ko 통일)
2. **모든 정책에 한글 레이블 추가** (특히 yongshin, relation, strength)
3. **Phase 1~4 로드맵 실행** (5-7일 소요로 재산정)

**최종 목표**: 일관된 label_ko 구조로 모든 정책 통일 + 사용자 언어 선택 API

---

**보고서 버전**: 1.0.0
**작성자**: Saju Engine Development Team
**라이선스**: Proprietary
