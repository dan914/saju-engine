# 토큰/권한/리워디드 광고 시스템 사양 v1.0

**Version:** 1.0
**Date:** 2025-10-07 KST
**Scope:** Entitlements, Token Ledger, Rewarded Ads (SSV)

사주 앱의 수익 모델 (Free/Plus/Pro), 토큰 경제 (reserve→finalize→release), 리워디드 광고 서버 검증 시스템의 완전한 사양.

---

## 1. 플랜 매트릭스

### 1.1 플랜별 권한

| 플랜 | 저장 한도 | Light/일 | Deep/일(기본) | Deep/월(총) | 광고 보상 | PDF/월 | 비고 |
|------|-----------|----------|--------------|------------|----------|--------|------|
| **Free** | 5명 | 5회 | 1회 | 0회 | +2토큰 · 일2회 · 60분쿨 | 0권 | 배너 최소, 리워디드 중심 |
| **Plus** | 30명 | 무제한 | 5회 | 30회 | 불필요 | 0권 | 광고 제거 |
| **Pro** | 무제한* | 무제한 | 무제한* | 무제한* | 불필요 | 1권 | *공정사용 정책 적용 |

**주요 특징:**
- **무제한**: -1로 표시 (예: `light_daily: -1`)
- **공정사용**: Pro 플랜은 과도 사용 시 제한 가능 (명시적 경고 후)
- **Deep 차감 순서**: daily → monthly → chat_token_balance

### 1.2 JSON 설정 (plans.json)

```json
{
  "version": "1.0",
  "plans": {
    "free": {
      "storage_limit": 5,
      "light_daily": 5,
      "deep_daily_base": 1,
      "deep_monthly_quota": 0,
      "reward": {
        "tokens_per_ad": 2,
        "daily_cap": 2,
        "cooldown_min": 60
      },
      "pdf_per_month": 0
    },
    "plus": {
      "storage_limit": 30,
      "light_daily": -1,
      "deep_daily_base": 5,
      "deep_monthly_quota": 30,
      "reward": null,
      "pdf_per_month": 0
    },
    "pro": {
      "storage_limit": -1,
      "light_daily": -1,
      "deep_daily_base": -1,
      "deep_monthly_quota": -1,
      "reward": null,
      "pdf_per_month": 1,
      "fair_use_note": "과도 사용 시 제한 가능 (명시적 경고 후)"
    }
  },
  "signature": {
    "sha256": "..."
  }
}
```

---

## 2. 토큰 상태 머신

### 2.1 상태 전이

```
IDLE
  ↓ (사용자 Deep 요청)
RESERVE (deep_daily_left-- or deep_monthly_left-- or chat_token_balance--)
  ↓ (LLM 처리 성공)
FINALIZE (확정)
  ↓
IDLE

RESERVE
  ↓ (LLM 처리 실패/취소)
RELEASE (복원: deep_daily_left++ or ...)
  ↓
IDLE
```

**상태 정의:**
- **IDLE**: 대기 상태
- **RESERVE**: 토큰 예약 (임시 차감)
- **FINALIZE**: 토큰 확정 (최종 소비)
- **RELEASE**: 토큰 복원 (예약 취소)

### 2.2 리셋 규칙

**일일 리셋 (매일 00:00 로컬 타임존):**
```python
# 매일 자정
entitlements.light_daily_left = plan.light_daily
entitlements.deep_daily_left = plan.deep_daily_base
```

**월간 리셋 (매월 1일 00:00 로컬 타임존):**
```python
# 매월 1일
entitlements.deep_monthly_left = plan.deep_monthly_quota
```

**리셋 시 기존 잔여량 무시** (이월 불가)

### 2.3 차감 순서 (Deep 요청 시)

```python
def consume_deep_token(entitlements):
    # 우선순위 1: 일일 할당량
    if entitlements.deep_daily_left > 0:
        entitlements.deep_daily_left -= 1
        return "daily"

    # 우선순위 2: 월간 할당량
    if entitlements.deep_monthly_left > 0:
        entitlements.deep_monthly_left -= 1
        return "monthly"

    # 우선순위 3: 토큰 잔액
    if entitlements.chat_token_balance > 0:
        entitlements.chat_token_balance -= 1
        return "balance"

    # 모두 소진 → Upsell
    return "upsell"
```

### 2.4 에러 시나리오

**Case 1: reserve 성공 후 네트워크 단절**
- 클라이언트: 동일 `idempotency_key`로 재시도
- 서버: 멱등성 보장 → 기존 reserve 상태 반환 (no-op)

**Case 2: finalize 중복 호출**
- 이미 finalize 완료 → `status: "noop"` 반환

**Case 3: release 전에 finalize 완료**
- `release` 요청 → `status: "noop"` 반환 (이미 확정됨)

**Case 4: reserve 시점에 잔액 부족**
- HTTP 200 + `status: "upsell"` 응답
- `upsell.reason: "no_deep_tokens"`

---

## 3. SSV 시퀀스 (Server-Side Verification)

### 3.1 플로우 다이어그램

```
[1] User → App(더보기 탭): "광고 보고 토큰 얻기" 버튼 클릭
[2] App → Ad SDK: showRewardedAd()
[3] Ad SDK → AdNetwork: requestAd(placement_id)
[4] AdNetwork → Ad SDK: adFilled(ad_creative)
[5] [사용자 광고 시청 완료 - 15초+]
[6] Ad SDK → App: onRewarded(client_receipt)
[7] App → Gateway: POST /api/v1/tokens/reward
    {
      "network": "admob",
      "receipt": "eyJhbGc...",  # opaque JWT
      "idempotency_key": "uuid-v4"
    }
[8] Gateway → AdNetwork SSV Endpoint: verify(receipt, user_id, device_id, ts, signature)
[9] AdNetwork → Gateway: HTTP 200 {status: "verified", reward_id: "..."}
[10] Gateway → Ledger: grant_tokens(user_id, amount=2, idem_key)
[11] Ledger → Gateway: new_balance
[12] Gateway → App: HTTP 200
    {
      "granted": 2,
      "balance": 15,
      "cooldown_sec": 3600,
      "daily_remaining": 1,
      "signatures": {"sha256": "..."}
    }
```

### 3.2 실패 분기

**[8] SSV 검증 실패:**
- **서명 불일치**: `E_SSV_INVALID` (HTTP 400)
- **시간 만료**: `ts` ± 300초 초과 → `E_SSV_EXPIRED` (HTTP 400)
- **중복 영수증**: `receipt_hash` 이미 존재 → `E_SSV_DUPLICATE` (HTTP 409)

**[10] Ledger 중복:**
- `(user_id, idempotency_key)` UNIQUE 제약 위반 → 기존 grant 결과 반환 (멱등성)

**[7] 쿨다운/일한도 위반:**
- 쿨다운 60분 미경과 → `E_REWARD_COOLDOWN` (HTTP 429)
- 일 2회 한도 초과 → `E_REWARD_DAILY_CAP` (HTTP 429)

---

## 4. API 스키마 (JSON Schema draft-2020-12)

### 4.1 GET /api/v1/entitlements

**Request:** 없음 (Authorization 헤더로 user 식별)

**Response Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/entitlements_v1.schema.json",
  "title": "EntitlementsResponse",
  "type": "object",
  "required": [
    "plan",
    "storage_limit",
    "stored",
    "light_daily_left",
    "deep_daily_left",
    "deep_monthly_left",
    "chat_token_balance"
  ],
  "properties": {
    "plan": {
      "type": "string",
      "enum": ["free", "plus", "pro"],
      "description": "현재 플랜"
    },
    "storage_limit": {
      "type": "integer",
      "description": "프로필 저장 한도 (-1 = 무제한)"
    },
    "stored": {
      "type": "integer",
      "minimum": 0,
      "description": "현재 저장된 프로필 수"
    },
    "light_daily_left": {
      "type": "integer",
      "description": "오늘 남은 Light 채팅 횟수 (-1 = 무제한)"
    },
    "deep_daily_left": {
      "type": "integer",
      "description": "오늘 남은 Deep 일일 할당량 (-1 = 무제한)"
    },
    "deep_monthly_left": {
      "type": "integer",
      "description": "이번 달 남은 Deep 월간 할당량 (-1 = 무제한)"
    },
    "chat_token_balance": {
      "type": "integer",
      "minimum": 0,
      "description": "보유 chat_token 잔액 (광고/구매로 획득)"
    },
    "pdf_credits": {
      "type": "integer",
      "minimum": 0,
      "description": "남은 PDF 생성 크레딧"
    },
    "reward": {
      "type": "object",
      "description": "광고 보상 정보 (Free 플랜만)",
      "properties": {
        "eligible": {
          "type": "boolean",
          "description": "광고 시청 가능 여부"
        },
        "cooldown_sec": {
          "type": "integer",
          "minimum": 0,
          "description": "쿨다운 남은 시간 (초)"
        },
        "daily_remaining": {
          "type": "integer",
          "minimum": 0,
          "description": "오늘 남은 광고 시청 횟수"
        }
      }
    }
  }
}
```

**Response Example:**
```json
{
  "plan": "free",
  "storage_limit": 5,
  "stored": 3,
  "light_daily_left": 2,
  "deep_daily_left": 0,
  "deep_monthly_left": 0,
  "chat_token_balance": 4,
  "pdf_credits": 0,
  "reward": {
    "eligible": true,
    "cooldown_sec": 0,
    "daily_remaining": 2
  }
}
```

---

### 4.2 POST /api/v1/tokens/reward

**Request Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/tokens_reward_request_v1.schema.json",
  "title": "TokensRewardRequest",
  "type": "object",
  "required": ["network", "receipt", "idempotency_key"],
  "properties": {
    "network": {
      "type": "string",
      "enum": ["admob", "ironsource", "unity", "applovin"],
      "description": "광고 네트워크"
    },
    "receipt": {
      "type": "string",
      "minLength": 16,
      "description": "광고 SDK가 반환한 opaque 영수증 (JWT 등)"
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 16,
      "description": "멱등성 키 (UUID v4 권장)"
    }
  },
  "additionalProperties": false
}
```

**Request Example:**
```json
{
  "network": "admob",
  "receipt": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/tokens_reward_response_v1.schema.json",
  "title": "TokensRewardResponse",
  "type": "object",
  "required": ["granted", "balance", "cooldown_sec", "daily_remaining", "signatures"],
  "properties": {
    "granted": {
      "type": "integer",
      "minimum": 0,
      "description": "이번 요청으로 지급된 토큰 (멱등 재시도 시 0)"
    },
    "balance": {
      "type": "integer",
      "minimum": 0,
      "description": "현재 chat_token_balance"
    },
    "cooldown_sec": {
      "type": "integer",
      "minimum": 0,
      "description": "다음 광고 시청까지 남은 시간 (초)"
    },
    "daily_remaining": {
      "type": "integer",
      "minimum": 0,
      "description": "오늘 남은 광고 시청 횟수"
    },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$",
          "description": "RFC-8785 canonical JSON SHA-256"
        }
      }
    }
  }
}
```

**Response Example (성공):**
```json
{
  "granted": 2,
  "balance": 6,
  "cooldown_sec": 3600,
  "daily_remaining": 1,
  "signatures": {
    "sha256": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a"
  }
}
```

**Response Example (쿨다운 위반, HTTP 429):**
```json
{
  "error": {
    "code": "E_REWARD_COOLDOWN",
    "message": "광고 시청 쿨다운이 아직 남았습니다. 45분 후 다시 시도하세요.",
    "cooldown_sec": 2700,
    "retry_after": 2700
  }
}
```

---

### 4.3 POST /api/v1/tokens/consume

**Request Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/tokens_consume_request_v1.schema.json",
  "title": "TokensConsumeRequest",
  "type": "object",
  "required": ["op", "reason", "idempotency_key"],
  "properties": {
    "op": {
      "type": "string",
      "enum": ["reserve", "finalize", "release"],
      "description": "토큰 연산 (reserve: 예약, finalize: 확정, release: 복원)"
    },
    "reason": {
      "type": "string",
      "enum": ["chat_deep", "report_pdf"],
      "description": "소비 사유"
    },
    "amount": {
      "type": "integer",
      "minimum": 1,
      "default": 1,
      "description": "소비할 토큰 수량 (기본 1)"
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 16,
      "description": "멱등성 키 (reserve/finalize/release 공통)"
    }
  },
  "additionalProperties": false
}
```

**Request Example (reserve):**
```json
{
  "op": "reserve",
  "reason": "chat_deep",
  "amount": 1,
  "idempotency_key": "7c9e6679-7425-40de-944b-e07f1b45c113"
}
```

**Request Example (finalize):**
```json
{
  "op": "finalize",
  "reason": "chat_deep",
  "idempotency_key": "7c9e6679-7425-40de-944b-e07f1b45c113"
}
```

**Response Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/tokens_consume_response_v1.schema.json",
  "title": "TokensConsumeResponse",
  "type": "object",
  "required": ["status", "balance", "deep_daily_left", "deep_monthly_left"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["reserved", "finalized", "released", "noop", "upsell"],
      "description": "토큰 상태"
    },
    "balance": {
      "type": "integer",
      "minimum": 0,
      "description": "현재 chat_token_balance"
    },
    "deep_daily_left": {
      "type": "integer",
      "description": "남은 일일 Deep 할당량"
    },
    "deep_monthly_left": {
      "type": "integer",
      "description": "남은 월간 Deep 할당량"
    },
    "signatures": {
      "type": "object",
      "properties": {
        "sha256": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$"
        }
      }
    }
  }
}
```

**Response Example (reserve 성공):**
```json
{
  "status": "reserved",
  "balance": 4,
  "deep_daily_left": 0,
  "deep_monthly_left": 29,
  "signatures": {
    "sha256": "5bdc0b7b2a1d0f3a8e2a7e5cc0e6ff9f3f2c1d5e0b9a7d6c4f1a2b3c4d5e6f70"
  }
}
```

**Response Example (finalize 성공):**
```json
{
  "status": "finalized",
  "balance": 4,
  "deep_daily_left": 0,
  "deep_monthly_left": 29,
  "signatures": {
    "sha256": "e3c1abf0e5a2d9c48b1a0f2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8090a1b2c3"
  }
}
```

**Response Example (upsell, HTTP 200):**
```json
{
  "status": "upsell",
  "balance": 0,
  "deep_daily_left": 0,
  "deep_monthly_left": 0,
  "upsell": {
    "show": true,
    "reason": "no_deep_tokens",
    "options": ["watch_ad", "buy_tokens", "subscribe_plus"]
  }
}
```

---

## 5. Ledger/DB 스키마

### 5.1 entitlements (사용자 권한)

```sql
CREATE TABLE entitlements (
  user_id TEXT PRIMARY KEY,
  plan TEXT NOT NULL CHECK (plan IN ('free', 'plus', 'pro')),
  storage_limit INTEGER NOT NULL,
  stored INTEGER NOT NULL DEFAULT 0,
  light_daily_left INTEGER NOT NULL,
  deep_daily_left INTEGER NOT NULL,
  deep_monthly_left INTEGER NOT NULL,
  chat_token_balance INTEGER NOT NULL DEFAULT 0,
  pdf_credits INTEGER NOT NULL DEFAULT 0,
  last_daily_reset_at TIMESTAMP NOT NULL,
  last_monthly_reset_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  INDEX idx_plan (plan),
  INDEX idx_updated (updated_at)
);
```

**필드 설명:**
- `user_id`: 사용자 식별자 (PK)
- `plan`: free/plus/pro
- `storage_limit`: 프로필 저장 한도 (-1 = 무제한)
- `stored`: 현재 저장된 프로필 수
- `light_daily_left`: 일일 Light 채팅 잔여량
- `deep_daily_left`: 일일 Deep 할당량 잔여
- `deep_monthly_left`: 월간 Deep 할당량 잔여
- `chat_token_balance`: 토큰 잔액 (광고/구매로 획득)
- `pdf_credits`: PDF 생성 크레딧
- `last_daily_reset_at`: 마지막 일일 리셋 시간
- `last_monthly_reset_at`: 마지막 월간 리셋 시간

### 5.2 tokens_ledger (토큰 원장)

```sql
CREATE TABLE tokens_ledger (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('grant', 'reserve', 'finalize', 'release', 'consume_refund')),
  amount INTEGER NOT NULL,
  reason TEXT,
  idempotency_key TEXT NOT NULL,
  balance_after INTEGER NOT NULL,
  meta JSONB,
  created_at TIMESTAMP NOT NULL,
  UNIQUE (user_id, idempotency_key),
  INDEX idx_user_created (user_id, created_at DESC),
  INDEX idx_idem (idempotency_key)
);
```

**필드 설명:**
- `id`: 레코드 ID (UUID)
- `user_id`: 사용자 식별자
- `type`: 원장 유형
  - `grant`: 토큰 지급 (광고/구매)
  - `reserve`: 토큰 예약 (임시 차감)
  - `finalize`: 토큰 확정 (최종 소비)
  - `release`: 토큰 복원 (예약 취소)
  - `consume_refund`: 환불 (에러/취소 시)
- `amount`: 변동량 (양수/음수)
- `reason`: 사유 (chat_deep, report_pdf 등)
- `idempotency_key`: 멱등성 키
- `balance_after`: 변동 후 잔액
- `meta`: 추가 메타데이터 (JSON)

**멱등성 보장:**
- `UNIQUE (user_id, idempotency_key)` 제약
- 중복 요청 시 기존 레코드 반환

### 5.3 ad_rewards (광고 보상 영수증)

```sql
CREATE TABLE ad_rewards (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  network TEXT NOT NULL CHECK (network IN ('admob', 'ironsource', 'unity', 'applovin')),
  receipt_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'verified', 'rejected', 'duplicate')),
  idempotency_key TEXT NOT NULL,
  ssv_response JSONB,
  created_at TIMESTAMP NOT NULL,
  verified_at TIMESTAMP,
  UNIQUE (network, receipt_hash),
  UNIQUE (user_id, idempotency_key),
  INDEX idx_user_created (user_id, created_at DESC),
  INDEX idx_receipt (receipt_hash)
);
```

**필드 설명:**
- `id`: 레코드 ID (UUID)
- `user_id`: 사용자 식별자
- `network`: 광고 네트워크
- `receipt_hash`: 영수증 SHA-256 해시
- `status`: 검증 상태
  - `pending`: 검증 대기
  - `verified`: 검증 완료
  - `rejected`: 검증 실패
  - `duplicate`: 중복 영수증
- `idempotency_key`: 멱등성 키
- `ssv_response`: SSV 응답 (JSON)
- `verified_at`: 검증 완료 시간

**중복 방지:**
- `UNIQUE (network, receipt_hash)`: 동일 영수증 재사용 차단
- `UNIQUE (user_id, idempotency_key)`: 동일 사용자 중복 요청 차단

---

## 6. 레이트리밋/쿨다운/일한도

### 6.1 규칙표

| 항목 | 규칙 | 기본값 | 플랜 예외 |
|------|------|--------|----------|
| **광고 쿨다운** | 최근 성공 이후 X분 전엔 거절 | 60분 | Free 전용 |
| **광고 일한도** | 일 최대 N회 성공 | 2회 | Free 전용 |
| **reserve RPS** | 초당 요청 제한 (user) | 10 rps | 전체 |
| **entitlements RPS** | 초당 요청 제한 (user) | 5 rps | 전체 |
| **reward RPS** | 초당 요청 제한 (user) | 3 rps | Free 전용 |

### 6.2 쿨다운 계산

```python
def check_reward_cooldown(user_id: str) -> tuple[bool, int]:
    """
    광고 보상 쿨다운 검사
    Returns: (eligible, cooldown_sec)
    """
    last_reward = get_last_reward(user_id)
    if not last_reward:
        return True, 0

    elapsed = now() - last_reward.verified_at
    cooldown_min = 60  # plans.json에서 로드
    cooldown_sec = cooldown_min * 60

    if elapsed < cooldown_sec:
        remaining = cooldown_sec - elapsed
        return False, remaining

    return True, 0
```

### 6.3 일한도 검사

```python
def check_reward_daily_cap(user_id: str) -> tuple[bool, int]:
    """
    광고 보상 일한도 검사
    Returns: (eligible, daily_remaining)
    """
    today_start = get_today_start()
    today_count = count_rewards_since(user_id, today_start)
    daily_cap = 2  # plans.json에서 로드

    if today_count >= daily_cap:
        return False, 0

    return True, daily_cap - today_count
```

---

## 7. 부정 방지 체크리스트

### 7.1 SSV 서명 검증

**AdMob SSV 예시:**
```python
import jwt
import requests

def verify_admob_ssv(receipt: str, user_id: str) -> dict:
    """
    AdMob SSV 검증
    """
    # 1. JWT 디코딩 (공개키 필요)
    try:
        payload = jwt.decode(
            receipt,
            ADMOB_PUBLIC_KEY,
            algorithms=["RS256"],
            audience="saju-app"
        )
    except jwt.InvalidSignatureError:
        raise ValueError("E_SSV_INVALID")
    except jwt.ExpiredSignatureError:
        raise ValueError("E_SSV_EXPIRED")

    # 2. 시간 유효성 (±300초)
    ts = payload.get("iat")
    if abs(now() - ts) > 300:
        raise ValueError("E_SSV_EXPIRED")

    # 3. user_id 일치 검사
    if payload.get("user_id") != user_id:
        raise ValueError("E_SSV_INVALID")

    return payload
```

**IronSource SSV 예시:**
```python
def verify_ironsource_ssv(receipt: str, user_id: str) -> dict:
    """
    IronSource SSV 검증 (서버 콜백)
    """
    # IronSource는 서버→서버 콜백 방식
    # Gateway가 콜백 엔드포인트를 노출
    # receipt는 콜백 파라미터의 서명 검증에 사용

    params = parse_callback_params(receipt)
    signature = params.get("signature")
    secret = IRONSOURCE_SECRET_KEY

    computed_sig = hmac.sha256(
        secret,
        f"{params['appKey']}{user_id}{params['timestamp']}{params['eventId']}"
    ).hexdigest()

    if signature != computed_sig:
        raise ValueError("E_SSV_INVALID")

    return params
```

### 7.2 영수증 중복 차단

```python
def check_receipt_duplicate(network: str, receipt: str) -> bool:
    """
    영수증 중복 검사
    """
    receipt_hash = hashlib.sha256(receipt.encode()).hexdigest()

    existing = db.query("""
        SELECT id FROM ad_rewards
        WHERE network = ? AND receipt_hash = ?
    """, network, receipt_hash)

    return existing is not None
```

### 7.3 디바이스/세션 제한

**수집 정보:**
- `device_id`: 고유 디바이스 식별자
- `ip_address`: 요청 IP
- `platform`: iOS/Android
- `app_version`: 앱 버전
- `session_id`: 세션 ID

**비정상 패턴 감지:**
```python
def detect_fraud_pattern(user_id: str, device_id: str) -> bool:
    """
    부정 사용 패턴 감지
    """
    # 1. 짧은 시간 내 다수 디바이스
    devices_1h = count_distinct_devices(user_id, hours=1)
    if devices_1h > 3:
        return True

    # 2. IP 변경 빈도
    ips_1d = count_distinct_ips(user_id, days=1)
    if ips_1d > 5:
        return True

    # 3. 루트/탈옥 디바이스
    if is_rooted(device_id):
        return True

    # 4. 과도한 시청 (일 10회+)
    rewards_1d = count_rewards(user_id, days=1)
    if rewards_1d > 10:
        return True

    return False
```

### 7.4 리스크 플래그

**플래그 유형:**
- `LOW`: 정상 사용
- `MEDIUM`: 의심 패턴 1~2개
- `HIGH`: 의심 패턴 3개+
- `BLOCKED`: 부정 사용 확정

**처리:**
```python
def flag_user_risk(user_id: str, risk_level: str):
    """
    사용자 리스크 플래그 설정
    """
    if risk_level == "HIGH":
        # 광고 보상 일시 차단
        disable_reward(user_id, duration_hours=24)
        notify_admin(user_id, "HIGH_RISK")

    if risk_level == "BLOCKED":
        # 계정 정지
        suspend_account(user_id)
        notify_admin(user_id, "FRAUD_CONFIRMED")
```

---

## 8. 테스트 명세

### 8.1 단위 테스트

**test_token_reserve_finalize:**
```python
def test_reserve_finalize():
    """reserve → finalize 플로우"""
    user = create_test_user(plan="free", deep_daily_left=1)
    idem_key = "test-idem-001"

    # 1. reserve
    res1 = consume_token(user.id, op="reserve", idem_key=idem_key)
    assert res1["status"] == "reserved"
    assert res1["deep_daily_left"] == 0

    # 2. finalize
    res2 = consume_token(user.id, op="finalize", idem_key=idem_key)
    assert res2["status"] == "finalized"
    assert res2["deep_daily_left"] == 0

    # 3. 원장 확인
    ledger = get_ledger(user.id, idem_key)
    assert ledger.type == "finalize"
```

**test_token_reserve_release:**
```python
def test_reserve_release():
    """reserve → release 플로우"""
    user = create_test_user(plan="free", deep_daily_left=1)
    idem_key = "test-idem-002"

    # 1. reserve
    res1 = consume_token(user.id, op="reserve", idem_key=idem_key)
    assert res1["deep_daily_left"] == 0

    # 2. release
    res2 = consume_token(user.id, op="release", idem_key=idem_key)
    assert res2["status"] == "released"
    assert res2["deep_daily_left"] == 1  # 복원됨

    # 3. 원장 확인
    ledger = get_ledger(user.id, idem_key)
    assert ledger.type == "release"
```

**test_idempotency:**
```python
def test_idempotency():
    """멱등성 검증"""
    user = create_test_user(plan="free", deep_daily_left=1)
    idem_key = "test-idem-003"

    # 1. 최초 reserve
    res1 = consume_token(user.id, op="reserve", idem_key=idem_key)
    assert res1["status"] == "reserved"

    # 2. 동일 키로 재시도
    res2 = consume_token(user.id, op="reserve", idem_key=idem_key)
    assert res2["status"] == "reserved"  # 멱등 성공
    assert res2["deep_daily_left"] == 0  # 잔액 불변
```

**test_reward_ssv_success:**
```python
def test_reward_ssv_success():
    """광고 보상 SSV 성공"""
    user = create_test_user(plan="free", chat_token_balance=0)
    receipt = generate_test_receipt("admob")
    idem_key = "test-reward-001"

    res = reward_token(user.id, network="admob", receipt=receipt, idem_key=idem_key)

    assert res["granted"] == 2
    assert res["balance"] == 2
    assert res["cooldown_sec"] == 3600
    assert res["daily_remaining"] == 1
```

**test_reward_duplicate:**
```python
def test_reward_duplicate():
    """영수증 중복 차단"""
    user = create_test_user(plan="free")
    receipt = generate_test_receipt("admob")
    idem_key1 = "test-reward-002"
    idem_key2 = "test-reward-003"

    # 1. 최초 성공
    res1 = reward_token(user.id, network="admob", receipt=receipt, idem_key=idem_key1)
    assert res1["granted"] == 2

    # 2. 동일 영수증 재사용
    with pytest.raises(APIError) as exc:
        reward_token(user.id, network="admob", receipt=receipt, idem_key=idem_key2)

    assert exc.value.code == "E_SSV_DUPLICATE"
```

### 8.2 통합 테스트

**test_free_user_flow:**
```python
def test_free_user_flow():
    """Free 사용자 전체 플로우"""
    user = create_test_user(plan="free")

    # 1. 초기 권한 확인
    ent = get_entitlements(user.id)
    assert ent["deep_daily_left"] == 1
    assert ent["chat_token_balance"] == 0

    # 2. Deep 1회 사용 (일일 할당량)
    idem1 = "flow-001"
    res1 = consume_token(user.id, op="reserve", idem_key=idem1)
    assert res1["status"] == "reserved"
    finalize_token(user.id, idem_key=idem1)

    # 3. Deep 2회 시도 (잔액 부족)
    idem2 = "flow-002"
    res2 = consume_token(user.id, op="reserve", idem_key=idem2)
    assert res2["status"] == "upsell"

    # 4. 광고 시청 (+2 토큰)
    receipt = generate_test_receipt("admob")
    reward_res = reward_token(user.id, network="admob", receipt=receipt, idem_key="flow-003")
    assert reward_res["granted"] == 2

    # 5. Deep 2회 재시도 (토큰 사용)
    res3 = consume_token(user.id, op="reserve", idem_key=idem2)
    assert res3["status"] == "reserved"
    assert res3["balance"] == 1  # 토큰 1 소진
```

**test_cooldown_enforcement:**
```python
def test_cooldown_enforcement():
    """쿨다운 강제 적용"""
    user = create_test_user(plan="free")

    # 1. 광고 1회 성공
    receipt1 = generate_test_receipt("admob")
    res1 = reward_token(user.id, network="admob", receipt=receipt1, idem_key="cd-001")
    assert res1["granted"] == 2
    assert res1["cooldown_sec"] == 3600

    # 2. 즉시 재시도 (쿨다운 위반)
    receipt2 = generate_test_receipt("admob")
    with pytest.raises(APIError) as exc:
        reward_token(user.id, network="admob", receipt=receipt2, idem_key="cd-002")

    assert exc.value.code == "E_REWARD_COOLDOWN"
    assert exc.value.cooldown_sec > 0
```

**test_daily_cap:**
```python
def test_daily_cap():
    """일한도 강제 적용"""
    user = create_test_user(plan="free")

    # 1. 광고 2회 성공 (일한도)
    for i in range(2):
        receipt = generate_test_receipt("admob")
        res = reward_token(user.id, network="admob", receipt=receipt, idem_key=f"cap-{i}")
        assert res["granted"] == 2

    # 2. 3회 시도 (일한도 초과)
    receipt3 = generate_test_receipt("admob")
    with pytest.raises(APIError) as exc:
        reward_token(user.id, network="admob", receipt=receipt3, idem_key="cap-3")

    assert exc.value.code == "E_REWARD_DAILY_CAP"
```

**test_network_failure_retry:**
```python
def test_network_failure_retry():
    """네트워크 장애 재시도"""
    user = create_test_user(plan="free", deep_daily_left=1)
    idem_key = "retry-001"

    # 1. reserve 성공
    res1 = consume_token(user.id, op="reserve", idem_key=idem_key)
    assert res1["status"] == "reserved"

    # 2. 네트워크 단절로 finalize 실패 (가정)
    # 클라이언트는 동일 idem_key로 재시도

    # 3. finalize 재시도 (멱등 성공)
    res2 = consume_token(user.id, op="finalize", idem_key=idem_key)
    assert res2["status"] == "finalized"
    assert res2["deep_daily_left"] == 0
```

---

## 9. 수용 기준 (Acceptance Criteria)

### 9.1 필수 요구사항

- [ ] **플랜 매트릭스**: Free/Plus/Pro 표 + JSON 설정 포함
- [ ] **토큰 상태 머신**: IDLE/RESERVE/FINALIZE/RELEASE 상태 정의
- [ ] **SSV 시퀀스**: 텍스트 다이어그램 포함 (Client→Gateway→AdNet→Ledger)
- [ ] **API 스키마**: 3개 API (entitlements, reward, consume) JSON Schema draft-2020-12 포함
- [ ] **Ledger 스키마**: DDL 유사 스키마 3개 테이블 (entitlements, tokens_ledger, ad_rewards)
- [ ] **멱등성**: `(user_id, idempotency_key)` UNIQUE 제약 명시
- [ ] **레이트리밋/쿨다운/일한도**: 규칙표 포함
- [ ] **부정 방지**: SSV 서명 검증, 영수증 중복, 디바이스/세션 제한, 리스크 플래그
- [ ] **테스트 명세**: 단위 6개, 통합 4개 케이스

### 9.2 검증 항목

**플랜 매트릭스:**
- [ ] Free: 저장 5, Light 5/일, Deep 1/일, 광고 +2토큰/일2회/60분쿨
- [ ] Plus: 저장 30, Light 무제한, Deep 30/월
- [ ] Pro: 모두 무제한, PDF 1/월, 공정사용 명시

**토큰 상태 머신:**
- [ ] reserve → finalize: 잔액 확정 차감
- [ ] reserve → release: 잔액 복원
- [ ] 멱등성: 동일 idem_key 재시도 시 no-op

**SSV:**
- [ ] 서명 검증 (RS256/HMAC)
- [ ] 시간 유효성 (±300초)
- [ ] 영수증 중복 차단 (receipt_hash UNIQUE)
- [ ] 쿨다운 60분, 일한도 2회 강제

**API:**
- [ ] GET /entitlements: plan/storage/light/deep/balance 반환
- [ ] POST /tokens/reward: granted/balance/cooldown_sec 반환
- [ ] POST /tokens/consume: status/balance/deep_left 반환

**테스트:**
- [ ] reserve → finalize 통과
- [ ] reserve → release 통과
- [ ] 멱등성 검증 통과
- [ ] SSV 성공/실패/중복 통과
- [ ] Free 사용자 플로우 통과
- [ ] 쿨다운/일한도 강제 통과

---

## 10. 구현 체크리스트

### Phase 1: 데이터 모델 (우선순위: 높음)
- [ ] entitlements 테이블 생성 (DDL)
- [ ] tokens_ledger 테이블 생성 (DDL)
- [ ] ad_rewards 테이블 생성 (DDL)
- [ ] plans.json 설정 파일 작성
- [ ] 일일/월간 리셋 크론잡 구현

### Phase 2: API 구현 (우선순위: 높음)
- [ ] GET /api/v1/entitlements 구현
- [ ] POST /api/v1/tokens/reward 구현 (SSV 통합)
- [ ] POST /api/v1/tokens/consume 구현 (reserve/finalize/release)
- [ ] 멱등성 미들웨어 구현
- [ ] RFC-8785 서명 생성/검증

### Phase 3: SSV 통합 (우선순위: 높음)
- [ ] AdMob SSV 검증 (JWT RS256)
- [ ] IronSource SSV 검증 (HMAC SHA256)
- [ ] Unity SSV 검증
- [ ] AppLovin SSV 검증
- [ ] 영수증 중복 차단

### Phase 4: 부정 방지 (우선순위: 중간)
- [ ] 디바이스/세션 로깅
- [ ] 비정상 패턴 감지
- [ ] 리스크 플래그 시스템
- [ ] 계정 정지 기능

### Phase 5: 테스트 (우선순위: 높음)
- [ ] 단위 테스트 6개 작성
- [ ] 통합 테스트 4개 작성
- [ ] 성능 테스트 (P95 <500ms)
- [ ] 부하 테스트 (1000 rps)

### Phase 6: 채팅 통합 (우선순위: 높음)
- [ ] /chat/send S0에서 GET /entitlements 호출
- [ ] /chat/send S7에서 POST /tokens/consume 호출
- [ ] Upsell 응답 생성 (no_deep_tokens)
- [ ] ads_suggest 필드 생성

---

**Version:** v1.0 (2025-10-07 KST)
**Last Updated:** 2025-10-07
**Maintainer:** Core Architects (Backend/Billing/Security)
