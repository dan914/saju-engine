# 📘 실행 프롬프트 — API 명세서(OpenAPI-lite) 전용 v1.0

**ROLE**
너는 KO-first 백엔드 아키텍트다. **설명 금지**, **결정적 사양만** 출력한다.

**GOAL**
아래 9개 엔드포인트의 **OpenAPI-lite 명세**를 한 문서로 산출한다. 각 엔드포인트마다: 요청/응답 JSON 스키마(draft-2020-12), 헤더·보안, 상태코드, 정상/에러 예시를 포함한다.

**ENDPOINTS (고정)**
- `POST /api/v1/report/saju`
- `POST /api/v1/chat/send`
- `POST /api/v1/luck/annual`
- `POST /api/v1/luck/monthly`
- `POST /api/v1/tokens/reward`   *(리워디드 광고 SSV)*
- `POST /api/v1/tokens/consume`
- `GET  /api/v1/entitlements`
- `POST /api/v1/report/pdf`
- `POST /api/v1/profiles`

**CONTEXT (고정 사실)**
- 서비스 체인: tz-time → astro → pillars → analysis → luck(연/월) → llm-polish → LLMGuard → Gateway
- 정책/데이터 파일: `strength_policy_v2.json`, `relation_policy.json`, `shensha_v2_policy.json`, `gyeokguk_policy.json`, `yongshin_policy.json`, `branch_tengods_policy.json`, `sixty_jiazi.json`, `localization_ko_v1.json`
- 신규 모듈(명세 참조만): `TwelveStageCalculator`, `VoidCalculator`, `YuanjinDetector`, `CombinationElementTransformer`, `AnnualLuckCalculator`, `MonthlyLuckCalculator`

---

## OUTPUT FORMAT (반드시 준수)

### 1) 문서 헤더
- 제목, 버전, 날짜(KST), 베이스 URL(placeholder), 인증 방식(Bearer)

### 2) 글로벌 규칙
- **보안**: `Authorization: Bearer <token>`
- **요청 헤더**: `X-Request-Id`(필수), `Idempotency-Key`(멱등 필요한 POST에 권장)
- **응답 헤더**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **에러 모델(공통)**:
  ```json
  { "error_code": "E_BAD_REQUEST", "message": "KO 설명", "trace_id": "…", "hint": "…" }
  ```
- **JSON 서명 규칙**: 모든 응답 예시에 `signatures.sha256`(RFC-8785 canonical JSON 기준) 필드 포함

### 3) 엔드포인트별 스펙(각각 제공)
- 요약/설명(짧게)
- 요청 스키마: JSON Schema draft-2020-12 (타입/enum/format/min/max/required)
- 응답 스키마: 성공/에러(공통 에러 스키마 참조)
- 상태코드: 200/201/400/401/403/404/409/422/429/500 중 해당 값
- 헤더: 요청/응답에 요구되는 헤더 명시
- 예시: 정상 1개, 에러 1개(에러는 한국어 message와 표준 error_code)
- 비고: 캐시/TTL, 멱등, 레이트리밋, 페이징(해당 시)

### 4) 공통 컴포넌트(스키마 섹션)
- Profile
- ReportSajuResponseSummary
- ChatResponseSummary
- LuckAnnual
- LuckMonthly
- Entitlements
- TokensRewardRequest/Response
- TokensConsumeRequest/Response
- PdfJob
- 에러코드 테이블: `E_BAD_REQUEST`, `E_UNAUTHORIZED`, `E_FORBIDDEN`, `E_NOT_FOUND`, `E_CONFLICT`, `E_RATE_LIMIT`, `E_UNPROCESSABLE`, `E_SERVER`

### 5) 부록
- 필드 제약 요약:
  - `birth_dt_local` ISO 8601 date-time
  - `calendar_type` ∈ {solar, lunar}
  - `zi_hour_mode` ∈ {split_23, default}
  - IANA TZ 패턴: `^[A-Za-z]+/[A-Za-z_]+(?:/[A-Za-z_]+)?$`
- 샘플 값 메모: 최소 1개 예시에 `unknown_hour:true`, `zi_hour_mode:"split_23"`, `regional_correction_minutes:-32` 포함

---

## SCHEMA HINTS (지켜라)

- `/api/v1/report/saju` 응답 최상위 키: `meta`, `time`, `pillars`, `analysis`, `localization`, `evidence`, (옵션) `entitlements`, (옵션) `ads_suggest`
- `/api/v1/chat/send` 응답: `cards[]`, `llm_text`, `consumed{tokens,depth}`, `upsell{show,reason,options[]}`, `next_cta[]`
- `/api/v1/tokens/reward`: `idempotency_key`, `network`, `receipt`, `cooldown_sec`, `daily_cap`
- `/api/v1/entitlements`: `plan`, `storage_limit`, `stored`, `light_daily_left`, `deep_tokens` 등
- `/api/v1/luck/*` 응답 메타에 `cache_ttl_sec` 표기 권장(연 365d, 월 30d)

---

## STYLE

- KO-first, 간결/정확/중립
- 임의 가정 최소화. 필요한 기본값/enum은 합리적으로 지정
- 표/코드블록(JSON Schema) 혼합 표현

---

## ACCEPTANCE CRITERIA

- 9개 엔드포인트 모두 요청/응답 스키마 + 정상/에러 예시 + 상태코드/헤더 포함
- 공통 에러 모델/코드표/보안/헤더/서명 규칙이 문서 상단과 컴포넌트에 정의
- `/report/saju`와 `/chat/send`는 샘플 JSON이 120~200줄 내로 포함
- 최소 1개 예시에 `unknown_hour:true`, `zi_hour_mode:"split_23"`, `regional_correction_minutes:-32` 등장
- 문서 전체를 한 번에 복사-저장 가능한 단일 명세로 출력
