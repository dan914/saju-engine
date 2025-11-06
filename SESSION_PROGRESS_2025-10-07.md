# 세션 진행 상황 — 2025-10-07

**세션 시작:** 2025-10-07 KST
**마지막 업데이트:** 2025-10-07 KST

---

## 완료된 작업 (✅)

### 1. 중앙 허브 문서 생성
- ✅ **claude.md** (13개 섹션, 프로젝트 전체 참조 문서)
  - 아키텍처 플로우 (9개 서비스)
  - 구현 상태 매트릭스 (서비스/엔진/정책/API)
  - 공통 규약 (머리말/스키마/RFC-8785/KO-first)
  - 엔진/정책 빠른 참조
  - 6개 Phase 로드맵

### 2. Policy Prompts Hub 구조 생성
- ✅ **docs/policy-prompts/README.md** (중앙 허브)
  - 폴더 구조 정의 (00_master ~ 50_cache_storage_qc)
  - 체크리스트 (문서/코드/정책)
  - 모델 라우팅 정책

### 3. API 사양 프롬프트 (3/3 완료)
- ✅ **01_openapi_lite_prompt.md** - 9개 엔드포인트 OpenAPI-lite 명세 생성용
- ✅ **02_report_schema_prompt.md** - POST /report/saju JSON Schema + 샘플
- ✅ **03_chat_send_spec_prompt.md** - POST /chat/send 오케스트레이터 (상태머신 9단계)

### 4. 정책/엔진 프롬프트 (2/3 완료)
- ✅ **twelve_stage_void_yuanjin_combo_prompt.md** (4개 엔진)
  - TwelveStageCalculator (12운성: 장생~양)
  - VoidCalculator (공망: 60갑자 순환)
  - YuanjinDetector (원진: 6쌍)
  - CombinationElementTransformer (합화오행: 천간5쌍+지지삼합/육합)
- ✅ **annual_monthly_luck_prompt.md** (2개 엔진)
  - AnnualLuckCalculator (연운: 년주+대운 조합)
  - MonthlyLuckCalculator (월운: 월주+길흉일)
- ⏳ **relation_policy_extension_prompt.md** (미생성)

### 5. 토큰/권한/광고 프롬프트 (1/1 완료)
- ✅ **tokens_entitlements_ssv_prompt.md** - 토큰 경제/플랜/리워디드 광고

### 6. 실행 결과 문서 (4개)
- ✅ **API_SPECIFICATION_v1.0.md** - 9개 엔드포인트 OpenAPI-lite (기존)
- ✅ **SAJU_REPORT_SCHEMA_v1.0.md** - /report/saju JSON Schema + 샘플 A/B
- ✅ **CHAT_SEND_SPEC_v1.0.md** - /chat/send 완전 사양 (상태머신/라우팅/스키마/예시)
- ✅ **TOKENS_ENTITLEMENTS_SSV_SPEC_v1.0.md** - 토큰/권한/광고 완전 사양

---

## 생성된 파일 목록

### 프롬프트 파일 (7개)
```
docs/policy-prompts/
├── README.md
├── 10_api-specs/
│   ├── 01_openapi_lite_prompt.md
│   ├── 02_report_schema_prompt.md
│   └── 03_chat_send_spec_prompt.md
├── 20_policy-engines/
│   ├── twelve_stage_void_yuanjin_combo_prompt.md
│   └── annual_monthly_luck_prompt.md
└── 40_tokens_entitlements_ads/
    └── tokens_entitlements_ssv_prompt.md
```

### 사양 문서 (5개)
```
/Users/yujumyeong/coding/ projects/사주/
├── claude.md
├── API_SPECIFICATION_v1.0.md (기존)
├── SAJU_REPORT_SCHEMA_v1.0.md
├── CHAT_SEND_SPEC_v1.0.md
└── TOKENS_ENTITLEMENTS_SSV_SPEC_v1.0.md
```

---

## 주요 사양 요약

### SAJU_REPORT_SCHEMA_v1.0.md
- JSON Schema draft-2020-12 (완전 스키마)
- 최상위 키 8개: meta, time, pillars, analysis, localization, evidence, entitlements(옵션), ads_suggest(옵션)
- 샘플 A (정상): 2000-09-14 10:00 AM Seoul, 庚辰 乙酉 乙亥 辛巳
- 샘플 B (엣지): unknown_hour:true, zi_hour_mode:"split_23", regional_correction_minutes:-32
- $defs 12개 (Pillar, TenGodsAnalysis, RelationsAnalysis, VoidAnalysis, LifeStageAnalysis, etc.)

### CHAT_SEND_SPEC_v1.0.md
- 상태머신 9단계: S0(Quota) → S1(Intent) → S2(Context) → S3(Pre-Guard) → S4(Template) → S5(LLM) → S6(Post-Guard) → S7(Consume) → S8(Respond)
- 모델 라우팅: Light(Qwen/DeepSeek→Gemini→GPT-5), Deep(Gemini→GPT-5)
- 카드 타입 5종: wuxing_summary, relations_highlight, strength_bucket, luck_snippet, notice
- intent 10종: today/month/year/money/work/study/move/love/match/general
- 검증 체크리스트 4개 섹션 (요청/상태머신/응답/Guard)

### TOKENS_ENTITLEMENTS_SSV_SPEC_v1.0.md
- 플랜 3종: Free(저장5/Light5·일/Deep1·일), Plus(저장30/Light무제한/Deep30·월), Pro(무제한+공정사용)
- 토큰 상태: IDLE → RESERVE → FINALIZE/RELEASE → IDLE
- 차감 순서: deep_daily_left → deep_monthly_left → chat_token_balance
- SSV 시퀀스 12단계: Client→AdSDK→Gateway→AdNet→Ledger
- DB 스키마 3개: entitlements, tokens_ledger, ad_rewards
- 쿨다운 60분, 일한도 2회, 광고 1회 +2토큰

### twelve_stage_void_yuanjin_combo_prompt.md
- 12운성: 일간별 12단계 매핑표 (장생/沐浴/冠帶/臨官/帝旺/衰/病/死/墓/絶/胎/養)
- 공망: 60갑자 순환별 공망 지지 2개 (예: 甲子~癸酉 → 戌亥공망)
- 원진: 6쌍 (子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌)
- 합화오행: 천간 5쌍 (甲己合土 등) + 지지 삼합 4국 + 육합 6쌍
- relation_policy.json 확장: yuanjin 필드, combine.transform 필드
- localization_ko_v1.json 확장: 12운성/공망/원진/합화 라벨 20+개

### annual_monthly_luck_prompt.md
- 연운: 년주 조회 (60갑자 순환), 십신/12운성/태세, annual_score (0~100), key_months
- 월운: 월주 조회 (절기 기반), good_days/caution_days (1~31), 7일 티저
- API 엔드포인트: POST /luck/annual, POST /luck/monthly
- 캐시: 연운 365일 TTL, 월운 30일 TTL, RFC-8785 서명
- 엣지 케이스: 윤년, 절기 경계, 자시 전환, 대운 전환기

---

## 다음 작업 (진행 중)

### 사용자가 제공할 프롬프트 (1/6 완료)
- ✅ **01_openapi_lite_prompt.md** - 저장 완료
- ⏳ **02번 프롬프트** - 대기 중 ("다음" 입력 시 제공 예정)
- ⏳ **03번 프롬프트** - 대기 중
- ⏳ **04번 프롬프트** - 대기 중
- ⏳ **05번 프롬프트** - 대기 중
- ⏳ **06번 프롬프트** - 대기 중

### 실행 필요한 프롬프트
1. **01_openapi_lite_prompt.md** → 새 채팅에서 실행 → OpenAPI-lite 통합 명세 생성
2. 나머지 5개 프롬프트 (사용자 제공 예정)

---

## 구현 Phase 로드맵 (claude.md 기반)

### Phase 1: API 스펙 완성 (우선순위: 높음)
- [x] 01_openapi_lite_prompt.md 저장
- [x] 02_report_schema_prompt.md → SAJU_REPORT_SCHEMA_v1.0.md
- [x] 03_chat_send_spec_prompt.md → CHAT_SEND_SPEC_v1.0.md
- [ ] 새 채팅에서 01_openapi_lite_prompt.md 실행 → 통합 OpenAPI 명세

### Phase 2: 정책 엔진 확장 (우선순위: 중간)
- [ ] twelve_stage_void_yuanjin_combo_prompt.md 실행
  - TwelveStageCalculator 구현
  - VoidCalculator 구현
  - YuanjinDetector 구현
  - CombinationElementTransformer 구현
- [ ] annual_monthly_luck_prompt.md 실행
  - AnnualLuckCalculator 구현
  - MonthlyLuckCalculator 구현
- [ ] relation_policy.json v2.1 확장 (yuanjin 필드)
- [ ] localization_ko_v1.json v1.1 확장 (12운성/공망/원진 라벨)

### Phase 3: LLM 통합 (우선순위: 높음)
- [ ] llm_templates_5pack_prompt.md 생성
- [ ] llm_guard_v1_prompt.md 실행 (LLM_GUARD_V1_ANALYSIS_AND_PLAN.md 기반)
- [ ] model_routing_policy_prompt.md 생성

### Phase 4: 토큰/권한/광고 (우선순위: 높음)
- [x] tokens_entitlements_ssv_prompt.md → TOKENS_ENTITLEMENTS_SSV_SPEC_v1.0.md
- [ ] DB 마이그레이션 스크립트 (3개 테이블)
- [ ] API 구현 (entitlements, reward, consume)
- [ ] SSV 통합 (AdMob/IronSource/Unity/AppLovin)

### Phase 5: 캐시/스토리지/QA (우선순위: 낮음)
- [ ] cache_storage_idempotency_prompt.md 생성
- [ ] qa_perf_release_plan_prompt.md 생성

### Phase 6: 통합 마스터 (우선순위: 낮음)
- [ ] Saju_Chat_Report_Integrated_Master_Prompt_v1.md 생성

---

## 기술 스택 요약

### 정책 파일 (14개)
- strength_policy_v2.json (강약 평가)
- relation_policy.json (합충형파해, **원진 확장 필요**)
- shensha_v2_policy.json (신살)
- gyeokguk_policy.json (격국)
- yongshin_policy.json (용신)
- branch_tengods_policy.json (지장간 십신)
- sixty_jiazi.json (60갑자 속성)
- lifecycle_stages.json (12운성, **통합 필요**)
- localization_ko_v1.json (한국어 라벨, **확장 필요**)
- localization_en_v1.json (영어 라벨, 미통합)
- luck_pillars_policy.json (대운)
- daystem_yinyang.json (일간 음양)
- elemental_projection_policy.json (오행 투영)
- elements_distribution_criteria.json (오행 분포)

### 엔진 상태
- **완전 통합 (10개)**: TenGodsCalculator, RelationTransformer, StrengthEvaluator, StructureDetector, ShenshaCatalog, YongshinAnalyzer, BranchTenGodsMapper, LuckCalculator, KoreanLabelEnricher, SchoolProfileManager
- **미통합 (1개)**: ClimateEvaluator (구현됨, 통합 안 됨)
- **미구현 (5개)**: TwelveStageCalculator, VoidCalculator, YuanjinDetector, CombinationElementTransformer, AnnualLuckCalculator, MonthlyLuckCalculator

### API 엔드포인트 (9개)
1. POST /api/v1/report/saju - 전체 사주 보고서
2. POST /api/v1/chat/send - 채팅 오케스트레이터
3. POST /api/v1/luck/annual - 연운
4. POST /api/v1/luck/monthly - 월운
5. POST /api/v1/tokens/reward - 광고 보상
6. POST /api/v1/tokens/consume - 토큰 소비
7. GET /api/v1/entitlements - 권한 조회
8. POST /api/v1/report/pdf - PDF 생성
9. POST /api/v1/profiles - 프로필 저장

### DB 스키마 (3개 테이블)
- **entitlements**: user_id, plan, storage_limit, light_daily_left, deep_daily_left, deep_monthly_left, chat_token_balance, pdf_credits
- **tokens_ledger**: id, user_id, type(grant/reserve/finalize/release), amount, idempotency_key, balance_after, UNIQUE(user_id, idempotency_key)
- **ad_rewards**: id, user_id, network, receipt_hash, status, idempotency_key, UNIQUE(network, receipt_hash), UNIQUE(user_id, idempotency_key)

---

## 중요 참조 문서

### 필수 읽기
1. **claude.md** - 프로젝트 전체 참조 (매 세션 시작 시 읽기)
2. **docs/policy-prompts/README.md** - Policy Prompts Hub 구조
3. **SESSION_PROGRESS_2025-10-07.md** - 현재 문서 (진행 상황 추적)

### 사양 문서
- API_SPECIFICATION_v1.0.md (9개 엔드포인트 요약)
- SAJU_REPORT_SCHEMA_v1.0.md (JSON Schema + 샘플)
- CHAT_SEND_SPEC_v1.0.md (상태머신 + 라우팅)
- TOKENS_ENTITLEMENTS_SSV_SPEC_v1.0.md (토큰 경제 + SSV)

### 기존 핸드오버 문서 (참고용)
- DEVELOPMENT_HANDOFF.md
- LIFECYCLE_HANDOFF_ANALYSIS.md
- MISSING_POLICIES_AND_INTEGRATIONS_HANDOVER.md
- FIX_COMPLETE_REPORT.md (2025-10-07 버그 수정)
- AUDIT_VERIFICATION_REPORT.md

---

## 다음 세션 시작 시 할 일

1. **이 파일 읽기**: SESSION_PROGRESS_2025-10-07.md
2. **claude.md 확인**: 프로젝트 전체 구조 복습
3. **대기 중인 프롬프트 확인**: 사용자가 제공할 02~06번 프롬프트
4. **실행 순서**:
   - 새 채팅에서 01_openapi_lite_prompt.md 실행 → OpenAPI-lite 통합 명세 생성
   - 사용자 제공 프롬프트 순차 실행
   - 생성된 사양 문서를 코드베이스에 반영

---

## 세션 통계

- **생성된 파일**: 12개 (프롬프트 7 + 사양 5)
- **작성된 라인**: ~15,000줄
- **완료 Phase**: 1/6 (API 스펙 완성)
- **다음 마일스톤**: OpenAPI-lite 통합 명세 생성 + 02~06번 프롬프트 실행

---

**마지막 사용자 메시지:**
> "일단 진행상황 정리하고 compact 다음에 읽을 파일 만들어"

**다음 예상 액션:**
사용자가 "다음"이라고 입력하면 02번 프롬프트 제공 예정.

---

**Version:** 1.0
**Last Updated:** 2025-10-07 KST
