# POST /api/v1/chat/send — Chat Orchestrator Specification v1.0

**Version:** 1.0
**Date:** 2025-10-07 KST
**Base URL:** `https://api.saju.example.com`
**Security:** `Authorization: Bearer <token>` (Required)

사주 채팅 오케스트레이터 엔드포인트의 완전한 사양 (상태머신, 모델 라우팅, 스키마, 예시, 검증 규칙).

---

## 1. 개요

`POST /api/v1/chat/send`는 **저장된 프로필**(pillars/analysis/luck 캐시)을 컨텍스트로 사용하여, 사용자 질문에 대한 **룰 기반 카드 + LLM-polish 텍스트** 응답을 생성하는 오케스트레이터입니다.

**핵심 특징:**
- **Light**(≤300토큰): 짧은 코칭 요약, 토큰 소모 0, 일 3회 무료
- **Deep**(≤900토큰): 상세 코칭 + 날짜 추천, 토큰 1 소비
- **카드**: 룰 기반 엔진 산출 (오행/관계/강약/대운)
- **텍스트**: 템플릿 → LLM-polish (Qwen/DeepSeek/Gemini/GPT-5)
- **Guard**: 정합성(수치·간지·날짜), 민감 주제, 톤, 프라이버시

---

## 2. 상태머신 정의

### 2.1 상태 플로우

```
S0: Quota Check
  ↓
S1: Intent Classifier
  ↓
S2: Context Build
  ↓
S3: Pre-Guard
  ↓
S4: Template Compose
  ↓
S5: LLM Polish
  ↓
S6: Post-Guard
  ↓
S7: Consume
  ↓
S8: Respond
```

**실패 분기:**
- S0 실패 → **Upsell 응답** (광고/토큰팩/플랜 제안)
- S3 실패 → **안전 응답** (가이드 문구 + 카드만)
- S6 실패 → **템플릿 축약** 후 동일 모델 재시도 1회 → 실패 시 안전 응답

### 2.2 상태별 정의

| 상태 | 입력 | 처리 | 출력 | 실패 처리 |
|------|------|------|------|-----------|
| **S0 Quota** | `profile_id`, `depth` | `/entitlements` 조회: `light_daily_left`, `deep_tokens` | quota_ok/quota_fail | Upsell 응답 (광고/토큰팩/플랜) |
| **S1 Intent** | `message`, `intent`(optional) | NLU 분류: `{today,month,year,money,work,study,move,love,match,general}` + `depth` 결정 (`auto` → 룰 기반) | intent, depth | 기본값 `general`, `light` |
| **S2 Context** | `profile_id` | `/profiles/{id}` 캐시 로드: `pillars`, `analysis`, `luck.years[YYYY]`, `luck.months[YYYY-MM]` | context_data | 캐시 없으면 카드만 + 안전 텍스트 |
| **S3 Pre-Guard** | `message`, `intent` | 금지 토픽 검사 (의료/법률/투자 구체행위), 개인정보 과노출 | pass/block | 안전 응답 (가이드 문구) |
| **S4 Template** | `intent`, `context_data` | 카드 생성 (룰 기반: 오행/관계/강약/대운) + 문장 슬롯 초안 | cards[], draft_text | N/A (항상 성공) |
| **S5 LLM** | `draft_text`, `depth` | 모델 호출 (Light: Qwen/DeepSeek → Gemini → GPT-5, Deep: Gemini → GPT-5), 상한 ≤300t(Light) / ≤900t(Deep) | llm_text | Fallback 체인 실행 |
| **S6 Post-Guard** | `llm_text`, `context_data` | 정합성 검사: 간지/날짜/퍼센트 일치, 위반 시 자동 패치 또는 "정보 없음" | pass/revise | 템플릿 축약 → S5 재시도 1회 |
| **S7 Consume** | `depth`, `profile_id` | `POST /tokens/consume` (deep=1, light=0), Idempotency-Key 처리 | consumed_tokens | 멱등성 보장, 실패 시 응답 포함 |
| **S8 Respond** | `cards`, `llm_text`, `consumed`, `upsell` | 최종 응답 구성: `cards[]`, `llm_text`, `consumed`, `upsell`, `next_cta[]`, RFC-8785 서명 | JSON response | N/A |

### 2.3 의사코드

```python
def chat_send(request):
    # S0: Quota Check
    entitlements = get_entitlements(request.profile_id)
    if request.depth == "deep" and entitlements.deep_tokens <= 0:
        return upsell_response(reason="no_deep_tokens", options=["watch_ad", "buy_tokens"])
    if request.depth == "light" and entitlements.light_daily_left <= 0:
        return upsell_response(reason="rate_limited", options=["subscribe_plus"])

    # S1: Intent Classifier
    intent = classify_intent(request.message, request.intent)
    depth = decide_depth(request.depth, intent)  # auto → 룰 기반

    # S2: Context Build
    context = load_context(request.profile_id)
    if not context:
        return safe_response(cards=[], text="프로필을 먼저 생성해주세요.")

    # S3: Pre-Guard
    guard_result = pre_guard_check(request.message, intent)
    if guard_result.block:
        return safe_response(cards=[], text=guard_result.guide_text)

    # S4: Template Compose
    cards = generate_cards(intent, context)
    draft_text = compose_template(intent, context, depth)

    # S5: LLM Polish
    llm_text = llm_polish(draft_text, depth, model_chain=get_model_chain(depth))

    # S6: Post-Guard
    post_guard_result = post_guard_check(llm_text, context)
    if post_guard_result.revise:
        draft_text = shorten_template(draft_text)
        llm_text = llm_polish(draft_text, depth, model_chain=get_model_chain(depth), retry=1)
        post_guard_result = post_guard_check(llm_text, context)
        if post_guard_result.revise:
            llm_text = safe_fallback_text(intent)

    # S7: Consume
    consumed = consume_tokens(request.profile_id, depth, idempotency_key=request.headers["Idempotency-Key"])

    # S8: Respond
    return {
        "cards": cards,
        "llm_text": llm_text,
        "consumed": consumed,
        "upsell": {"show": False},
        "next_cta": generate_next_cta(intent, depth),
        "signatures": {"sha256": compute_signature(response)}
    }
```

---

## 3. 모델 라우팅 정책

| Depth | 1차 모델 | 2차 Fallback | 3차 Backstop | 타임아웃 | 재시도 | 메모 |
|-------|----------|--------------|--------------|----------|--------|------|
| **Light** | Qwen Flash **or** DeepSeek-Chat | Gemini 2.5 Pro | GPT-5 | 3s / 7s / 10s | 네트워크 1회 | 비용 최소화, 한글 품질 확보 |
| **Deep** | Gemini 2.5 Pro | GPT-5 | — | 8s / 15s | 네트워크 1회 | 롱컨텍스트, 안정적 서술 |
| **Report-style** | Gemini 2.5 Pro | GPT-5 | — | 12s | 0회 | 채팅 내 소규모 리포트 |

**재시도 규칙:**
- **네트워크 오류**: 1회 재시도 (동일 모델)
- **Guard 위반/정합성 실패**: 즉시 상위 모델 승격 **금지** → 먼저 **템플릿 축약** 후 동일 모델 재시도 1회
- **타임아웃**: 다음 모델로 Fallback (예: Qwen 3s 초과 → DeepSeek → Gemini)

**모델별 토큰 상한:**
- Light: ≤300 토큰
- Deep: ≤900 토큰

---

## 4. 요청/응답 JSON Schema

### 4.1 Request Schema (draft-2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/chat_send_request_v1.schema.json",
  "title": "ChatSendRequest",
  "description": "POST /api/v1/chat/send 요청 스키마",
  "type": "object",
  "required": ["profile_id", "message"],
  "properties": {
    "profile_id": {
      "type": "string",
      "format": "uuid",
      "description": "저장된 프로필 ID (GET /api/v1/profiles에서 생성)"
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000,
      "description": "사용자 입력 메시지"
    },
    "depth": {
      "type": "string",
      "enum": ["auto", "light", "deep"],
      "default": "auto",
      "description": "응답 깊이 (auto: 룰 기반 자동 결정, light: 간단, deep: 상세)"
    },
    "intent": {
      "type": "string",
      "enum": ["today", "month", "year", "money", "work", "study", "move", "love", "match", "general"],
      "nullable": true,
      "description": "사용자 의도 (optional, 미제공 시 NLU 분류)"
    },
    "locale": {
      "type": "string",
      "default": "ko-KR",
      "description": "응답 언어 (현재 ko-KR만 지원)"
    },
    "client_ts": {
      "type": "string",
      "format": "date-time",
      "nullable": true,
      "description": "클라이언트 타임스탬프 (시간 기반 intent 결정에 사용)"
    }
  },
  "additionalProperties": false
}
```

### 4.2 Response Schema (draft-2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/chat_send_response_v1.schema.json",
  "title": "ChatSendResponse",
  "description": "POST /api/v1/chat/send 응답 스키마",
  "type": "object",
  "required": ["cards", "llm_text", "consumed"],
  "properties": {
    "cards": {
      "type": "array",
      "description": "룰 기반 카드 목록",
      "items": {
        "type": "object",
        "required": ["type", "data"],
        "properties": {
          "type": {
            "type": "string",
            "enum": ["wuxing_summary", "relations_highlight", "strength_bucket", "luck_snippet", "notice"],
            "description": "카드 타입"
          },
          "data": {
            "type": "object",
            "description": "카드별 데이터 (타입에 따라 구조 상이)"
          }
        },
        "additionalProperties": false
      }
    },
    "llm_text": {
      "type": "string",
      "description": "LLM-polish 결과 텍스트 (템플릿 기반 초안 → 모델 다듬기)"
    },
    "consumed": {
      "type": "object",
      "required": ["tokens", "depth"],
      "properties": {
        "tokens": {
          "type": "integer",
          "minimum": 0,
          "description": "소비된 토큰 (light=0, deep=1)"
        },
        "depth": {
          "type": "string",
          "enum": ["light", "deep"],
          "description": "실제 사용된 깊이"
        }
      }
    },
    "upsell": {
      "type": "object",
      "required": ["show"],
      "properties": {
        "show": {
          "type": "boolean",
          "description": "업셀 제안 표시 여부"
        },
        "reason": {
          "type": "string",
          "nullable": true,
          "enum": ["no_deep_tokens", "rate_limited", "forbidden_topic", "plan_restricted", null],
          "description": "업셀 사유"
        },
        "options": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["watch_ad", "buy_tokens", "subscribe_plus", "subscribe_pro"]
          },
          "description": "제안 옵션 목록"
        }
      }
    },
    "next_cta": {
      "type": "array",
      "items": { "type": "string" },
      "description": "다음 행동 제안 (예: '이번 달 달력 보기', 'PDF 리포트 받기')"
    },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": {
          "type": "string",
          "pattern": "^[A-Fa-f0-9]{64}$",
          "description": "RFC-8785 canonical JSON SHA-256 해시"
        }
      }
    }
  },
  "additionalProperties": false
}
```

---

## 5. 정상/에러 예시

### 5.1 정상 — Light (오행/관계 요약)

**Request:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "이번 주 운세 간단하게 알려줘",
  "depth": "auto",
  "locale": "ko-KR"
}
```

**Response:**
```json
{
  "cards": [
    {
      "type": "wuxing_summary",
      "data": {
        "percent": {
          "木": 25,
          "火": 15,
          "土": 15,
          "金": 35,
          "水": 10
        },
        "status_tag": {
          "金": "over",
          "木": "developed"
        }
      }
    },
    {
      "type": "relations_highlight",
      "data": {
        "earth": {
          "clash": [["巳", "亥"]],
          "he6": [["酉", "辰"]]
        }
      }
    }
  ],
  "llm_text": "요약: 금 기운이 강해 규칙과 마감 준수가 이득입니다. 이번 주는 충이 있어 갈등을 피하고 문서 정리를 먼저 하세요.",
  "consumed": {
    "tokens": 0,
    "depth": "light"
  },
  "upsell": {
    "show": false
  },
  "next_cta": [
    "이번 달 달력 보기",
    "용신 설명 자세히"
  ],
  "signatures": {
    "sha256": "5bdc0b7b2a1d0f3a8e2a7e5cc0e6ff9f3f2c1d5e0b9a7d6c4f1a2b3c4d5e6f70"
  }
}
```

### 5.2 정상 — Deep (강약/대운 상세 해석)

**Request:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "이번 달 재운 상세하게 봐줘",
  "depth": "deep",
  "intent": "money",
  "locale": "ko-KR"
}
```

**Response:**
```json
{
  "cards": [
    {
      "type": "strength_bucket",
      "data": {
        "score": 38,
        "bucket": "weak",
        "factors": ["월령 미득령", "비겁 부족"]
      }
    },
    {
      "type": "luck_snippet",
      "data": {
        "month": "2025-10",
        "pillar": "丙戌",
        "ten_god": "정재",
        "stage": "묘",
        "range": "D+1~D+7"
      }
    }
  ],
  "llm_text": "상세: 이번 달은 정재가 활성화되어 지출 관리와 정리 정돈이 핵심입니다. 10/12~10/14에는 문서·비품 정리가 유리하고, 계약은 10/22 이후가 안정적입니다.",
  "consumed": {
    "tokens": 1,
    "depth": "deep"
  },
  "upsell": {
    "show": false
  },
  "next_cta": [
    "PDF 리포트 받기",
    "대운 타임라인 보기"
  ],
  "signatures": {
    "sha256": "e3c1abf0e5a2d9c48b1a0f2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8090a1b2c3"
  }
}
```

### 5.3 에러 — Quota 부족 (업셀)

**Request:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "대운 상세 해석 부탁해",
  "depth": "deep"
}
```

**Response (HTTP 200, upsell=true):**
```json
{
  "cards": [
    {
      "type": "notice",
      "data": {
        "title": "딥 응답 이용 불가",
        "detail": "오늘 남은 Deep 이용 가능 횟수가 없습니다."
      }
    }
  ],
  "llm_text": "광고를 시청하거나 토큰팩을 구매하면 상세 풀이를 받을 수 있어요.",
  "consumed": {
    "tokens": 0,
    "depth": "light"
  },
  "upsell": {
    "show": true,
    "reason": "no_deep_tokens",
    "options": ["watch_ad", "buy_tokens", "subscribe_plus"]
  },
  "next_cta": []
}
```

### 5.4 에러 — Guard 위반 (민감 주제)

**Request:**
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "내 사주로 주식 종목 추천해줘",
  "depth": "deep"
}
```

**Response (HTTP 200, Pre-Guard 차단):**
```json
{
  "cards": [
    {
      "type": "notice",
      "data": {
        "title": "안전 가이드",
        "detail": "해당 주제는 구체적 의료/투자 조언을 제공하지 않습니다. 대신 일상 관리 팁을 안내합니다."
      }
    }
  ],
  "llm_text": "안전: 건강/투자 관련 구체 행위는 제시하지 않고, 기록·예산·상담 등 일반적 습관을 권장합니다.",
  "consumed": {
    "tokens": 0,
    "depth": "light"
  },
  "upsell": {
    "show": false
  },
  "next_cta": []
}
```

---

## 6. 헤더/레이트리밋/멱등·재시도/타임아웃

### 6.1 요청 헤더

| 헤더 | 필수 | 형식 | 설명 |
|------|------|------|------|
| `Authorization` | ✅ | `Bearer <token>` | 인증 토큰 |
| `X-Request-Id` | ✅ | UUID v4 | 요청 추적 ID |
| `Idempotency-Key` | ❌ | UUID v4 | 재시도 중복 방지 (동일 입력 재전송 시 사용) |
| `Content-Type` | ✅ | `application/json` | JSON 페이로드 |

### 6.2 응답 헤더

| 헤더 | 형식 | 설명 |
|------|------|------|
| `X-RateLimit-Limit` | integer | 분당 요청 한도 (기본 60) |
| `X-RateLimit-Remaining` | integer | 남은 요청 수 |
| `X-RateLimit-Reset` | UNIX timestamp | 리셋 시간 |
| `X-Request-Id` | UUID v4 | 요청 추적 ID (echo) |

### 6.3 레이트리밋

**기본:** 60 RPM (Requests Per Minute) / 프로젝트
**플랜별 상향:**
- Free: 60 RPM
- Plus: 120 RPM
- Pro: 300 RPM

**초과 시:** HTTP 429 Too Many Requests
```json
{
  "error": {
    "code": "E_RATE_LIMITED",
    "message": "요청 한도를 초과했습니다. 1분 후 재시도하세요.",
    "retry_after": 60
  }
}
```

### 6.4 타임아웃

| Depth | 1차 모델 | 2차 Fallback | 3차 Backstop | 최대 총 시간 |
|-------|----------|--------------|--------------|--------------|
| Light | 3s (Qwen/DeepSeek) | 7s (Gemini) | 10s (GPT-5) | 15s |
| Deep  | 8s (Gemini) | 15s (GPT-5) | — | 15s |

**초과 시:** 다음 모델로 Fallback, 최종 실패 시 HTTP 504 Gateway Timeout

### 6.5 멱등성 & 재시도

**멱등성:**
- `Idempotency-Key` 헤더 제공 시, 동일 키로 24시간 내 재요청 시 캐시된 응답 반환
- 토큰 소비는 최초 1회만 발생

**재시도 규칙:**
1. **네트워크 오류** (연결 실패, 5xx): 1회 재시도 (동일 모델)
2. **타임아웃**: 다음 모델로 Fallback (예: Qwen 3s → DeepSeek 7s)
3. **Guard 위반/정합성 실패**: 즉시 상위 모델 승격 **금지** → 템플릿 축약 후 동일 모델 재시도 1회 → 실패 시 안전 응답

**클라이언트 재시도:**
- 4xx 에러: 재시도 불필요 (클라이언트 오류)
- 5xx/타임아웃: 지수 백오프 (1s → 2s → 4s) 최대 3회

---

## 7. 검증 체크리스트

### 7.1 요청 검증

- [ ] `profile_id` UUID 형식 검증
- [ ] `profile_id` 소유권 검증 (Authorization 토큰과 일치)
- [ ] `message` 길이 1~2000자
- [ ] `depth` ∈ {auto, light, deep}
- [ ] `intent` ∈ {today, month, year, money, work, study, move, love, match, general} or null
- [ ] `locale` 지원 여부 (현재 ko-KR만)

### 7.2 상태머신 검증

- [ ] **S0 Quota**: `/entitlements` 조회 성공, `light_daily_left`/`deep_tokens` 확인
- [ ] **S1 Intent**: `depth=auto` 시 룰 기반 결정 (예: "오늘" → today, "이번 달" → month)
- [ ] **S2 Context**: 캐시 로드 실패 시 카드만 제공 + 안전 텍스트
- [ ] **S3 Pre-Guard**: 금지 토픽 키워드 필터링 (의료: "치료", "약", 투자: "종목", "매수")
- [ ] **S4 Template**: 카드 타입별 데이터 구조 일치 (wuxing_summary.percent 합=100)
- [ ] **S5 LLM**: 모델 타임아웃 준수, Fallback 체인 실행
- [ ] **S6 Post-Guard**: `llm_text` 내 간지/날짜/퍼센트가 `context_data`와 일치
- [ ] **S7 Consume**: `POST /tokens/consume` 멱등 처리 (Idempotency-Key)
- [ ] **S8 Respond**: RFC-8785 서명 생성 (signatures.sha256)

### 7.3 응답 검증

- [ ] `cards[]` 최소 1개 (실패 시 notice 카드)
- [ ] `llm_text` 비어있지 않음
- [ ] `consumed.tokens` ∈ {0, 1}
- [ ] `consumed.depth` ∈ {light, deep}
- [ ] `upsell.show=true` 시 `reason` 필수
- [ ] `upsell.reason` ∈ {no_deep_tokens, rate_limited, forbidden_topic, plan_restricted}
- [ ] `next_cta[]` intent별 적절한 제안 (예: money → "재운 달력", year → "대운 타임라인")
- [ ] `signatures.sha256` 64자 hex 문자열

### 7.4 Guard 검증

**Pre-Guard (금지 토픽):**
- [ ] 의료: "치료", "약 처방", "수술", "진단" → 차단
- [ ] 법률: "소송", "계약서 조항", "법적 책임" → 차단
- [ ] 투자: "주식 종목", "코인 매수", "부동산 매매" → 차단
- [ ] 개인정보: "주민번호", "계좌번호", "비밀번호" → 차단

**Post-Guard (정합성):**
- [ ] `llm_text` 내 간지가 `pillars`에 존재
- [ ] `llm_text` 내 날짜가 `luck.months` 키 범위 내
- [ ] `llm_text` 내 퍼센트가 `wuxing.raw.percent` ±5% 오차 내
- [ ] `llm_text` 내 십신이 `ten_gods.by_pillar` 일치
- [ ] 위반 시 자동 패치 (예: "辛巳" → "해당 기둥") 또는 "정보 없음"

---

## 8. 카드 타입 상세

### 8.1 wuxing_summary (오행 요약)

**용도:** 오행 분포 시각화
**데이터 구조:**
```json
{
  "type": "wuxing_summary",
  "data": {
    "percent": {
      "木": 25.0,
      "火": 15.0,
      "土": 15.0,
      "金": 35.0,
      "水": 10.0
    },
    "status_tag": {
      "木": "developed",
      "火": "weak",
      "土": "weak",
      "金": "over",
      "水": "weak"
    }
  }
}
```

**검증:**
- [ ] `percent` 합계 = 100 (±0.1 오차 허용)
- [ ] `status_tag` ∈ {over, developed, balanced, weak, missing}

### 8.2 relations_highlight (관계 하이라이트)

**용도:** 주요 관계 (합/충/형) 표시
**데이터 구조:**
```json
{
  "type": "relations_highlight",
  "data": {
    "heavenly": {
      "combine": [["甲", "己"]]
    },
    "earth": {
      "clash": [["巳", "亥"]],
      "he6": [["酉", "辰"]]
    }
  }
}
```

**검증:**
- [ ] 간지가 `pillars`에 존재
- [ ] 관계가 `relation_policy.json`과 일치

### 8.3 strength_bucket (강약 등급)

**용도:** 일간 세력 요약
**데이터 구조:**
```json
{
  "type": "strength_bucket",
  "data": {
    "score": 38.0,
    "bucket": "weak",
    "factors": ["월령 미득령", "비겁 부족"]
  }
}
```

**검증:**
- [ ] `score` ∈ [0, 100]
- [ ] `bucket` ∈ {extreme_strong, strong, balanced, weak, extreme_weak}
- [ ] `bucket`이 `strength_policy_v2.json` 구간과 일치

### 8.4 luck_snippet (대운/월운 티저)

**용도:** 7일/1기 운세 미리보기
**데이터 구조:**
```json
{
  "type": "luck_snippet",
  "data": {
    "month": "2025-10",
    "pillar": "丙戌",
    "ten_god": "정재",
    "stage": "묘",
    "range": "D+1~D+7",
    "good_days": [3, 8, 13],
    "caution_days": [5, 14]
  }
}
```

**검증:**
- [ ] `month` 형식 YYYY-MM
- [ ] `pillar` 60갑자 패턴
- [ ] `ten_god` 십신 enum
- [ ] `stage` 12운성 enum
- [ ] `good_days`/`caution_days` ∈ [1, 31]

### 8.5 notice (공지/안내)

**용도:** 업셀/Guard 안내
**데이터 구조:**
```json
{
  "type": "notice",
  "data": {
    "title": "딥 응답 이용 불가",
    "detail": "오늘 남은 Deep 이용 가능 횟수가 없습니다."
  }
}
```

---

## 9. 에러 코드

| 코드 | HTTP | 설명 | 해결 방법 |
|------|------|------|-----------|
| `E_BAD_REQUEST` | 400 | 요청 형식 오류 | 스키마 검증 |
| `E_UNAUTHORIZED` | 401 | 인증 실패 | Bearer 토큰 확인 |
| `E_FORBIDDEN` | 403 | 권한 부족 | profile_id 소유권 확인 |
| `E_NOT_FOUND` | 404 | 프로필 미존재 | GET /profiles로 생성 |
| `E_RATE_LIMITED` | 429 | 요청 한도 초과 | retry_after 초 대기 |
| `E_SERVER` | 500 | 서버 내부 오류 | 로그 확인 + 재시도 |
| `E_TIMEOUT` | 504 | LLM 타임아웃 | Fallback 실패, 재시도 |

**에러 응답 형식:**
```json
{
  "error": {
    "code": "E_RATE_LIMITED",
    "message": "요청 한도를 초과했습니다. 1분 후 재시도하세요.",
    "retry_after": 60
  }
}
```

---

## 10. 구현 체크리스트

### Phase 1: 상태머신 (우선순위: 높음)
- [ ] S0: Quota Check (`/entitlements` 통합)
- [ ] S1: Intent Classifier (NLU 모델 또는 룰 기반)
- [ ] S2: Context Build (`/profiles/{id}` 캐시 로더)
- [ ] S3: Pre-Guard (금지 토픽 키워드 필터)
- [ ] S4: Template Compose (카드 생성 + 초안 작성)
- [ ] S5: LLM Polish (모델 라우팅 체인)
- [ ] S6: Post-Guard (정합성 검증 + 패치)
- [ ] S7: Consume (`/tokens/consume` 멱등 호출)
- [ ] S8: Respond (RFC-8785 서명 생성)

### Phase 2: 모델 통합 (우선순위: 높음)
- [ ] Qwen Flash API 연동
- [ ] DeepSeek-Chat API 연동
- [ ] Gemini 2.5 Pro API 연동
- [ ] GPT-5 API 연동
- [ ] Fallback 체인 구현 (타임아웃 → 다음 모델)
- [ ] 토큰 상한 적용 (Light ≤300t, Deep ≤900t)

### Phase 3: 카드 엔진 (우선순위: 중간)
- [ ] wuxing_summary 카드 생성
- [ ] relations_highlight 카드 생성
- [ ] strength_bucket 카드 생성
- [ ] luck_snippet 카드 생성 (7일/1기 티저)
- [ ] notice 카드 생성 (업셀/Guard)

### Phase 4: Guard 구현 (우선순위: 높음)
- [ ] Pre-Guard: 금지 토픽 키워드 DB
- [ ] Post-Guard: 간지 일치 검증
- [ ] Post-Guard: 날짜 범위 검증
- [ ] Post-Guard: 퍼센트 오차 검증
- [ ] Auto-patch: "정보 없음" 대체

### Phase 5: 테스트 (우선순위: 높음)
- [ ] 단위 테스트: 상태머신 각 단계
- [ ] 통합 테스트: E2E 플로우 (Light/Deep)
- [ ] 에러 시나리오: Quota/Guard/Timeout
- [ ] 성능 테스트: P95 응답 시간 <5s (Light), <10s (Deep)
- [ ] 멱등성 테스트: 동일 Idempotency-Key 재요청

---

**Version:** v1.0 (2025-10-07 KST)
**Last Updated:** 2025-10-07
**Maintainer:** Core Architects (Backend/Policy/Data)
