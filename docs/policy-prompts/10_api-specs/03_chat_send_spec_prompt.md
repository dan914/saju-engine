# 📘 실행 프롬프트 — `/chat/send` 오케스트레이터 스펙 v1.0

**버전**: v1.0
**날짜**: 2025-10-07 KST
**경로 권장**: `docs/policy-prompts/10_api-specs/03_chat_send_spec_prompt.md`

---

## ROLE
너는 KO-first 백엔드/플랫폼 아키텍트다. 설명 대신 **결정적 사양**만 출력한다.

## GOAL
`POST /api/v1/chat/send`의 **완전한 사양**을 산출한다:
- 상태머신(Quota→Intent→Context→Pre-Guard→Template→LLM→Post-Guard→Consume→Respond)
- 모델 라우팅 정책(Light/Deep/Fallback)
- 요청/응답 **JSON Schema(draft-2020-12)**
- 정상/에러 예시
- 헤더/보안/레이트리밋/멱등·재시도 규칙

## CONTEXT(고정)
- 채팅은 **저장된 프로필**(pillars/analysis/luck 캐시)을 컨텍스트로 사용.
- **Light**(≤300t): 짧은 코칭 요약, **토큰 소모 0**.
- **Deep**(≤900t): 상세 코칭+날짜 추천, **토큰 1 소비**.
- Free/Plus/Pro 권한·토큰 정책은 별도 API(`/entitlements`, `/tokens/*`)가 담당.
- 결과 카드는 **룰 기반(엔진 산출)**, 텍스트는 **템플릿→LLM-polish**.
- Guard: **Consistency(수치·간지·날짜 일치), Scope(민감 주제), Tone, Privacy, Grounding**.

## OUTPUT ORDER (반드시 이 순서)
1) 문서 헤더(제목/버전/날짜/베이스URL/보안)
2) **상태머신 정의**(텍스트 + 표 + 의사코드)
3) **모델 라우팅 정책** 표(라이트/딥/백스탑·타임아웃·재시도)
4) **요청/응답 JSON Schema(draft-2020-12)**
5) **정상 예시 2건**(Light/Deep) + **에러 예시 2건**(Quota/Guard)
6) **헤더/레이트리밋/멱등·재시도/타임아웃 규칙**
7) **검증 체크리스트**(필드 유효성·가드 키 일치·토큰 소비 이벤트)

## 상태머신(필수 요구사항)
- **S0 Quota Check**: `/entitlements` 조회 → 저장 한도, `light_daily_left`, `deep_tokens`. 부족 시 **Upsell 응답**(광고/토큰팩/플랜).
- **S1 Intent Classifier**: `intent ∈ {today, month, year, money, work, study, move, love, match, general}` + `depth ∈ {auto, light, deep}` 결정.
- **S2 Context Build**: `profiles/{id}` → `pillars`, `analysis`, `luck.years[YYYY]`, `luck.months[YYYY-MM]` 캐시 로드.
- **S3 Pre-Guard**: 금지 토픽(의료/법률/투자 구체행위), 개인정보 과노출 차단.
- **S4 Template Compose**: 카드(룰 기반) + 문장 슬롯 초안(draft).
- **S5 LLM Polish**: 모델 호출(Light/Deep 상한 적용).
- **S6 Post-Guard**: 컨텍스트 값과 **정합성 검사**, 위반 시 자동 패치 또는 "정보 없음".
- **S7 Consume**: `tokens/consume`(deep이면 1, light이면 0) 멱등 처리.
- **S8 Respond**: `cards[]`, `llm_text`, `consumed`, `upsell`, `next_cta[]`.

> 실패 분기: S0/S3/S6 단계에서 실패 시 **안전 응답**(가이드 문구 + 카드만)로 종료.

## 모델 라우팅 정책(표)
| Depth | 1차 | 2차(Fallback) | 3차(Backstop) | 타임아웃 | 재시도 | 메모 |
|---|---|---|---|---|---|---|
| Light | Qwen Flash **or** DeepSeek-Chat | Gemini 2.5 Pro | GPT-5 | 3s/7s/10s | 네트워크 1회 | 비용 최소·한글 품질 확보 |
| Deep | Gemini 2.5 Pro | GPT-5 | — | 8s/15s | 네트워크 1회 | 롱컨텍스트/안정 서술 |
| Report-style 텍스트 | Gemini 2.5 Pro | GPT-5 | — | 12s | 0 | 채팅 내 소규모 리포트 |

> Guard 위반/정합성 실패 시 **즉시 상위 모델 재시도 금지**, 먼저 **템플릿 축약** 후 동일 모델 1회 재시도.

## 요청/응답 JSON Schema (draft-2020-12)

### Request Schema
- 필수: `profile_id`, `message`
- 선택: `depth`, `intent`, `locale`(기본 `ko-KR`), `client_ts`
- 제약: `profile_id` UUID, `message` 길이 1–2000, `depth ∈ {auto,light,deep}`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/chat_send_request.schema.json",
  "type": "object",
  "required": ["profile_id", "message"],
  "properties": {
    "profile_id": { "type": "string", "format": "uuid", "description": "저장 프로필 ID" },
    "message": { "type": "string", "minLength": 1, "maxLength": 2000, "description": "사용자 입력" },
    "depth": { "type": "string", "enum": ["auto", "light", "deep"], "default": "auto" },
    "intent": { "type": "string", "enum": ["today","month","year","money","work","study","move","love","match","general"], "nullable": true },
    "locale": { "type": "string", "default": "ko-KR" },
    "client_ts": { "type": "string", "format": "date-time", "nullable": true }
  },
  "additionalProperties": false
}
```

### Response Schema
핵심: `cards[]`(룰 결과 카드), `llm_text`(해설), `consumed{tokens,depth}`, `upsell{show,reason,options[]}`, `next_cta[]`
카드 타입 예: `wuxing_summary`, `relations_highlight`, `strength_bucket`, `luck_snippet`(7일/1기 티저)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/chat_send_response.schema.json",
  "type": "object",
  "required": ["cards", "llm_text", "consumed"],
  "properties": {
    "cards": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type","data"],
        "properties": {
          "type": { "type": "string", "enum": ["wuxing_summary","relations_highlight","strength_bucket","luck_snippet","notice"] },
          "data": { "type": "object" }
        },
        "additionalProperties": false
      }
    },
    "llm_text": { "type": "string", "description": "LLM-polish 결과 텍스트" },
    "consumed": {
      "type": "object",
      "required": ["tokens","depth"],
      "properties": {
        "tokens": { "type": "integer", "minimum": 0 },
        "depth": { "type": "string", "enum": ["light","deep"] }
      }
    },
    "upsell": {
      "type": "object",
      "required": ["show"],
      "properties": {
        "show": { "type": "boolean" },
        "reason": { "type": "string", "nullable": true, "enum": ["no_deep_tokens","rate_limited","forbidden_topic","plan_restricted",null] },
        "options": { "type": "array", "items": { "type": "string", "enum": ["watch_ad","buy_tokens","subscribe_plus","subscribe_pro"] } }
      }
    },
    "next_cta": { "type": "array", "items": { "type": "string" } },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" }
      }
    }
  },
  "additionalProperties": false
}
```

## 정상/에러 예시

### 정상 — Light
```json
{
  "cards": [
    { "type":"wuxing_summary","data":{"percent":{"木":25,"火":15,"土":15,"金":35,"水":10},"status_tag":{"金":"over","木":"developed"}} },
    { "type":"relations_highlight","data":{"earth":{"clash":[["巳","亥"]],"he6":[["酉","辰"]]}} }
  ],
  "llm_text": "요약: 금 기운이 강해 규칙과 마감 준수가 이득입니다. 이번 주는 충이 있어 갈등을 피하고 문서 정리를 먼저 하세요.",
  "consumed": { "tokens": 0, "depth": "light" },
  "upsell": { "show": false },
  "next_cta": ["이번 달 달력 보기","용신 설명 자세히"],
  "signatures": { "sha256": "5bdc0b7b2a1d0f3a8e2a7e5cc0e6ff9f3f2c1d5e0b9a7d6c4f1a2b3c4d5e6f70" }
}
```

### 정상 — Deep
```json
{
  "cards": [
    { "type":"strength_bucket","data":{"score":38,"bucket":"weak","factors":["월령 미득령","비겁 부족"]} },
    { "type":"luck_snippet","data":{"month":"2025-10","pillar":"丙戌","ten_god":"정재","stage":"묘","range":"D+1~D+7"} }
  ],
  "llm_text": "상세: 이번 달은 정재가 활성화되어 지출 관리와 정리 정돈이 핵심입니다. 10/12~10/14에는 문서·비품 정리가 유리하고, 계약은 10/22 이후가 안정적입니다.",
  "consumed": { "tokens": 1, "depth": "deep" },
  "upsell": { "show": false },
  "next_cta": ["PDF 리포트 받기","대운 타임라인 보기"],
  "signatures": { "sha256": "e3c1abf0e5a2d9c48b1a0f2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8090a1b2c3" }
}
```

### 에러 — Quota/토큰 부족(업셀)
```json
{
  "cards": [
    { "type":"notice","data":{"title":"딥 응답 이용 불가","detail":"오늘 남은 Deep 이용 가능 횟수가 없습니다."} }
  ],
  "llm_text": "광고를 시청하거나 토큰팩을 구매하면 상세 풀이를 받을 수 있어요.",
  "consumed": { "tokens": 0, "depth": "light" },
  "upsell": { "show": true, "reason": "no_deep_tokens", "options": ["watch_ad","buy_tokens","subscribe_plus"] }
}
```

### 에러 — Guard 위반(민감 주제)
```json
{
  "cards": [
    { "type":"notice","data":{"title":"안전 가이드","detail":"해당 주제는 구체적 의료/투자 조언을 제공하지 않습니다. 대신 일상 관리 팁을 안내합니다."} }
  ],
  "llm_text": "안전: 건강/투자 관련 구체 행위는 제시하지 않고, 기록·예산·상담 등 일반적 습관을 권장합니다.",
  "consumed": { "tokens": 0, "depth": "light" },
  "upsell": { "show": false }
}
```

## 헤더/레이트리밋/멱등·재시도/타임아웃

**보안**: `Authorization: Bearer <token>`
**요청 헤더**: `X-Request-Id`(필수), `Idempotency-Key`(선택; 동일 입력 재시도 시 중복 방지)
**응답 헤더**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
**레이트리밋**: 기본 60 RPM/프로젝트(플랜별 상향)
**타임아웃**: Light 3s(1차) / Deep 8s(1차); Fallback 포함 최대 15s
**재시도**: 네트워크 오류 1회, Guard 위반 시 상위 모델 즉시 승격 금지(템플릿 축약 후 동일 모델 재시도)

## 검증 체크리스트

- [ ] `profile_id` 소유권 검증
- [ ] `intent`/`depth` 유효값 확인; `depth=auto`일 때 룰 기반 결정
- [ ] 컨텍스트(`pillars`/`analysis`/`luck`) 캐시 로드 실패 시 카드만 제공 + 안전 텍스트
- [ ] Post-Guard: `llm_text` 내 간지·날짜·퍼센트가 컨텍스트와 일치하는지 검증
- [ ] `consumed.tokens` 정확 기록 + `tokens/consume` 멱등 처리
- [ ] Upsell 사유/옵션 표준화(`no_deep_tokens`, `rate_limited`, `plan_restricted`, `forbidden_topic`)
