# 사주 프로젝트 — Claude 참조 문서 v1.0

**최종 갱신:** 2025-10-07 KST
**목적:** Claude가 매 세션마다 읽어야 할 프로젝트 구조, 정책, 구현 상태 중앙 허브

---

## 0. 프로젝트 개요

**사주 (四柱) - Korean Four Pillars of Destiny**

마이크로서비스 기반 사주 계산·분석·상담 시스템. 정책 기반 엔진 + LLM 폴리싱 하이브리드 아키텍처.

**핵심 원칙:**
- **정책 결정**: 엔진/정책 파일이 단독 결정 → LLM은 수정 금지
- **LLM 역할**: 설명/코칭/요약/문장 다듬기만 (템플릿 우선 → LLM 보강)
- **KO-first**: 한국어 라벨 병행 (*_ko 필드)
- **RFC-8785**: Canonical JSON + SHA-256 서명
- **Schema-first**: JSON Schema draft-2020-12 기반 검증

---

## 1. 아키텍처 플로우

```
Client (앱 4탭: 홈/채팅/더보기/사주계산)
  ↓
API Gateway
  ↓
  ├─→ tz-time-service (시간 변환: UTC/LMT/DST)
  │     ↓
  ├─→ astro-service (절기 계산: 24절기)
  │     ↓
  ├─→ pillars-service (기둥 계산: 년월일시 60갑자)
  │     ↓
  ├─→ analysis-service (핵심 분석 엔진)
  │     ├─ TenGodsCalculator (십신)
  │     ├─ RelationTransformer (육합/삼합/충/형/파/해/원진)
  │     ├─ StrengthEvaluator (강약: strength_policy_v2.json)
  │     ├─ StructureDetector (격국: gyeokguk_policy.json)
  │     ├─ ShenshaCatalog (신살: shensha_v2_policy.json)
  │     ├─ ClimateEvaluator (조후: 미통합)
  │     ├─ YongshinAnalyzer (용신: yongshin_policy.json)
  │     ├─ BranchTenGodsMapper (지장간 십신: branch_tengods_policy.json)
  │     ├─ KoreanLabelEnricher (한국어 라벨: localization_ko_v1.json)
  │     └─ (신규 예정) TwelveStageCalculator, VoidCalculator, YuanjinDetector
  │     ↓
  ├─→ luck-service (대운/연운/월운)
  │     ├─ LuckCalculator (대운 시작 나이/방향: luck_pillars_policy.json)
  │     └─ (신규 예정) AnnualLuckCalculator, MonthlyLuckCalculator
  │     ↓
  ├─→ llm-polish (템플릿→문장화)
  │     ├─ Light: Qwen Flash / DeepSeek-Chat → Fallback: Gemini 2.5 Pro
  │     └─ Deep: Gemini 2.5 Pro → Backstop: GPT-5
  │     ↓
  ├─→ LLMGuard (Pre/Post 검증: 계획만 존재)
  │     ├─ DETERMINISM, TRACE_INTEGRITY, EVIDENCE_BOUND
  │     ├─ POLICY_BOUND, KO_FIRST_LABELS, HARM_GUARD
  │     └─ 문서: LLM_GUARD_V1_ANALYSIS_AND_PLAN.md
  │     ↓
  ├─→ billing/entitlement/tokens (권한·토큰·리워디드: 미구현)
  │     ├─ plan: free/plus/pro
  │     ├─ light_daily_left, deep_tokens
  │     └─ ads_suggest: SSV verification
  │     ↓
  └─→ report-service (PDF 생성: 미구현)
```

---

## 2. 폴더 구조 매핑

### 2.1 현재 코드베이스 구조

```
/Users/yujumyeong/coding/ projects/사주/
├── services/
│   ├── tz-time-service/          ✅ 완전 구현
│   ├── astro-service/             ✅ 완전 구현
│   ├── pillars-service/           ✅ 완전 구현
│   │   └── app/core/
│   │       ├── pillars.py         (calculate_four_pillars - LMT 지원)
│   │       ├── canonical_calendar.py (orphaned)
│   │       └── input_validator.py
│   ├── analysis-service/          🟡 부분 구현 (80%)
│   │   ├── app/core/
│   │   │   ├── engine.py          (AnalysisEngine - 10/11 엔진 통합)
│   │   │   ├── strength.py        (WangStateMapper, StrengthEvaluator)
│   │   │   ├── relations.py       (RelationTransformer)
│   │   │   ├── luck.py            (LuckCalculator)
│   │   │   ├── school.py          (SchoolProfileManager)
│   │   │   ├── recommendation.py  (RecommendationGuard)
│   │   │   ├── text_guard.py      (TextGuard)
│   │   │   ├── climate.py         (ClimateEvaluator - 미통합)
│   │   │   ├── korean_enricher.py (KoreanLabelEnricher - 141 mappings)
│   │   │   └── policy_guards.py   (런타임 정책 검증)
│   │   ├── app/models/
│   │   │   └── analysis.py        (AnalysisRequest, AnalysisResponse)
│   │   └── tests/                 (47/47 passing)
│   ├── luck-service/              ❌ 미구현 (analysis-service에 임베디드)
│   ├── llm-polish/                ❌ 미구현
│   ├── llm-guard/                 ❌ 미구현 (계획만 존재)
│   └── report-service/            ❌ 미구현
├── saju_codex_batch_all_v2_6_signed/
│   ├── policies/                  ✅ 정책 파일 (RFC-8785 서명)
│   │   ├── strength_policy_v2.json
│   │   ├── relation_policy.json
│   │   ├── shensha_v2_policy.json
│   │   ├── gyeokguk_policy.json
│   │   ├── yongshin_policy.json
│   │   ├── branch_tengods_policy.json
│   │   ├── sixty_jiazi.json
│   │   ├── lifecycle_stages.json
│   │   ├── localization_ko_v1.json
│   │   ├── localization_en_v1.json
│   │   ├── luck_pillars_policy.json
│   │   ├── daystem_yinyang.json
│   │   ├── elemental_projection_policy.json
│   │   └── elements_distribution_criteria.json
│   └── schemas/                   ✅ JSON Schema (draft-2020-12)
│       ├── strength_policy_v2.schema.json
│       ├── relation.schema.json
│       ├── shensha_v2_policy.schema.json
│       ├── gyeokguk.schema.json
│       ├── yongshin.schema.json
│       └── (기타 9개)
├── scripts/                       ✅ 계산 검증 스크립트
│   ├── calculate_pillars_traditional.py (기둥 계산 엔진)
│   ├── analyze_2000_09_14_corrected.py (전체 분석 테스트)
│   └── (기타 30+ 검증 스크립트)
├── data/
│   ├── terms_*.csv                ✅ 절기 데이터 (1900~2050)
│   └── canonical/                 (백업)
├── docs/                          🆕 제안 구조 (미생성)
│   └── policy-prompts/
│       ├── README.md
│       ├── 00_master/
│       ├── 10_api-specs/
│       ├── 20_policy-engines/
│       ├── 30_llm/
│       ├── 40_tokens_entitlements_ads/
│       └── 50_cache_storage_qc/
├── API_SPECIFICATION_v1.0.md      ✅ 9개 엔드포인트 OpenAPI-lite
├── SAJU_REPORT_SCHEMA_v1.0.md     ✅ /report/saju JSON Schema + 샘플
├── LLM_GUARD_V1_ANALYSIS_AND_PLAN.md ✅ LLM Guard 구현 계획
└── (기타 분석/핸드오버 문서 20+)
```

### 2.2 제안된 docs/policy-prompts/ 구조

| 폴더                              | 목적                                 | 현재 상태 |
|-----------------------------------|--------------------------------------|-----------|
| `00_master/`                      | 통합 마스터 프롬프트                 | 미생성    |
| `10_api-specs/`                   | API 사양 프롬프트                    | 부분 완료 |
| ├─ `01_openapi_lite_prompt.md`    | 9개 엔드포인트 OpenAPI-lite          | ✅ 완료 (API_SPECIFICATION_v1.0.md) |
| ├─ `02_report_schema_prompt.md`   | /report/saju JSON Schema             | ✅ 완료 (SAJU_REPORT_SCHEMA_v1.0.md) |
| └─ `03_chat_send_spec_prompt.md`  | /chat/send 스펙                      | ⏳ 대기 |
| `20_policy-engines/`              | 정책/엔진 프롬프트                   | 미생성    |
| ├─ `relation_policy_extension_prompt.md` | 원진/조합원소 확장          | ⏳ 대기 |
| ├─ `twelve_stage_void_yuanjin_combo_prompt.md` | 12운성/공망/원진 | ⏳ 대기 |
| └─ `annual_monthly_luck_prompt.md` | 연운/월운 계산기                    | ⏳ 대기 |
| `30_llm/`                         | LLM 템플릿·가드·라우팅                | 미생성    |
| ├─ `llm_templates_5pack_prompt.md` | 오행/용신/강약/대운/연월운 템플릿 | ⏳ 대기 |
| ├─ `llm_guard_v1_prompt.md`       | LLM Guard v1.0 구현                  | 🟡 계획만 (LLM_GUARD_V1_ANALYSIS_AND_PLAN.md) |
| └─ `model_routing_policy_prompt.md` | Light/Deep 모델 라우팅              | ⏳ 대기 |
| `40_tokens_entitlements_ads/`     | 토큰·권한·리워디드                   | 미생성    |
| └─ `tokens_entitlements_ssv_prompt.md` | 토큰/권한/SSV 검증              | ⏳ 대기 |
| `50_cache_storage_qc/`            | 캐시/스토리지/QA                     | 미생성    |
| ├─ `cache_storage_idempotency_prompt.md` | 캐시/멱등성                  | ⏳ 대기 |
| └─ `qa_perf_release_plan_prompt.md` | QA/성능/릴리스 계획                | ⏳ 대기 |

---

## 3. 구현 상태 매트릭스

### 3.1 서비스별 구현 상태

| 서비스                  | 상태 | 완성도 | 비고 |
|-------------------------|------|--------|------|
| tz-time-service         | ✅   | 100%   | UTC/LMT/DST 변환 완전 구현 |
| astro-service           | ✅   | 100%   | 24절기 계산 완전 구현 |
| pillars-service         | ✅   | 100%   | calculate_four_pillars (LMT -32분 서울) |
| analysis-service        | 🟡   | 80%    | 10/11 엔진 통합, ClimateEvaluator 미통합 |
| luck-service            | 🟡   | 40%    | 대운 시작/방향만, 연/월운 미구현 |
| llm-polish              | ❌   | 0%     | 템플릿/라우팅 미구현 |
| llm-guard               | 🟡   | 10%    | 계획만 존재 (LLM_GUARD_V1_ANALYSIS_AND_PLAN.md) |
| billing/entitlement     | ❌   | 0%     | 토큰/권한 시스템 미구현 |
| report-service          | ❌   | 0%     | PDF 생성 미구현 |

### 3.2 Analysis-Service 엔진별 구현 상태

| 엔진                    | 통합 | 테스트 | 정책 파일 | 비고 |
|-------------------------|------|--------|-----------|------|
| TenGodsCalculator       | ✅   | ✅     | -         | 십신 계산 |
| RelationTransformer     | ✅   | ✅     | relation_policy.json | 육합/삼합/충/형/파/해 |
| StrengthEvaluator       | ✅   | ✅     | strength_policy_v2.json | 강약 평가 (Fix 적용) |
| StructureDetector       | ✅   | ✅     | gyeokguk_policy.json | 격국 탐지 |
| ShenshaCatalog          | ✅   | ✅     | shensha_v2_policy.json | 신살 |
| ClimateEvaluator        | ❌   | ✅     | -         | **구현됨, 미통합** |
| YongshinAnalyzer        | ✅   | ✅     | yongshin_policy.json | 용신 |
| BranchTenGodsMapper     | ✅   | ✅     | branch_tengods_policy.json | 지장간 십신 |
| LuckCalculator          | ✅   | ✅     | luck_pillars_policy.json | 대운 시작/방향 |
| KoreanLabelEnricher     | ✅   | ✅     | localization_ko_v1.json | 141 mappings |
| SchoolProfileManager    | ✅   | ✅     | -         | 학파 프로필 |
| RecommendationGuard     | ✅   | ✅     | -         | 권고사항 필터링 |
| TwelveStageCalculator   | ❌   | ❌     | lifecycle_stages.json | **12운성 미구현** |
| VoidCalculator          | ❌   | ❌     | -         | **공망 미구현** |
| YuanjinDetector         | ❌   | ❌     | -         | **원진 미구현** |
| CombinationElement      | ❌   | ❌     | -         | **조합오행 미구현** |

### 3.3 정책 파일 상태

| 정책 파일                        | 위치 | 서명 | 스키마 | 통합 |
|----------------------------------|------|------|--------|------|
| strength_policy_v2.json          | ✅   | ✅   | ✅     | ✅   |
| relation_policy.json             | ✅   | ✅   | ✅     | ✅   |
| shensha_v2_policy.json           | ✅   | ✅   | ✅     | ✅   |
| gyeokguk_policy.json             | ✅   | ✅   | ✅     | ✅   |
| yongshin_policy.json             | ✅   | ✅   | ✅     | ✅   |
| branch_tengods_policy.json       | ✅   | ✅   | ✅     | ✅   |
| sixty_jiazi.json                 | ✅   | ✅   | ✅     | ✅   |
| lifecycle_stages.json            | ✅   | ✅   | ✅     | ❌   |
| localization_ko_v1.json          | ✅   | ✅   | -      | ✅   |
| localization_en_v1.json          | ✅   | ✅   | -      | ❌   |
| luck_pillars_policy.json         | ✅   | ✅   | ✅     | ✅   |
| daystem_yinyang.json             | ✅   | ✅   | ✅     | ✅   |
| elemental_projection_policy.json | ✅   | ✅   | -      | 🟡   |
| elements_distribution_criteria.json | ✅ | ✅  | ✅     | 🟡   |

### 3.4 API 엔드포인트 구현 상태

| 엔드포인트               | 스펙 | 구현 | 테스트 | 비고 |
|--------------------------|------|------|--------|------|
| POST /report/saju        | ✅   | 🟡   | 🟡     | 스키마 완료, 서비스 부분 구현 |
| POST /chat/send          | ❌   | ❌   | ❌     | 스펙 대기 중 |
| POST /luck/annual        | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| POST /luck/monthly       | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| POST /tokens/reward      | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| POST /tokens/consume     | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| GET /entitlements        | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| POST /report/pdf         | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |
| POST /profiles           | 🟡   | ❌   | ❌     | 스펙 부분, 미구현 |

---

## 4. 공통 규약

### 4.1 파일 머리말 규칙

모든 프롬프트/정책/스키마 파일은 다음 형식을 따름:

```markdown
# <제목>

**Version:** <vMAJOR.MINOR>
**Date:** <YYYY-MM-DD KST>
**Spec:** <JSON Schema draft-2020-12 / OpenAPI 3.1 / Policy v2>

## ROLE
<역할 정의>

## GOAL
<목표 정의>

## OUTPUT ORDER
<산출물 순서>
```

### 4.2 JSON Schema 규칙

- **$schema**: `https://json-schema.org/draft/2020-12/schema`
- **$id**: 버전 포함 URI (예: `/schemas/report_saju_v1.schema.json`)
- **$defs**: 재사용 컴포넌트 적극 활용
- **description**: 모든 필드에 한국어/영어 설명 필수
- **enum**: 10간/12지/십신/12운성 등 고정 값
- **pattern**: 60갑자, IANA TZ, ISO8601, YYYY-MM 등
- **범위**: percent (0..100), score (0..100), age (0..20)

### 4.3 RFC-8785 서명

모든 JSON 산출물은 다음 구조 포함:

```json
{
  "meta": {
    "signatures": {
      "sha256": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a"
    }
  }
}
```

**검증 방법:**
```python
from canonicaljson import encode_canonical_json
import hashlib

canonical = encode_canonical_json(data)  # RFC-8785
computed = hashlib.sha256(canonical).hexdigest()
assert computed == data["meta"]["signatures"]["sha256"]
```

### 4.4 KO-first 라벨

모든 enum/code 필드는 `*_ko` 병행 필드 제공:

```json
{
  "strength": {
    "bucket": "신약",
    "bucket_ko": "신약"
  },
  "structure": {
    "primary": "정관격",
    "primary_ko": "정관격"
  },
  "luck_direction": {
    "direction": "reverse",
    "direction_ko": "역행"
  }
}
```

### 4.5 LLM 역할 제한

**허용:**
- 설명 문장화 (예: "일간이 약하므로...")
- 코칭 메시지 생성 (예: "이번 달 주의사항...")
- 요약 생성 (예: "핵심 특성 3가지")

**금지:**
- 정책 수치 변경 (예: strength.score 임의 조정)
- 관계 추가/삭제 (예: 충 관계 무시)
- 의료/법률/투자 구체 행위 조언

---

## 5. 엔진 빠른 참조

### 5.1 기둥 계산 (Pillars)

**엔진:** `calculate_four_pillars()` (scripts/calculate_pillars_traditional.py)

**파라미터:**
- `birth_dt`: datetime 객체
- `tz_str`: IANA timezone (예: "Asia/Seoul")
- `mode`: "traditional_kr" (한국 전통 방식)
- `zi_hour_mode`: "default" | "split_23" | "traditional"
- `use_refined`: True (정제된 절기 데이터 사용)
- `return_metadata`: True (LMT/DST 메타데이터 포함)

**출력:**
```python
{
  "year": "庚辰",
  "month": "乙酉",
  "day": "乙亥",
  "hour": "辛巳",
  "metadata": {
    "lmt_offset": -32,  # 서울 경도 보정 (분)
    "dst_applied": False,
    "zi_transition": False
  }
}
```

**지역별 LMT 보정:**
- 서울: -32분 (126.978°E)
- 부산: -24분 (129.075°E)
- 광주: -36분 (126.853°E)

### 5.2 분석 엔진 (Analysis)

**엔진:** `AnalysisEngine` (services/analysis-service/app/core/engine.py)

**호출 방법:**
```python
from app.core.engine import AnalysisEngine
from app.models.analysis import AnalysisRequest, PillarInput

engine = AnalysisEngine()
request = AnalysisRequest(
    pillars={
        "year": PillarInput(pillar="庚辰"),
        "month": PillarInput(pillar="乙酉"),
        "day": PillarInput(pillar="乙亥"),
        "hour": PillarInput(pillar="辛巳")
    },
    options={
        "birth_dt": "2000-09-14T10:00:00+09:00",
        "timezone": "Asia/Seoul"
    }
)
result = engine.analyze(request)
```

**출력:** AnalysisResponse (services/analysis-service/app/models/analysis.py:115)

**핵심 필드:**
- `ten_gods.summary`: 십신 매핑
- `relations.{he6,sanhe,chong,xing,po,hai}`: 관계 목록
- `strength.level`: 강약 등급 (극신강/신강/중화/신약/극신약)
- `strength_details.total`: 세력 점수
- `structure.primary`: 주격국
- `luck.start_age`: 대운 시작 나이
- `luck_direction.direction`: 순행/역행
- `shensha.list`: 신살 목록
- `school_profile.id`: 학파 ID

### 5.3 한국어 보강 (Korean Enricher)

**엔진:** `KoreanLabelEnricher` (services/analysis-service/app/core/korean_enricher.py)

**호출 방법:**
```python
from app.core.korean_enricher import KoreanLabelEnricher

enricher = KoreanLabelEnricher.from_files()
payload = result.model_dump()
enriched = enricher.enrich(payload)
```

**보강 통계:**
- 총 매핑: 141개
- 커버리지: 십신, 강약, 격국, 신살, 대운, 12운성, 육십갑자
- 테스트: 21/21 passing

### 5.4 강약 평가 (Strength)

**정책:** strength_policy_v2.json

**점수 계산 요소:**
1. `month_state`: 월지 왕상휴수사 (-30~+30)
2. `branch_root`: 지지 통근 (0~+25)
3. `stem_visible`: 천간 투출 (0~+15)
4. `combo_clash`: 합충형파해 보정 (-20~+20)
5. `season_adjust`: 계절 조정 (-10~+10)
6. `month_stem_effect`: 월간 효과 (-10~+10)
7. `wealth_location_bonus`: 재성 위치 보너스 (0~+10)

**등급 (bucket):**
- 극신강: 80~100
- 신강: 60~79
- 중화: 40~59
- 신약: 20~39
- 극신약: 0~19

**최근 수정 (2025-10-07):**
- `wealth_month_state`: WangStateMapper 통합 (engine.py:280-295)
- `wealth_seal_branch_conflict`: CHONG_PAIRS 기반 검증 (engine.py:307-337)
- 대운 시작 나이: 하드코딩 제거, options.birth_dt 사용 (engine.py:481-493)

### 5.5 관계 분석 (Relations)

**정책:** relation_policy.json

**천간 관계:**
- 합(combine): 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火
- 충(clash): 甲庚, 乙辛, 丙壬, 丁癸

**지지 관계:**
- 육합(he6): 子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未
- 삼합(sanhe): 申子辰水, 亥卯未木, 寅午戌火, 巳酉丑金
- 충(chong): 子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥
- 형(xing): 寅巳申, 丑戌未, 子卯, 辰辰, 午午, 酉酉, 亥亥
- 파(po): 子酉, 午卯, 辰丑, 未戌, 寅亥, 巳申
- 해(hai): 子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌
- 방합(directional): 寅卯辰東方木, 巳午未南方火, 申酉戌西方金, 亥子丑北方水
- 원진(yuanjin): 子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌 **(미구현)**

**우선순위:** he6 > sanhe > chong > xing > po > hai

### 5.6 신살 (Shensha)

**정책:** shensha_v2_policy.json

**주요 신살 (상위 20개):**
- 천을귀인(天乙貴人): 년/일간 기준 귀인
- 문창귀인(文昌貴人): 학업·문서
- 역마(驛馬): 이동·변화
- 도화(桃花): 인연·매력
- 화개(華蓋): 예술·종교
- 공망(空亡): 허무·공허 **(미구현)**
- 십이운성(十二運星): 장생~양 **(미구현)**

**현재 구현:** ShenshaCatalog (engine.py:522-539)
**미구현:** 공망, 십이운성 (별도 엔진 필요)

---

## 6. 정책 파일 빠른 참조

### 6.1 정책 파일 위치

```
saju_codex_batch_all_v2_6_signed/policies/
├── strength_policy_v2.json          # 강약 평가 정책
├── relation_policy.json             # 관계 (합충형파해) 정책
├── shensha_v2_policy.json           # 신살 정책
├── gyeokguk_policy.json             # 격국 탐지 정책
├── yongshin_policy.json             # 용신 정책
├── branch_tengods_policy.json       # 지장간 십신 매핑
├── sixty_jiazi.json                 # 60갑자 속성
├── lifecycle_stages.json            # 12운성 (미통합)
├── localization_ko_v1.json          # 한국어 라벨
├── localization_en_v1.json          # 영어 라벨 (미통합)
├── luck_pillars_policy.json         # 대운 정책
├── daystem_yinyang.json             # 일간 음양
├── elemental_projection_policy.json # 오행 투영
└── elements_distribution_criteria.json # 오행 분포
```

### 6.2 정책 로딩 방법

**파일 기반 로딩:**
```python
import json

with open("saju_codex_batch_all_v2_6_signed/policies/strength_policy_v2.json") as f:
    strength_policy = json.load(f)
```

**RFC-8785 검증:**
```python
from canonicaljson import encode_canonical_json
import hashlib

# 서명 제거 후 canonical 직렬화
policy_copy = {k: v for k, v in strength_policy.items() if k != "signature"}
canonical = encode_canonical_json(policy_copy)
computed = hashlib.sha256(canonical).hexdigest()

# 서명 검증
assert computed == strength_policy["signature"]["sha256"]
```

### 6.3 주요 정책 구조

**strength_policy_v2.json:**
```json
{
  "version": "2.0",
  "month_state_scores": {
    "旺": 30, "相": 15, "休": 0, "囚": -15, "死": -30
  },
  "branch_root_scores": {
    "strong": 25, "medium": 15, "weak": 5
  },
  "stem_visible_scores": {
    "比劫透": 15, "印透": 10, "其他": 0
  },
  "buckets": [
    {"code": "극신강", "min": 80, "max": 100},
    {"code": "신강", "min": 60, "max": 79},
    {"code": "중화", "min": 40, "max": 59},
    {"code": "신약", "min": 20, "max": 39},
    {"code": "극신약", "min": 0, "max": 19}
  ],
  "signature": {
    "sha256": "..."
  }
}
```

**relation_policy.json:**
```json
{
  "version": "2.0",
  "heavenly": {
    "combine": [
      {"pair": ["甲", "己"], "result": "土", "priority": 1},
      {"pair": ["乙", "庚"], "result": "金", "priority": 1}
    ]
  },
  "earth": {
    "he6": [
      {"pair": ["子", "丑"], "result": "土"},
      {"pair": ["辰", "酉"], "result": "金"}
    ],
    "chong": [
      {"pair": ["子", "午"], "severity": "high"},
      {"pair": ["巳", "亥"], "severity": "high"}
    ]
  },
  "signature": {
    "sha256": "..."
  }
}
```

---

## 7. 모델 라우팅 정책

### 7.1 Light 채팅 (무료/일 3회)

**우선순위:**
1. **Qwen Flash** (기본, 속도 최적화)
2. **DeepSeek-Chat** (폴백 1차)
3. **Gemini 2.5 Pro** (폴백 2차, 최종)

**사용 사례:**
- 간단한 질문 (예: "내 일간이 뭐야?")
- 오늘의 운세 요약
- 빠른 해석 (5초 이내 응답)

### 7.2 Deep 채팅 (토큰 소비)

**우선순위:**
1. **Gemini 2.5 Pro** (기본)
2. **GPT-5** (백스탑, 고품질 요청)

**사용 사례:**
- 심층 상담 (예: "내 격국 성립 조건 상세 설명")
- 대운·연운 해석
- 용신·조후 전략 분석
- 장문 코칭 (500+ 토큰)

**토큰 소비:**
- Deep 1회 = 1토큰
- 리워디드 광고 1회 = 2토큰 (1시간 쿨다운, 일 2회 한도)

### 7.3 보고서 자동 생성

**엔진:** Gemini 2.5 Pro

**사용 사례:**
- POST /report/saju → PDF 자동 생성
- 템플릿 기반 문장화
- 30일 캐시

### 7.4 프리미엄 수작업 보고서

**엔진:** GPT-5 Pro

**사용 사례:**
- 전문가 검수 보고서
- 유료 심층 상담
- 커스텀 해석

---

## 8. 다음 액션 로드맵

### Phase 1: API 스펙 완성 (우선순위: 높음)

- [x] `10_api-specs/01_openapi_lite_prompt.md` → API_SPECIFICATION_v1.0.md
- [x] `10_api-specs/02_report_schema_prompt.md` → SAJU_REPORT_SCHEMA_v1.0.md
- [ ] `10_api-specs/03_chat_send_spec_prompt.md` → /chat/send 스펙 생성
  - 상태 머신 (idle → typing → streaming → done)
  - 카드 생성 로직 (오행/용신/강약/대운/연월운)
  - LLM 라우팅 (Light/Deep)
  - 토큰 소비 플로우

### Phase 2: 정책 엔진 확장 (우선순위: 중간)

- [ ] `20_policy-engines/twelve_stage_void_yuanjin_combo_prompt.md`
  - TwelveStageCalculator (12운성: 장생~양)
  - VoidCalculator (공망: 일간 기준 공망 지지)
  - YuanjinDetector (원진: relation_policy.json 확장)
  - CombinationElement (조합오행: 합화 결과)
- [ ] `20_policy-engines/annual_monthly_luck_prompt.md`
  - AnnualLuckCalculator (연운: 년주 + 대운 조합)
  - MonthlyLuckCalculator (월운: 월주 + 길흉일 계산)
- [ ] `20_policy-engines/relation_policy_extension_prompt.md`
  - 원진(yuanjin) 규칙 추가
  - 조합오행(combination_element) 변환 규칙

### Phase 3: LLM 통합 (우선순위: 높음)

- [ ] `30_llm/llm_templates_5pack_prompt.md`
  - 오행 해석 템플릿 (木火土金水 과부족)
  - 용신 전략 템플릿 (扶抑/調候/通關/專旺/從格)
  - 강약 코칭 템플릿 (극신강~극신약)
  - 대운 해석 템플릿 (시작 나이, 순역, 기둥별 영향)
  - 연운·월운 템플릿 (길일·흉일, 주의사항)
- [ ] `30_llm/llm_guard_v1_prompt.md`
  - LLM_GUARD_V1_ANALYSIS_AND_PLAN.md 기반 구현
  - 6개 규칙 패밀리 (DETERMINISM, TRACE_INTEGRITY, EVIDENCE_BOUND, POLICY_BOUND, KO_FIRST_LABELS, HARM_GUARD)
  - Pre-generation / Post-generation 검증
  - Verdict: allow / block / revise
- [ ] `30_llm/model_routing_policy_prompt.md`
  - Light/Deep 라우팅 정책
  - 폴백 체인 (Qwen → DeepSeek → Gemini)
  - 백스탑 (GPT-5)
  - 레이트 리밋 / 에러 핸들링

### Phase 4: 토큰/권한/광고 (우선순위: 중간)

- [ ] `40_tokens_entitlements_ads/tokens_entitlements_ssv_prompt.md`
  - Entitlements 스키마 (plan, storage_limit, light_daily_left, deep_tokens)
  - Token consume 플로우 (Idempotency-Key)
  - Rewarded ads SSV 검증 (Google AdMob)
  - Cooldown/Cap 정책 (1시간 쿨다운, 일 2회 한도)

### Phase 5: 캐시/스토리지/QA (우선순위: 낮음)

- [ ] `50_cache_storage_qc/cache_storage_idempotency_prompt.md`
  - 캐시 전략 (annual 365일, monthly 30일, report 30일)
  - RFC-8785 서명 기반 무결성 검증
  - Idempotency-Key 처리 (POST 중복 방지)
- [ ] `50_cache_storage_qc/qa_perf_release_plan_prompt.md`
  - QA 체크리스트 (단위/통합/E2E)
  - 성능 벤치마크 (P50/P95/P99 응답 시간)
  - 릴리스 계획 (Canary → Staging → Production)

### Phase 6: 통합 마스터 (우선순위: 낮음)

- [ ] `00_master/Saju_Chat_Report_Integrated_Master_Prompt_v1.md`
  - 전체 시스템 통합 프롬프트
  - 모든 엔진/정책/LLM 조율
  - E2E 플로우 검증

---

## 9. 빠른 문제 해결

### 9.1 자주 발생하는 이슈

**Issue 1: 대운 시작 나이가 모든 사주에서 동일**
- **원인:** engine.py:430 하드코딩 `datetime(1992, 7, 15, 23, 40)`
- **해결:** ✅ 2025-10-07 수정 완료 (options.birth_dt 사용)
- **파일:** services/analysis-service/app/core/engine.py:481-493

**Issue 2: ClimateEvaluator 구현됨, 사용 안 됨**
- **원인:** engine.py에 통합 안 됨
- **해결:** 🟡 대기 중 (Phase 2)
- **파일:** services/analysis-service/app/core/climate.py

**Issue 3: 시간 미상(unknown_hour) 처리**
- **원인:** pillars.hour = null 처리 필요
- **해결:** ✅ SAJU_REPORT_SCHEMA_v1.0.md에 스키마 정의 완료
- **샘플:** 샘플 B 참조

**Issue 4: 원진(yuanjin) 미구현**
- **원인:** RelationTransformer에 원진 로직 없음
- **해결:** 🟡 대기 중 (Phase 2: relation_policy_extension_prompt.md)
- **정책:** relation_policy.json 확장 필요

**Issue 5: 12운성(lifecycle_stages) 미구현**
- **원인:** lifecycle_stages.json 존재, 엔진 없음
- **해결:** 🟡 대기 중 (Phase 2: twelve_stage_void_yuanjin_combo_prompt.md)
- **정책:** lifecycle_stages.json → TwelveStageCalculator

### 9.2 Cross-Service Import 문제

**Issue:** services/pillars-service가 scripts/에서 import
- **위치:** services/pillars-service/app/core/engine.py
- **원인:** Python 모듈명에 하이픈 불가 (tz-time-service)
- **임시 해결:** 스텁 클래스 사용 (evidence.py에 문서화)
- **영구 해결:** 🟡 services/common/ 폴더로 공통 클래스 추출

**관련 파일:**
- services/pillars-service/app/core/evidence.py:17-77 (스텁 문서)
- FIX_COMPLETE_REPORT.md (교차 서비스 임포트 섹션)

### 9.3 테스트 실행

**전체 테스트:**
```bash
PYTHONPATH=".:services/analysis-service:services/pillars-service:services/common" \
  .venv/bin/pytest services/analysis-service/tests/ -v
```

**특정 테스트:**
```bash
../../.venv/bin/pytest tests/test_strength_policy_v2.py -v
../../.venv/bin/pytest tests/test_korean_enricher.py -v
../../.venv/bin/pytest tests/test_llm_guard.py -v  # (미구현)
```

**커버리지:**
- analysis-service: 47/47 passing ✅
- pillars-service: 25/25 passing ✅
- astro-service: 12/12 passing ✅
- tz-time-service: 8/8 passing ✅

---

## 10. 체크리스트 (PR 머지 전)

### 10.1 문서 체크리스트

- [ ] 제목/버전/날짜(KST) 포함
- [ ] ROLE/GOAL/OUTPUT ORDER 정의
- [ ] JSON Schema draft-2020-12 선언
- [ ] $defs 재사용 컴포넌트 분리
- [ ] description 필드 모든 속성에 포함
- [ ] 샘플 JSON 2건 이상 (정상 + 엣지)
- [ ] signatures.sha256 포함
- [ ] *_ko 라벨 병행 (KO-first)
- [ ] enum/pattern 완전성 검증
- [ ] 검증 힌트 섹션 포함

### 10.2 코드 체크리스트

- [ ] Pydantic 모델 정의
- [ ] 정책 파일 로딩 구현
- [ ] RFC-8785 서명 검증
- [ ] 단위 테스트 작성 (coverage ≥80%)
- [ ] 통합 테스트 작성
- [ ] Type hints 완전성
- [ ] Docstring 포함
- [ ] 에러 핸들링 (try/except)
- [ ] 로깅 추가
- [ ] Pre-commit hooks 통과

### 10.3 정책 체크리스트

- [ ] version 필드 포함
- [ ] signature.sha256 포함
- [ ] JSON Schema 스키마 파일 존재
- [ ] 스키마 검증 통과
- [ ] 샘플 데이터 3건 이상
- [ ] 엔진 통합 완료
- [ ] 테스트 케이스 작성
- [ ] 문서화 (README/claude.md)

---

## 11. 중요 문서 링크

### 11.1 기술 문서

- **API_SPECIFICATION_v1.0.md** - 9개 엔드포인트 OpenAPI-lite 사양
- **SAJU_REPORT_SCHEMA_v1.0.md** - POST /report/saju JSON Schema + 샘플
- **LLM_GUARD_V1_ANALYSIS_AND_PLAN.md** - LLM Guard 구현 계획 (730줄)
- **IMPLEMENTED_ENGINES_AND_FEATURES.md** - 엔진 인벤토리 (500줄)
- **FIX_COMPLETE_REPORT.md** - 2025-10-07 버그 수정 보고서
- **AUDIT_VERIFICATION_REPORT.md** - 2025-10-04 감사 검증

### 11.2 정책 문서

- **saju_codex_batch_all_v2_6_signed/policies/** - 14개 정책 파일
- **saju_codex_batch_all_v2_6_signed/schemas/** - 10개 스키마 파일

### 11.3 핸드오버 문서

- **DEVELOPMENT_HANDOFF.md** - 개발 핸드오버
- **LIFECYCLE_HANDOFF_ANALYSIS.md** - 생애주기 핸드오버
- **MISSING_POLICIES_AND_INTEGRATIONS_HANDOVER.md** - 미구현 정책 핸드오버

### 11.4 분석 문서

- **ENGINE_RETIREMENT_ANALYSIS.md** - 엔진 퇴직 분석 (orphaned engines)
- **FEATURE_GAP_ANALYSIS.md** - 기능 갭 분석
- **CODEX_AND_CODEBASE_SCAN_REPORT.md** - 코드베이스 스캔 보고서

---

## 12. 버전 관리

**현재 버전:** v1.0 (2025-10-07 KST)

**변경 이력:**
- **v1.0** (2025-10-07): 초기 생성
  - 아키텍처 플로우 정의
  - 폴더 구조 매핑
  - 구현 상태 매트릭스
  - 공통 규약 정의
  - 엔진/정책 빠른 참조
  - 다음 액션 로드맵 (6개 Phase)

**다음 업데이트 예정:**
- /chat/send 스펙 완성 시 → v1.1
- 12운성/공망/원진 통합 시 → v1.2
- LLM Guard v1.0 구현 시 → v1.3
- 토큰/권한 시스템 구현 시 → v1.4

---

## 13. 긴급 참조

### 13.1 엔진 위치

| 엔진                  | 파일 경로                                          |
|-----------------------|----------------------------------------------------|
| calculate_four_pillars | scripts/calculate_pillars_traditional.py          |
| AnalysisEngine        | services/analysis-service/app/core/engine.py       |
| TenGodsCalculator     | services/analysis-service/app/core/engine.py:102   |
| RelationTransformer   | services/analysis-service/app/core/relations.py    |
| StrengthEvaluator     | services/analysis-service/app/core/strength.py     |
| LuckCalculator        | services/analysis-service/app/core/luck.py         |
| KoreanLabelEnricher   | services/analysis-service/app/core/korean_enricher.py |
| WangStateMapper       | services/analysis-service/app/core/strength.py:18  |

### 13.2 정책 파일 로딩

**StrengthEvaluator:**
```python
policy = StrengthEvaluator._load_policy(
    "saju_codex_batch_all_v2_6_signed/policies/strength_policy_v2.json"
)
```

**RelationTransformer:**
```python
policy = RelationTransformer._load_policy(
    "saju_codex_batch_all_v2_6_signed/policies/relation_policy.json"
)
```

**KoreanLabelEnricher:**
```python
enricher = KoreanLabelEnricher.from_files(
    localization_path="saju_codex_batch_all_v2_6_signed/policies/localization_ko_v1.json",
    sixty_jiazi_path="saju_codex_batch_all_v2_6_signed/policies/sixty_jiazi.json",
    lifecycle_path="saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json"
)
```

### 13.3 CHONG_PAIRS (충 관계)

```python
CHONG_PAIRS = {
    ("子", "午"), ("午", "子"),
    ("丑", "未"), ("未", "丑"),
    ("寅", "申"), ("申", "寅"),
    ("卯", "酉"), ("酉", "卯"),
    ("辰", "戌"), ("戌", "辰"),
    ("巳", "亥"), ("亥", "巳")
}
```

### 13.4 STEM_TO_ELEMENT / ELEMENT_GENERATES

```python
STEM_TO_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

ELEMENT_GENERATES = {
    "木": "火",  # 木生火
    "火": "土",  # 火生土
    "土": "金",  # 土生金
    "金": "水",  # 金生水
    "水": "木"   # 水生木
}
```

---

## 끝

이 문서는 Claude가 매 세션마다 읽어야 할 프로젝트 중앙 참조 문서입니다.

**갱신 규칙:**
- 주요 구현 완료 시 즉시 갱신
- Phase 완료 시 버전 업데이트
- 새 정책/엔진 추가 시 섹션 추가

**문의:**
- GitHub Issues: https://github.com/[your-repo]/issues
- Core Architects: 백엔드/정책/데이터 팀

**마지막 검증:** 2025-10-07 KST
