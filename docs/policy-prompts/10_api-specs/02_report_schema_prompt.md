# 📘 실행 프롬프트 — `/report/saju` JSON Schema + 샘플 전용 v1.0

**버전**: v1.0
**날짜**: 2025-10-07 KST
**경로 권장**: `docs/policy-prompts/10_api-specs/02_report_schema_prompt.md`

---

## ROLE
너는 KO-first 스키마 엔지니어다. 설명 대신 **결정적 산출물**만 출력한다.

## GOAL
`POST /api/v1/report/saju`의 **정식 JSON Schema (draft-2020-12)**와 **샘플 응답 2건**을 산출한다. 스키마는 **유효성 검증 가능**해야 하며, 필드 설명(`description`)과 제약을 포함한다.

## CONTEXT (고정 사실)
- 상위 키: `meta`, `time`, `pillars`, `analysis`, `localization`, `evidence`, *(옵션)* `entitlements`, *(옵션)* `ads_suggest`.
- 기존 정책/데이터: `strength_policy_v2.json`, `relation_policy.json`, `shensha_v2_policy.json`, `gyeokguk_policy.json`, `yongshin_policy.json`, `branch_tengods_policy.json`, `sixty_jiazi.json`, `localization_ko_v1.json`.
- KO-first 라벨 필요: 가능한 곳에 `*_ko` 보조 필드 포함.
- RFC-8785 canonical JSON + `signatures.sha256` 예시 필드 포함.

## MUST INCLUDE (필수 스키마 세부)
1) **`meta`**
   - `name`(string), `gender`(enum: `male`/`female`/`other`), `school_profile`(string), `signatures.sha256`(string, pattern SHA-256 hex).
2) **`time`**
   - `timezone`(IANA, pattern), `dst`(boolean), `utc`(ISO8601 `date-time`),
   - `lmt`(string `date-time`), `regional_correction_minutes`(integer, -180..+180),
   - `solar_time`(string `date-time`), `evidence`(object).
3) **`pillars`**
   - `year|month|day|hour` → `{ stem, branch, sexagenary }` (모두 string; 10간/12지/60갑자 유효성 enum 또는 패턴),
   - `meta.zi_hour_mode`(enum: `default`/`split_23`).
4) **`analysis`**
   - `ten_gods.by_pillar.{year,month,day,hour}.{heavenly,earth}`(string enum 10개),
   - `ten_gods.stats.percent`(object of number 0..100),
   - `relations.{heavenly,earth}.{combine,clash,xing,po,hai,he6,sanhe,directional,yuanjin}`(array of arrays with items string),
   - `void.kong_wang`(array of branch strings),
   - `life_stage.by_pillar.*`(enum: 장생~양 12단계),
   - `shensha.summary[]`(string), `shensha.by_pillar.*[]`(string),
   - `strength.{score(0..100), bucket(enum), factors[]}`,
   - `structure.{primary,status,score}`,
   - `climate.{needs[],notes[]}`,
   - `yongshin.{type,elements[],rationale}`(객관 필드 중심),
   - `wuxing.{raw.percent{木,火,土,金,水}, adjusted? , status_tag{…}}`(각 0..100 합<=100),
   - `luck.{decades{start_age(0..20),direction(enum:forward|reverse),pillars[]}, years{ YYYY }, months{ YYYY-MM }}`.
5) **`localization`**
   - `ko`(boolean).
6) **`evidence`**
   - `policies_applied[]`(string), `trace_id`(string), `inputs_hash`(string).
7) **`entitlements` (optional)**
   - `plan`(enum: `free`/`plus`/`pro`), `storage_limit`(int), `stored`(int),
   - `light_daily_left`(int), `deep_tokens`(int).
8) **`ads_suggest` (optional)**
   - `eligible`(boolean), `cooldown_min`(int ≥0).

## VALIDATION RULES
- ISO8601 `date-time` 포맷 적용.
- IANA TZ: `^[A-Za-z]+/[A-Za-z_]+(?:/[A-Za-z_]+)?$` 패턴.
- 10간/12지/60갑자/십신/12운성/신살 등은 **enum**으로 강제(대표 subset 포함, 필요시 `"enumComment"`로 전체 목록 참고 링크 설명).
- 수치 필드는 범위 강제(예: percent 0..100, score 0..100).
- `months` 키는 `^(19|20|21)\\d{2}-(0[1-9]|1[0-2])$` 패턴, `years` 키는 `^(19|20|21)\\d{2}$`.

## SAMPLES (2건 모두 제공)
- **샘플 A(표준)**: 정상 시간, `zi_hour_mode:"default"`, `regional_correction_minutes:0`.
- **샘플 B(엣지)**: `unknown_hour:true` 시나리오를 반영해 `pillars.hour`를 `null` 처리, `meta.zi_hour_mode:"split_23"`, `regional_correction_minutes:-32`, `ads_suggest.eligible:true`.
- 두 샘플 모두 `signatures.sha256` 값(32바이트 hex) 포함, `wuxing.raw.percent` 합이 100이 되도록 숫자 설정.

## OUTPUT FORMAT (반드시 이 순서)
1) 제목/버전/날짜(예: 2025-10-07 KST), 간단 개요
2) **JSON Schema (draft-2020-12)** — 단일 최상위 스키마, `$defs`에 재사용 구조(`Pillar`, `TenGod`, `WuxingPercent` 등) 분리
3) **샘플 응답 A (정상)** — 120~180줄 내
4) **샘플 응답 B (엣지/시간 모름)** — 120~180줄 내
5) **검증 힌트** — `ajv`/`jsonschema`로 검증 시 주의점(예: patternProperties로 `years`/`months` 키 검증)

## STYLE
- KO-first, 간결·정확·중립.
- 임의 서사 금지. 스키마와 예시만.
- 주석 대신 `description` 필드를 사용.

## ACCEPTANCE CRITERIA
- 스키마는 draft-2020-12 `$schema` 선언 포함.
- 필수/옵션/enum/범위/패턴이 명확.
- 샘플 A/B 모두 스키마에 **유효**해야 하며, B에 `unknown_hour:true`, `split_23`, `-32`가 등장.
- `entitlements`/`ads_suggest`가 **옵션**으로 스키마에 정의되고, 샘플 중 최소 1건에서 등장.

## NOW OUTPUT
위 조건을 충족하는 **단일 문서**를 생성하라.
