# 사주 API 명세서 v1.0

**버전**: 1.0.0
**날짜**: 2025-10-07
**베이스 URL**: `https://api.saju.example.com`
**인증**: Bearer Token
**응답 형식**: RFC-8785 Canonical JSON

---

## 글로벌 규칙

### 인증
모든 요청에 필수:
```
Authorization: Bearer <app_token>
```

### 공통 헤더

**요청 헤더**:
- `X-Request-Id` (string, optional): 클라이언트 요청 추적 ID
- `Idempotency-Key` (string, required for POST /tokens/*): 멱등성 보장 키 (UUID v4)
- `Accept-Language` (string, optional): `ko-KR` (기본값) | `en-US`

**응답 헤더**:
- `X-Request-Id` (string): 요청 추적 ID (에코 또는 서버 생성)
- `X-RateLimit-Limit` (integer): 시간 창 내 최대 요청 수
- `X-RateLimit-Remaining` (integer): 남은 요청 수
- `X-RateLimit-Reset` (integer): 리셋 시각 (Unix epoch)
- `Cache-Control` (string): 캐시 정책 (luck 엔드포인트)

### 공통 에러 모델

**ErrorResponse**:
```json
{
  "error_code": "E_BAD_REQUEST",
  "message": "요청 형식이 올바르지 않습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "birth_dt_local 필드는 ISO8601 형식이어야 합니다",
  "field": "birth_dt_local"
}
```

**필드**:
- `error_code` (string, required): 에러 코드 (아래 표 참조)
- `message` (string, required): 한국어 에러 메시지
- `trace_id` (string, required): 서버 추적 ID
- `hint` (string, optional): 해결 방법 힌트
- `field` (string, optional): 문제 필드명

### 응답 서명

모든 응답 JSON은 RFC-8785 정규화 후 SHA-256 서명:
```json
{
  "data": {...},
  "signatures": {
    "sha256": "a3f2c1b9..."
  }
}
```

---

## 1. POST /api/v1/report/saju

**설명**: 사주 전체 분석 리포트 생성 (홈 탭 데이터 소스)

### 요청

**Request Body**:
```json
{
  "birth_dt_local": "2000-09-14T10:00:00",
  "timezone": "Asia/Seoul",
  "calendar_type": "solar",
  "unknown_hour": false,
  "zi_hour_mode": "default",
  "gender": "m",
  "name": "홍길동",
  "options": {
    "include_annual_luck": true,
    "include_monthly_luck": true,
    "annual_years": 10,
    "monthly_months": 12
  }
}
```

**스키마**:
```typescript
{
  birth_dt_local: string;        // ISO8601, required
  timezone: string;              // IANA timezone, required
  calendar_type: "solar" | "lunar";  // required
  unknown_hour?: boolean;        // 시간 모름, default: false
  zi_hour_mode?: "default" | "split_23" | "split_00";  // default: "default"
  gender?: "m" | "f" | null;     // optional
  name?: string;                 // optional, max 50자
  regional_correction_minutes?: number;  // LMT 보정, default: auto
  options?: {
    include_annual_luck?: boolean;      // default: true
    include_monthly_luck?: boolean;     // default: true
    annual_years?: number;              // 1-20, default: 10
    monthly_months?: number;            // 1-24, default: 12
  }
}
```

### 응답

**Status**: 200 OK

**Response Body** (요약):
```json
{
  "meta": {
    "request_id": "req_7f3a9b2c",
    "version": "1.0.0",
    "generated_at": "2025-10-07T10:30:45Z"
  },
  "time": {
    "input_local": "2000-09-14T10:00:00",
    "timezone": "Asia/Seoul",
    "solar_adjusted": "2000-09-14T09:28:00",
    "lmt_correction_minutes": -32,
    "dst_applied": false
  },
  "pillars": {
    "year": {"pillar": "庚辰", "stem": "庚", "branch": "辰"},
    "month": {"pillar": "乙酉", "stem": "乙", "branch": "酉"},
    "day": {"pillar": "乙亥", "stem": "乙", "branch": "亥"},
    "hour": {"pillar": "辛巳", "stem": "辛", "branch": "巳"}
  },
  "analysis": {
    "ten_gods": {
      "summary": {
        "year": "偏官",
        "month": "比肩",
        "day": "日主",
        "hour": "正官"
      }
    },
    "relations": {
      "he6": [["辰", "酉"]],
      "sanhe": [],
      "chong": [["巳", "亥"]],
      "hai": [],
      "po": [],
      "xing": []
    },
    "strength": {
      "level": "신약",
      "basis": {
        "season": "得令",
        "roots": "有本氣",
        "seal": "天干1見",
        "peer": "同氣"
      }
    },
    "structure": {
      "primary": null,
      "confidence": "low",
      "candidates": [
        {"type": "정관", "score": 15},
        {"type": "편관", "score": 15}
      ]
    },
    "luck": {
      "start_age": 7.98,
      "direction": null
    },
    "twelve_stages": {
      "year": {"stage": "양", "description": "양육 단계"},
      "month": {"stage": "병", "description": "병약 단계"},
      "day": {"stage": "태", "description": "태아 단계"},
      "hour": {"stage": "절", "description": "절멸 단계"}
    },
    "void": {
      "has_void": true,
      "void_branches": ["午", "未"],
      "affected_pillars": ["none"]
    },
    "yuanjin": {
      "has_yuanjin": false,
      "pairs": []
    }
  },
  "luck_annual": {
    "years": [
      {
        "year": 2025,
        "age": 25,
        "pillar": "甲辰",
        "summary": "변화와 성장의 해",
        "forecast": {
          "career": "길",
          "wealth": "중길",
          "relationship": "평",
          "health": "주의"
        }
      }
    ]
  },
  "luck_monthly": {
    "months": [
      {
        "year_month": "2025-10",
        "pillar": "丙戌",
        "summary": "재물운 상승",
        "good_days": ["2025-10-03", "2025-10-15"],
        "caution_days": ["2025-10-08", "2025-10-22"]
      }
    ]
  },
  "localization": {
    "locale": "ko-KR",
    "enriched_count": 141,
    "version": "1.0.0"
  },
  "evidence": {
    "rule_id": "KR_classic_v1.4",
    "trace": {
      "tz_time_ms": 45,
      "astro_ms": 12,
      "pillars_ms": 23,
      "analysis_ms": 89,
      "luck_ms": 156,
      "total_ms": 325
    }
  },
  "signatures": {
    "sha256": "a3f2c1b9d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
  }
}
```

### 에러

**Status**: 400 Bad Request
```json
{
  "error_code": "E_BAD_REQUEST",
  "message": "birth_dt_local 형식이 올바르지 않습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "ISO8601 형식을 사용하세요 (예: 2000-09-14T10:00:00)",
  "field": "birth_dt_local"
}
```

**Status**: 422 Unprocessable Entity
```json
{
  "error_code": "E_INVALID_DATE",
  "message": "해당 날짜의 절기 데이터를 찾을 수 없습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "1900-2050년 사이의 날짜만 지원됩니다"
}
```

### 비고
- 캐시: 동일 명식 30일 캐시 (birth_dt + timezone + calendar_type 기준)
- 레이트리밋: 100 req/min (무료), 1000 req/min (Pro)
- 평균 응답시간: 300-500ms

---

## 2. POST /api/v1/chat/send

**설명**: 대화형 사주 상담 (채팅 탭)

### 요청

**Request Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "message": "이번 달 금전운과 지출 포인트 알려줘",
  "depth": "auto",
  "intent": null,
  "locale": "ko-KR",
  "context": {
    "previous_message_id": "msg_123"
  }
}
```

**스키마**:
```typescript
{
  profile_id: string;          // required, 저장된 프로필 ID
  message: string;             // required, 1-500자
  depth?: "auto" | "light" | "deep";  // default: "auto"
  intent?: string | null;      // optional, 서버가 자동 분류
  locale?: "ko-KR" | "en-US";  // default: "ko-KR"
  context?: {
    previous_message_id?: string;
    session_id?: string;
  }
}
```

### 응답

**Status**: 200 OK

**Response Body**:
```json
{
  "message_id": "msg_456",
  "cards": [
    {
      "type": "wuxing_summary",
      "data": {
        "wood": 2,
        "fire": 0,
        "earth": 1,
        "metal": 3,
        "water": 2,
        "dominant": "metal",
        "lacking": "fire"
      }
    },
    {
      "type": "relations_highlight",
      "data": {
        "he6": [["辰", "酉"]],
        "chong": [["巳", "亥"]],
        "message": "육합이 있어 조화로우나 충이 있어 주의 필요"
      }
    }
  ],
  "llm_text": "이번 달(10월)은 丙戌월로 정재 비중이 높아 금전운이 좋습니다. 다만 15일과 22일은 충이 발생하므로 큰 지출은 피하시고, 3일과 15일에 재물 관련 일을 처리하시면 좋습니다.",
  "consumed": {
    "tokens": 1,
    "depth": "deep",
    "cost_estimate": "₩2"
  },
  "upsell": {
    "show": false,
    "reason": null
  },
  "next_cta": [
    "월운 달력 보기",
    "PDF 리포트 받기"
  ],
  "intent_detected": "monthly_wealth",
  "model_used": "gemini-2.5-pro"
}
```

### 에러

**Status**: 403 Forbidden
```json
{
  "error_code": "E_QUOTA_EXCEEDED",
  "message": "Deep 토큰이 부족합니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "광고를 시청하거나 토큰팩을 구매하세요",
  "remaining": {
    "light_daily": 2,
    "deep_tokens": 0
  }
}
```

**Status**: 404 Not Found
```json
{
  "error_code": "E_PROFILE_NOT_FOUND",
  "message": "프로필을 찾을 수 없습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "profile_id를 확인하거나 새 프로필을 생성하세요"
}
```

### 비고
- 레이트리밋: Light 5 req/min, Deep 2 req/min
- 캐시: 동일 질문 + profile_id 조합 1시간 캐시
- 평균 응답시간: Light 500-800ms, Deep 1500-3000ms

---

## 3. POST /api/v1/luck/annual

**설명**: 연운 조회 (캐시 우선)

### 요청

**Request Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "years": [2025, 2026, 2027],
  "include_forecast": true
}
```

**스키마**:
```typescript
{
  profile_id: string;          // required
  years: number[];             // required, 1-20개
  include_forecast?: boolean;  // default: true
}
```

### 응답

**Status**: 200 OK
**Cache-Control**: `public, max-age=31536000` (365일)

**Response Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "years": [
    {
      "year": 2025,
      "age": 25,
      "pillar": "甲辰",
      "stem": "甲",
      "branch": "辰",
      "summary": "변화와 성장의 해",
      "forecast": {
        "career": "길",
        "wealth": "중길",
        "relationship": "평",
        "health": "주의"
      },
      "key_events": [
        "상반기 직장 이동 가능성",
        "7-9월 재물운 상승"
      ]
    }
  ],
  "cache_ttl_sec": 31536000,
  "generated_at": "2025-10-07T10:30:45Z"
}
```

### 에러

**Status**: 404 Not Found
```json
{
  "error_code": "E_PROFILE_NOT_FOUND",
  "message": "프로필을 찾을 수 없습니다",
  "trace_id": "req_7f3a9b2c"
}
```

### 비고
- 캐시: Redis, TTL 365일
- 레이트리밋: 20 req/min
- 평균 응답시간: 150-250ms (캐시), 800-1200ms (계산)

---

## 4. POST /api/v1/luck/monthly

**설명**: 월운 조회 (캐시 우선)

### 요청

**Request Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "year_months": ["2025-10", "2025-11", "2025-12"],
  "include_good_days": true,
  "include_caution_days": true
}
```

**스키마**:
```typescript
{
  profile_id: string;            // required
  year_months: string[];         // required, 1-24개, "YYYY-MM" 형식
  include_good_days?: boolean;   // default: true
  include_caution_days?: boolean; // default: true
}
```

### 응답

**Status**: 200 OK
**Cache-Control**: `public, max-age=2592000` (30일)

**Response Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "months": [
    {
      "year_month": "2025-10",
      "pillar": "丙戌",
      "stem": "丙",
      "branch": "戌",
      "summary": "재물운 상승, 대인관계 주의",
      "good_days": [
        {
          "date": "2025-10-03",
          "reason": "육합일",
          "activities": ["계약", "투자", "이사"]
        },
        {
          "date": "2025-10-15",
          "reason": "귀인일",
          "activities": ["면접", "상담", "협상"]
        }
      ],
      "caution_days": [
        {
          "date": "2025-10-08",
          "reason": "충일",
          "avoid": ["큰 결정", "수술", "이동"]
        }
      ]
    }
  ],
  "cache_ttl_sec": 2592000,
  "generated_at": "2025-10-07T10:30:45Z"
}
```

### 에러

**Status**: 400 Bad Request
```json
{
  "error_code": "E_INVALID_FORMAT",
  "message": "year_months 형식이 올바르지 않습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "YYYY-MM 형식을 사용하세요 (예: 2025-10)",
  "field": "year_months"
}
```

### 비고
- 캐시: Redis, TTL 30일
- 레이트리밋: 30 req/min
- 평균 응답시간: 100-200ms (캐시), 600-900ms (계산)

---

## 5. POST /api/v1/tokens/reward

**설명**: 리워디드 광고 SSV (Server-Side Verification)

### 요청

**Request Body**:
```json
{
  "network": "admob",
  "receipt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "u_123",
  "device_id": "d_abc",
  "ad_unit_id": "ca-app-pub-123"
}
```

**헤더**:
- `Idempotency-Key` (required): UUID v4

**스키마**:
```typescript
{
  network: "admob" | "unity" | "applovin";  // required
  receipt: string;                           // required, SSV 토큰
  user_id: string;                           // required
  device_id: string;                         // required
  ad_unit_id: string;                        // required
}
```

### 응답

**Status**: 200 OK

**Response Body**:
```json
{
  "success": true,
  "tokens_awarded": 2,
  "new_balance": 5,
  "cooldown_remaining_sec": 3600,
  "daily_remaining": 1,
  "next_eligible_at": "2025-10-07T11:30:45Z"
}
```

### 에러

**Status**: 409 Conflict
```json
{
  "error_code": "E_COOLDOWN_ACTIVE",
  "message": "광고 쿨다운 중입니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "1시간 후 다시 시도하세요",
  "cooldown_remaining_sec": 2345
}
```

**Status**: 403 Forbidden
```json
{
  "error_code": "E_DAILY_CAP_REACHED",
  "message": "일일 광고 시청 한도에 도달했습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "내일 다시 시도하세요",
  "daily_cap": 2,
  "reset_at": "2025-10-08T00:00:00Z"
}
```

### 비고
- 멱등성: Idempotency-Key 기반 (24시간 중복 방지)
- 보상: 광고 1회 = 2 chat_token
- 쿨다운: 1시간
- 일일 한도: 2회
- 레이트리밋: 10 req/min

---

## 6. POST /api/v1/tokens/consume

**설명**: 토큰 차감 (Deep 질문, 기능 사용)

### 요청

**Request Body**:
```json
{
  "user_id": "u_123",
  "amount": 1,
  "reason": "chat_deep",
  "metadata": {
    "message_id": "msg_456",
    "profile_id": "p_a3f2c1b9"
  }
}
```

**헤더**:
- `Idempotency-Key` (required): UUID v4

**스키마**:
```typescript
{
  user_id: string;          // required
  amount: number;           // required, 1-10
  reason: "chat_deep" | "chat_light" | "report_pdf" | "profile_save_temp";  // required
  metadata?: object;        // optional
}
```

### 응답

**Status**: 200 OK

**Response Body**:
```json
{
  "success": true,
  "consumed": 1,
  "new_balance": 4,
  "transaction_id": "tx_a3f2c1b9"
}
```

### 에러

**Status**: 403 Forbidden
```json
{
  "error_code": "E_INSUFFICIENT_TOKENS",
  "message": "토큰이 부족합니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "광고를 시청하거나 토큰팩을 구매하세요",
  "required": 1,
  "available": 0
}
```

### 비고
- 멱등성: Idempotency-Key 기반 (24시간 중복 방지)
- 레이트리밋: 20 req/min
- 평균 응답시간: 50-100ms

---

## 7. GET /api/v1/entitlements

**설명**: 사용자 권한 및 할당량 조회

### 요청

**Query Parameters**:
- `user_id` (string, required): 사용자 ID

**예시**:
```
GET /api/v1/entitlements?user_id=u_123
```

### 응답

**Status**: 200 OK

**Response Body**:
```json
{
  "user_id": "u_123",
  "plan": "free",
  "storage": {
    "limit": 5,
    "used": 3,
    "remaining": 2
  },
  "quota": {
    "light_daily_limit": 5,
    "light_daily_used": 3,
    "light_daily_remaining": 2,
    "light_reset_at": "2025-10-08T00:00:00Z",
    "deep_tokens": 4,
    "deep_monthly_quota": 0
  },
  "features": {
    "pdf_reports": false,
    "advanced_luck": false,
    "priority_support": false
  },
  "ads": {
    "eligible": true,
    "cooldown_remaining_sec": 0,
    "daily_remaining": 2,
    "next_eligible_at": "2025-10-07T10:30:45Z"
  }
}
```

### 에러

**Status**: 404 Not Found
```json
{
  "error_code": "E_USER_NOT_FOUND",
  "message": "사용자를 찾을 수 없습니다",
  "trace_id": "req_7f3a9b2c"
}
```

### 비고
- 캐시: 1분 (Redis)
- 레이트리밋: 60 req/min
- 평균 응답시간: 50-100ms

---

## 8. POST /api/v1/report/pdf

**설명**: PDF 리포트 생성 요청 (비동기 큐)

### 요청

**Request Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "type": "full",
  "options": {
    "include_luck": true,
    "include_twelve_stages": true,
    "theme": "modern"
  }
}
```

**스키마**:
```typescript
{
  profile_id: string;          // required
  type: "full" | "simple";     // required
  options?: {
    include_luck?: boolean;              // default: true
    include_twelve_stages?: boolean;     // default: true
    theme?: "classic" | "modern";        // default: "modern"
  }
}
```

### 응답

**Status**: 202 Accepted

**Response Body**:
```json
{
  "job_id": "job_a3f2c1b9",
  "status": "queued",
  "estimated_completion_sec": 30,
  "poll_url": "/api/v1/report/pdf/job_a3f2c1b9"
}
```

**Status**: 200 OK (job 완료 시 polling)
```json
{
  "job_id": "job_a3f2c1b9",
  "status": "completed",
  "pdf_url": "https://cdn.saju.example.com/reports/p_a3f2c1b9_20251007.pdf",
  "expires_at": "2025-10-14T10:30:45Z"
}
```

### 에러

**Status**: 403 Forbidden
```json
{
  "error_code": "E_QUOTA_EXCEEDED",
  "message": "PDF 리포트 생성 한도를 초과했습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "Pro 플랜은 월 1회 무료, 추가 생성은 IAP 구매 필요",
  "monthly_limit": 1,
  "used": 1
}
```

### 비고
- 비동기: 큐 시스템 (RabbitMQ/SQS)
- 평균 생성시간: 20-40초
- 레이트리밋: 5 req/hour
- 멱등성: profile_id + type 조합 (1시간 중복 방지)

---

## 9. POST /api/v1/profiles

**설명**: 사주 프로필 저장 (계산 후 저장)

### 요청

**Request Body**:
```json
{
  "user_id": "u_123",
  "name": "홍길동",
  "birth_dt_local": "2000-09-14T10:00:00",
  "timezone": "Asia/Seoul",
  "calendar_type": "solar",
  "unknown_hour": false,
  "zi_hour_mode": "default",
  "gender": "m",
  "location": "서울",
  "memo": "본인"
}
```

**스키마**:
```typescript
{
  user_id: string;             // required
  name: string;                // required, 1-50자
  birth_dt_local: string;      // required, ISO8601
  timezone: string;            // required, IANA
  calendar_type: "solar" | "lunar";  // required
  unknown_hour?: boolean;      // default: false
  zi_hour_mode?: "default" | "split_23" | "split_00";  // default: "default"
  gender?: "m" | "f" | null;
  location?: string;           // optional, max 100자
  memo?: string;               // optional, max 200자
  regional_correction_minutes?: number;  // optional
}
```

### 응답

**Status**: 201 Created

**Response Body**:
```json
{
  "profile_id": "p_a3f2c1b9",
  "user_id": "u_123",
  "name": "홍길동",
  "pillars": {
    "year": "庚辰",
    "month": "乙酉",
    "day": "乙亥",
    "hour": "辛巳"
  },
  "hash_key": "sha256:a3f2c1b9...",
  "created_at": "2025-10-07T10:30:45Z"
}
```

### 에러

**Status**: 403 Forbidden
```json
{
  "error_code": "E_STORAGE_LIMIT",
  "message": "프로필 저장 한도를 초과했습니다",
  "trace_id": "req_7f3a9b2c",
  "hint": "기존 프로필을 삭제하거나 Plus/Pro로 업그레이드하세요",
  "limit": 5,
  "used": 5
}
```

**Status**: 409 Conflict
```json
{
  "error_code": "E_DUPLICATE_PROFILE",
  "message": "동일한 사주가 이미 존재합니다",
  "trace_id": "req_7f3a9b2c",
  "existing_profile_id": "p_xyz123"
}
```

### 비고
- 중복 체크: hash_key 기반 (birth_dt + timezone + calendar_type)
- 레이트리밋: 20 req/min
- 평균 응답시간: 100-200ms

---

## 공통 컴포넌트

### 스키마

**Profile**:
```typescript
{
  profile_id: string;
  user_id: string;
  name: string;
  birth_dt_local: string;
  timezone: string;
  calendar_type: "solar" | "lunar";
  unknown_hour: boolean;
  zi_hour_mode: "default" | "split_23" | "split_00";
  gender: "m" | "f" | null;
  location: string | null;
  memo: string | null;
  pillars: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
  hash_key: string;
  created_at: string;
  updated_at: string;
}
```

**Entitlements**:
```typescript
{
  user_id: string;
  plan: "free" | "plus" | "pro";
  storage: {
    limit: number;
    used: number;
    remaining: number;
  };
  quota: {
    light_daily_limit: number;
    light_daily_used: number;
    light_daily_remaining: number;
    light_reset_at: string;
    deep_tokens: number;
    deep_monthly_quota: number;
  };
  features: {
    pdf_reports: boolean;
    advanced_luck: boolean;
    priority_support: boolean;
  };
  ads: {
    eligible: boolean;
    cooldown_remaining_sec: number;
    daily_remaining: number;
    next_eligible_at: string;
  };
}
```

**LuckAnnual**:
```typescript
{
  year: number;
  age: number;
  pillar: string;
  stem: string;
  branch: string;
  summary: string;
  forecast: {
    career: "대길" | "길" | "중길" | "평" | "주의" | "흉";
    wealth: "대길" | "길" | "중길" | "평" | "주의" | "흉";
    relationship: "대길" | "길" | "중길" | "평" | "주의" | "흉";
    health: "대길" | "길" | "중길" | "평" | "주의" | "흉";
  };
  key_events: string[];
}
```

**LuckMonthly**:
```typescript
{
  year_month: string;
  pillar: string;
  stem: string;
  branch: string;
  summary: string;
  good_days: Array<{
    date: string;
    reason: string;
    activities: string[];
  }>;
  caution_days: Array<{
    date: string;
    reason: string;
    avoid: string[];
  }>;
}
```

---

## 에러 코드 테이블

| 코드 | HTTP Status | 설명 | 해결 방법 |
|------|-------------|------|----------|
| `E_BAD_REQUEST` | 400 | 요청 형식 오류 | 요청 JSON 스키마 확인 |
| `E_INVALID_FORMAT` | 400 | 필드 형식 오류 | 필드 타입/형식 확인 |
| `E_INVALID_DATE` | 422 | 날짜 범위 초과 | 1900-2050년 범위 확인 |
| `E_UNAUTHORIZED` | 401 | 인증 실패 | Bearer 토큰 확인 |
| `E_FORBIDDEN` | 403 | 권한 없음 | 플랜/권한 확인 |
| `E_QUOTA_EXCEEDED` | 403 | 할당량 초과 | 광고/업그레이드/다음날 재시도 |
| `E_INSUFFICIENT_TOKENS` | 403 | 토큰 부족 | 광고/토큰팩 구매 |
| `E_STORAGE_LIMIT` | 403 | 저장 한도 초과 | 프로필 삭제 또는 업그레이드 |
| `E_NOT_FOUND` | 404 | 리소스 없음 | ID 확인 |
| `E_PROFILE_NOT_FOUND` | 404 | 프로필 없음 | profile_id 확인 또는 생성 |
| `E_USER_NOT_FOUND` | 404 | 사용자 없음 | user_id 확인 |
| `E_DUPLICATE_PROFILE` | 409 | 중복 프로필 | 기존 프로필 사용 |
| `E_CONFLICT` | 409 | 상태 충돌 | 리소스 상태 확인 |
| `E_COOLDOWN_ACTIVE` | 409 | 쿨다운 중 | 대기 후 재시도 |
| `E_DAILY_CAP_REACHED` | 403 | 일일 한도 도달 | 다음날 재시도 |
| `E_RATE_LIMIT` | 429 | 요청 제한 초과 | Retry-After 헤더 확인 |
| `E_UNPROCESSABLE` | 422 | 처리 불가 | 입력값 검증 |
| `E_SERVER` | 500 | 서버 오류 | 재시도 또는 지원팀 연락 |

---

## 부록

### A. 필드 제약 규칙

**시간/날짜**:
- `birth_dt_local`: ISO8601 형식 (`YYYY-MM-DDTHH:MM:SS`), 1900-2050년 범위
- `timezone`: IANA timezone database (예: `Asia/Seoul`, `America/New_York`)
- `year_month`: `YYYY-MM` 형식
- `date`: `YYYY-MM-DD` 형식

**열거형**:
- `calendar_type`: `solar` | `lunar`
- `zi_hour_mode`: `default` (기본) | `split_23` (23시 자시 분리) | `split_00` (00시 자시 분리)
- `gender`: `m` (남성) | `f` (여성) | `null` (미지정)
- `plan`: `free` | `plus` | `pro`
- `depth`: `auto` | `light` | `deep`

**숫자**:
- `regional_correction_minutes`: -60 ~ +60 (LMT 보정, 기본값: 자동 계산)
- `annual_years`: 1 ~ 20
- `monthly_months`: 1 ~ 24
- `tokens`: 1 ~ 10 (1회 차감량)

**문자열 길이**:
- `name`: 1-50자
- `message`: 1-500자
- `location`: 1-100자
- `memo`: 1-200자

### B. 특수 케이스 샘플

**시간 모름 케이스**:
```json
{
  "birth_dt_local": "2000-09-14T12:00:00",
  "unknown_hour": true,
  "zi_hour_mode": "default",
  "timezone": "Asia/Seoul",
  "calendar_type": "solar"
}
```
→ 시간을 12:00으로 설정하고 `unknown_hour: true` 플래그 사용

**야자시 (23시) 케이스**:
```json
{
  "birth_dt_local": "2000-09-14T23:30:00",
  "unknown_hour": false,
  "zi_hour_mode": "split_23",
  "timezone": "Asia/Seoul",
  "calendar_type": "solar"
}
```
→ 23시는 다음 날 자시로 처리 (day pillar +1)

**지역시 보정 케이스**:
```json
{
  "birth_dt_local": "2000-09-14T10:00:00",
  "timezone": "Asia/Seoul",
  "regional_correction_minutes": -32,
  "calendar_type": "solar"
}
```
→ 서울 LMT 보정 -32분 (126.978°E vs 135°E)

**음력 케이스**:
```json
{
  "birth_dt_local": "2000-08-16T10:00:00",
  "calendar_type": "lunar",
  "timezone": "Asia/Seoul"
}
```
→ 음력 2000년 8월 16일 → 양력 변환 후 계산

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2025-10-07 | 초안 작성 (9개 엔드포인트) |

---

**문서 끝**
