# ⚖️ 실행 프롬프트 — 토큰/권한(Entitlements) + 리워디드(SSV) 정책 v1.0

**버전**: v1.0
**날짜**: 2025-10-07 KST
**경로 권장**: `docs/policy-prompts/40_tokens_entitlements_ads/tokens_entitlements_ssv_prompt.md`

---

## ROLE
너는 **수익모델 운영 아키텍트 + 백엔드 설계자**다. 설명 대신 **결정적 산출물**만 출력한다.

## GOAL
다음 3가지를 하나의 결정적 사양으로 산출한다:
1) **권한/플랜(Entitlements)** — Free/Plus/Pro의 저장 한도, 라이트/딥 사용 한도
2) **토큰 경제(ledger)** — chat_token, report_credit, 일일/월간 리셋, 멱등/예약(reserve)→확정(finalize)→해제(release)
3) **리워디드 광고(SSV)** — 서버 검증, 쿨다운/일한도, 부정방지

## CONTEXT (고정 사실)
- 앱 4탭 구조(홈/채팅/더보기/사주계산), 메인 과금 단위는 **chat_token(딥=1)**.
- Free 기본: **저장 5명**, **Light 5회/일**, **Deep 기본 1회/일(설정값)**.
- 광고 1회 시청 SSV 성공 시 **+2 chat_token**, **일 최대 2회**, **쿨다운 60분(기본값)**.
- Plus: 광고 제거, Light 무제한, **Deep 30/월**, 저장 30명.
- Pro: Deep 공정사용 무제한, 저장 무제한, PDF/월 1권.
- `/chat/send`는 딥 요청 시 **S7 단계에서 reserve→성공 시 finalize, 실패 시 release**를 호출.

---

## OUTPUT ORDER (반드시 이 순서)
1) **플랜 매트릭스**(표 + JSON 설정 조각) — Free/Plus/Pro 파라미터화
2) **토큰 상태 머신** — 일일/월간 리셋, reserve/finalize/release, 오류 처리
3) **SSV 시퀀스 다이어그램(텍스트)** — Client↔AdSDK↔Gateway↔Ad Network SSV↔Ledger
4) **API 스키마** — `/entitlements`(GET), `/tokens/reward`(POST), `/tokens/consume`(POST) JSON Schema(draft-2020-12) + 예시
5) **Ledger/DB 스키마** — 테이블 정의(DDL 유사), 멱등키/유니크 제약
6) **레이트리밋/쿨다운/일한도** — 공식 규칙표
7) **부정 방지 체크리스트** — SSV 서명 검증, 디바이스/세션 제한, 중복감지
8) **테스트 명세** — 단위/통합 케이스 목록과 기대 결과
9) **수용 기준(AC)**

---

## 1) 플랜 매트릭스

### 표
| 플랜 | 저장 한도 | Light/일 | Deep/일(기본) | Deep/월(총) | 광고 보상 | PDF 포함 | 비고 |
|---|---:|---:|---:|---:|---:|---:|---|
| Free | 5 | 5 | 1 | 0 | +2/token · 일2회 · 60분 쿨다운 | 0 | 배너 최소, 리워디드 중심 |
| Plus | 30 | 무제한 | 5 | 30 | 필요없음 | 0 | 광고 제거 |
| Pro | 무제한 | 무제한 | 무제한* | 무제한* | 필요없음 | 1/월 | *공정사용 정책 |

### 구성(JSON 설정 조각; 코드에서 로딩)
```json
{
  "plans": {
    "free": {
      "storage_limit": 5,
      "light_daily": 5,
      "deep_daily_base": 1,
      "deep_monthly_quota": 0,
      "reward": {"tokens_per_ad": 2, "daily_cap": 2, "cooldown_min": 60}
    },
    "plus": {
      "storage_limit": 30,
      "light_daily": -1,
      "deep_daily_base": 5,
      "deep_monthly_quota": 30,
      "reward": null
    },
    "pro": {
      "storage_limit": -1,
      "light_daily": -1,
      "deep_daily_base": -1,
      "deep_monthly_quota": -1,
      "reward": null,
      "pdf_per_month": 1,
      "fair_use_note": "과도 사용시 제한 가능"
    }
  }
}
```

---

## 2) 토큰 상태 머신

- **일일 리셋(00:00 로컬)**: `light_daily_left = plan.light_daily`, `deep_daily_left = plan.deep_daily_base`.
- **월간 리셋(매월 1일 00:00)**: `deep_monthly_left = plan.deep_monthly_quota`.
- **소비 플로우(딥 요청)**
  1. `RESERVE`: `/tokens/consume(op=reserve, amount=1, reason="chat_deep", idempotency_key)`
  2. LLM 처리 성공 시 `FINALIZE`: `/tokens/consume(op=finalize, idem=...)`
  3. 실패/취소 시 `RELEASE`: `/tokens/consume(op=release, idem=...)`
- **차감 순서**: `deep_daily_left → deep_monthly_left → chat_token(balance)` (남는 경로 없음 시 Upsell)
- **에러 시나리오**:
  - `reserve` 성공 후 네트워크 단절 → 동일 `idempotency_key`로 재시도 시 **멱등 성공**
  - `finalize` 중복 호출 → **무효(no-op)**
  - `release` 전에 `finalize` 완료 → `release`는 **무효(no-op)**

---

## 3) SSV 시퀀스(텍스트 다이어그램)

```
User → App(더보기/모달): "광고 보고 토큰 얻기" 선택
App → Ad SDK: Show Rewarded
Ad SDK → AdNet: requestAd
AdNet → Ad SDK: adFilled
[사용자 시청 완료]
Ad SDK → App: client_receipt (opaque)
App → Gateway POST /tokens/reward {network, receipt, idempotency_key}
Gateway → AdNet SSV: verify(receipt, app_user, device, ts, signature)
AdNet → Gateway: {status: "verified", reward_id, signature_ok}
Gateway → Ledger: grant +2 tokens (idempotency_key unique)
Ledger → Gateway: new_balance
Gateway → App: {granted:2, cooldown_sec: 3600, daily_remaining:1, balance:new_balance}
```

- **실패 분기**: 서명 불일치/만료/중복 → 보상 거절(`E_SSV_INVALID`/`E_SSV_DUPLICATE`).

---

## 4) API 스키마 (JSON Schema, draft-2020-12)

### 4.1 `GET /api/v1/entitlements` (응답)
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["plan","storage_limit","stored","light_daily_left","deep_daily_left","deep_monthly_left"],
  "properties": {
    "plan": {"type":"string","enum":["free","plus","pro"]},
    "storage_limit": {"type":"integer"},
    "stored": {"type":"integer"},
    "light_daily_left": {"type":"integer"},
    "deep_daily_left": {"type":"integer"},
    "deep_monthly_left": {"type":"integer"},
    "chat_token_balance": {"type":"integer"},
    "pdf_credits": {"type":"integer"},
    "reward": {
      "type":"object",
      "properties": {
        "eligible": {"type":"boolean"},
        "cooldown_sec": {"type":"integer"},
        "daily_remaining": {"type":"integer"}
      }
    }
  }
}
```

### 4.2 `POST /api/v1/tokens/reward` (요청/응답)
요청:
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["network","receipt","idempotency_key"],
  "properties": {
    "network": {"type":"string","enum":["admob","ironsource","unity","applovin"]},
    "receipt": {"type":"string","minLength":16},
    "idempotency_key": {"type":"string","minLength":16}
  },
  "additionalProperties": false
}
```
응답:
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["granted","balance","cooldown_sec","daily_remaining","signatures"],
  "properties": {
    "granted": {"type":"integer"},
    "balance": {"type":"integer"},
    "cooldown_sec": {"type":"integer"},
    "daily_remaining": {"type":"integer"},
    "signatures": {"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  }
}
```

### 4.3 `POST /api/v1/tokens/consume` (요청/응답)
요청:
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["op","reason","idempotency_key"],
  "properties": {
    "op": {"type":"string","enum":["reserve","finalize","release"]},
    "reason": {"type":"string","enum":["chat_deep","report_pdf"]},
    "amount": {"type":"integer","minimum":1,"default":1},
    "idempotency_key": {"type":"string","minLength":16}
  },
  "additionalProperties": false
}
```
응답:
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["status","balance","deep_daily_left","deep_monthly_left"],
  "properties": {
    "status": {"type":"string","enum":["reserved","finalized","released","noop"]},
    "balance": {"type":"integer"},
    "deep_daily_left": {"type":"integer"},
    "deep_monthly_left": {"type":"integer"},
    "signatures": {"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  }
}
```

---

## 5) Ledger/DB 스키마 (DDL 유사)

```sql
-- 사용자 플랜/권한
CREATE TABLE entitlements (
  user_id TEXT PRIMARY KEY,
  plan TEXT NOT NULL CHECK (plan IN ('free','plus','pro')),
  storage_limit INTEGER NOT NULL,
  light_daily_left INTEGER NOT NULL,
  deep_daily_left INTEGER NOT NULL,
  deep_monthly_left INTEGER NOT NULL,
  chat_token_balance INTEGER NOT NULL DEFAULT 0,
  pdf_credits INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL
);

-- 토큰 원장
CREATE TABLE tokens_ledger (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('grant','reserve','finalize','release','consume_refund')),
  amount INTEGER NOT NULL,
  reason TEXT,
  idempotency_key TEXT NOT NULL,
  balance_after INTEGER NOT NULL,
  meta JSONB,
  created_at TIMESTAMP NOT NULL,
  UNIQUE (user_id, idempotency_key)
);

-- 광고 보상 영수증
CREATE TABLE ad_rewards (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  network TEXT NOT NULL,
  receipt_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','verified','rejected','duplicate')),
  idempotency_key TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  UNIQUE (network, receipt_hash),
  UNIQUE (user_id, idempotency_key)
);
```

- **원칙**: 모든 변동은 **원장 기반**(append-only). 실시간 잔액은 `balance_after`로 파생.
- **멱등**: `(user_id, idempotency_key)` 유니크로 중복 방지.

---

## 6) 레이트리밋/쿨다운/일한도

| 항목 | 규칙 | 기본값 |
|---|---|---|
| `/tokens/reward` 쿨다운 | 최근 성공 이후 X분 전엔 거절 | 60분 |
| `/tokens/reward` 일한도 | 일 최대 N회 성공 | 2회 |
| `/tokens/consume reserve` | 초당 요청 제한 | 10 rps/user |
| `/entitlements` 조회 | 초당 요청 제한 | 5 rps/user |

---

## 7) 부정 방지 체크리스트
1. **SSV 서명 검증**: 네트워크 공개키/시크릿으로 수검증. 시간유효성(`ts` ±300s).
2. **영수증 중복**: `receipt_hash` 유니크.
3. **디바이스/세션**: device_id / IP / 플랫폼 로그 병행 수집, 비정상 패턴 차단.
4. **쿨다운/일한도**: 서버 기준으로 적용(클라이언트 표시와 독립).
5. **리스크 플래그**: 과도 시청/짧은 체류시간/루프 의심 시 계정 제한.

---

## 8) 테스트 명세

- **단위**
  - `reserve→finalize` 잔액·일/월 카운터 정확 반영
  - `reserve→release` 시 잔액 불변
  - 멱등키 중복 호출 시 **noop**
  - 보상 SSV 성공/실패/중복

- **통합**
  - Free 사용자가 딥 2회: 1회(기본), 1회(광고 보상) → 성공
  - 쿨다운 위반 시 거절, 안내 값(cooldown_sec) 정확
  - 일한도 초과 시 `E_REWARD_DAILY_CAP`
  - 네트워크 장애 시 재시도 정책 검증

---

## 9) 수용 기준(AC)
- 플랜 매트릭스와 JSON 설정 조각이 포함되어야 함
- 상태 머신(리셋/소비)과 SSV 시퀀스가 명확해야 함
- 3개 API의 요청/응답 **JSON Schema**와 **예시**가 포함되어야 함
- DDL 유사 스키마와 멱등/유니크 규칙 명시
- 레이트리밋/쿨다운/일한도 표 제시, 부정 방지 리스트 포함
- 테스트 명세(단위/통합)가 존재

---

## NOW OUTPUT
위 요구사항을 모두 충족하는 **단일 사양 문서**를 생성하라. 설명이 아닌 **스펙/표/스키마/시퀀스/테스트**만 출력한다.
