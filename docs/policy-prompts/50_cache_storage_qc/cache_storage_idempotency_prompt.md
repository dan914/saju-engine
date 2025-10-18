# 🧱 실행 프롬프트 — Cache · Storage · Idempotency v1.0

**ROLE**
너는 KO-first **플랫폼 엔지니어**다. **설명 금지**, **결정적 사양만** 출력한다.

**GOAL**
사주앱의 핵심 경로에 대한 **캐시 키/TTL/무결성 서명(RFC‑8785+SHA‑256)**, **오브젝트 스토리지 레이아웃**, **멱등·락·리트라이**, **DDL/스키마**, **품질검증(QC) 체크리스트**, **테스트 명세**를 한 문서로 산출한다.
출력물은 **표 + JSON 스키마 + DDL + 시퀀스 + 테스트**로 구성되어, 바로 코드화 가능해야 한다.

**SCOPE (엔드포인트별 적용)**
- `POST /api/v1/report/saju`  *(핵심 리포트; JSON+PDF 서명/저장)*
- `POST /api/v1/chat/send`    *(텍스트 응답; 멱등 옵션, 캐시 가능)*
- `POST /api/v1/luck/annual`  *(연운 캐시)*
- `POST /api/v1/luck/monthly` *(월운 캐시; 절기 경계 주의)*
- `POST /api/v1/tokens/reward` *(SSV; 멱등키 필수)*
- `POST /api/v1/tokens/consume`*(reserve/finalize/release 멱등)*
- `GET  /api/v1/entitlements`  *(짧은 TTL 캐시 가능)*

---

## OUTPUT ORDER (반드시 이 순서)
1) **캐시 계층 & 키/TTL 표**(서비스별 키 규칙/TTL/무효화 트리거/스토리지 클래스)
2) **Canonical JSON & 서명 규칙**(RFC‑8785, SHA‑256, `signatures.sha256`)
3) **오브젝트 스토리지 레이아웃**(JSON/PDF 경로 규칙, ETag/MD5, 보관/삭제 정책)
4) **멱등성/락/리트라이 정책**(키 스코프, 중복 처리, 분산락, 타임아웃)
5) **스키마**: CacheEnvelope, StorageIndex, IdempotencyRecord, LockLease(JSON Schema)
6) **DDL**(PostgreSQL/Redis 키스페이스/오브젝트 스토어 디렉토리 규칙)
7) **시퀀스 다이어그램**(report, chat, reward, consume)
8) **품질검증(QC) 체크리스트**(서명, evidence, policy 적용)
9) **테스트 명세**(단위/통합/경계)
10) **수용 기준(AC)**

---

## 1) 캐시 계층 & 키/TTL 표

### 1.1 레벨
- L1: 메모리(프로세스) · 초단위 TTL
- L2: Redis(클러스터) · 분 단위 TTL
- L3: 오브젝트 스토어(JSON 스냅샷/ PDF) · 버전/불변

### 1.2 키 규칙/TTL/무효화 (표)
| 영역 | Key 패턴 | TTL | 무효화 트리거 | 비고 |
|---|---|---:|---|---|
| **astro** 절기 | `astro:terms:{year}` | 365d | 데이터 리프레시 | CSV prewarm |
| **pillars** | `pillars:{profile_id}:{inputs_hash}` | 30d | 입력 변경(시간/zi/solar) | inputs_hash=RFC‑8785 hash |
| **analysis** | `analysis:{profile_id}:{pillars_sha}:{flags_hash}` | 30d | 정책 파일 버전 변경 | flags: climate/palace/combination |
| **luck:years** | `luck:years:{profile_id}:{YYYY}` | 365d | 정책/절기 데이터 변경 | 캐시 히트 우선 |
| **luck:months** | `luck:months:{profile_id}:{YYYY-MM}` | 30d | 절기 경계 월만 강제 갱신 | 입절±2일 주의 |
| **report:saju** | `report:saju:{profile_id}:{report_sha}` | 90d | 재생성/정책 메이저업 | L3 스냅샷 핸들 |
| **chat:send** | `chat:light:{profile_id}:{prompt_fp}` | 24h | 템플릿/가드 버전업 | Light만 기본 캐시 |
| **entitlements** | `ent:{user_id}` | 60s | 토큰/리워드 변동 | 강한 일관성 불필요 |
| **tokens:reward cooldown** | `reward:cooldown:{user_id}` | 60m | 성공 시 설정 | 일한도 별도키 |
| **tokens:reward dailycap** | `reward:daycap:{user_id}:{YYYYMMDD}` | 24h | 리셋 | 누적 카운트 |

---

## 2) Canonical JSON & 서명 규칙

- 정규화: **RFC‑8785**(키 정렬, 수치 표준화, UTF‑8, NaN 금지)
- 서명: `sha256(canonical_json_bytes)` → hex 64자 → `signatures.sha256`에 저장
- 서명 대상: `/report/saju` 최종 응답, `/chat/send` 최종 텍스트 래퍼, `/tokens/*` 응답
- 검증: 게이트웨이 레벨에서 **응답 서명 검증 후** 전송

**Schema: SignatureBlock**
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}
}
```

---

## 3) 오브젝트 스토리지 레이아웃

- **버킷**: `saju-{env}-{region}`
- **경로 규칙**:
  - JSON 스냅샷: `snapshots/report-saju/{profile_id}/{yyyy}/{mm}/r_{timestamp}_{sha8}.json`
  - PDF: `reports/pdf/{profile_id}/{yyyy}/{mm}/r_{timestamp}_{sha8}.pdf`
- **메타**: `Content-Type`, `Content-MD5`(ETag), `x-signature-sha256`
- **보관/삭제**: JSON/PDF 90일 기본, Pro 플랜은 1년
- **접근**: 사설 버킷 + 서명 URL(15분) 발급

**Schema: StorageIndex**
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["path","sha256","size","mime","created_at"],
  "properties":{
    "path":{"type":"string"},
    "sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"},
    "size":{"type":"integer","minimum":0},
    "mime":{"type":"string"},
    "created_at":{"type":"string","format":"date-time"},
    "etag":{"type":"string"},
    "signed_url":{"type":"string"}
  }
}
```

---

## 4) 멱등성/락/리트라이 정책

### 4.1 멱등 키 스코프
| 엔드포인트 | 키 필드 | 유니크 제약 | 만료 |
|---|---|---|---|
| `/tokens/reward` | `idempotency_key` | `(user_id, idempotency_key)` | 2d |
| `/tokens/consume` | `idempotency_key` | `(user_id, idempotency_key)` | 2d |
| `/report/saju` | `inputs_hash` | `(profile_id, inputs_hash)` | 30d |
| `/chat/send` | `prompt_fp` | `(profile_id, prompt_fp, depth)` | 24h |

### 4.2 분산 락(충돌 방지)
- **키**: `lock:{scope}:{hash}` / TTL=15s / 리뉴얼 허용
- **취득 실패 시**: 409 반환 또는 큐잉(선택)

**Schema: LockLease**
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["key","owner","ttl_ms","acquired_at"],
  "properties":{
    "key":{"type":"string"},
    "owner":{"type":"string"},
    "ttl_ms":{"type":"integer","minimum":1000},
    "acquired_at":{"type":"string","format":"date-time"}
  }
}
```

### 4.3 리트라이
- 네트워크/5xx/timeout → 지수 백오프(200ms, 400ms, 800ms 최대)
- 동일 입력 해시 30초 내 재시도 금지(쿨다운)

---

## 5) 스키마(JSON Schema)

### CacheEnvelope
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["cache_key","created_at","ttl_sec","payload","signatures"],
  "properties":{
    "cache_key":{"type":"string"},
    "created_at":{"type":"string","format":"date-time"},
    "ttl_sec":{"type":"integer","minimum":1},
    "payload":{"type":"object"},
    "source":{"type":"string","enum":["L1","L2","L3","MISS"]},
    "signatures":{"$ref":"#/defs/SignatureBlock"}
  },
  "defs":{
    "SignatureBlock":{"type":"object","properties":{"sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}}}
  }
}
```

### IdempotencyRecord
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["key","scope","status","first_seen_at"],
  "properties":{
    "key":{"type":"string","minLength":16},
    "scope":{"type":"string","enum":["reward","consume","report","chat"]},
    "status":{"type":"string","enum":["reserved","finalized","released","replayed"]},
    "first_seen_at":{"type":"string","format":"date-time"},
    "last_used_at":{"type":"string","format":"date-time"},
    "response_hash":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"}
  }
}
```

---

## 6) DDL (PostgreSQL) & Redis 키스페이스

### PostgreSQL
```sql
-- 캐시 인덱스(옵션: 관측 용도)
CREATE TABLE cache_index (
  cache_key TEXT PRIMARY KEY,
  ttl_sec INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  hits BIGINT NOT NULL DEFAULT 0,
  meta JSONB
);

-- 스토리지 색인
CREATE TABLE storage_index (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  sha256 CHAR(64) NOT NULL,
  size BIGINT NOT NULL,
  mime TEXT NOT NULL,
  etag TEXT,
  created_at TIMESTAMP NOT NULL,
  signed_url TEXT
);

-- 멱등
CREATE TABLE idempotency_keys (
  user_id TEXT NOT NULL,
  key TEXT NOT NULL,
  scope TEXT NOT NULL CHECK (scope IN ('reward','consume','report','chat')),
  status TEXT NOT NULL CHECK (status IN ('reserved','finalized','released','replayed')),
  response_hash CHAR(64),
  first_seen_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NOT NULL,
  PRIMARY KEY (user_id, key)
);
```

### Redis 키스페이스 예
```
L1:process:   (내부 메모리)
L2:redis:
  astro:terms:{year}
  pillars:{profile_id}:{inputs_hash}
  analysis:{profile_id}:{pillars_sha}:{flags_hash}
  luck:years:{profile_id}:{YYYY}
  luck:months:{profile_id}:{YYYY-MM}
  report:saju:{profile_id}:{report_sha}
  chat:light:{profile_id}:{prompt_fp}
  reward:cooldown:{user_id}
  reward:daycap:{user_id}:{YYYYMMDD}
  lock:{scope}:{hash}
```

---

## 7) 시퀀스 다이어그램(텍스트)

### 7.1 /report/saju
```
Client → Gateway: POST /report/saju(body)
Gateway → L2: GET pillars:{profile}:{inputs_hash} (MISS)
… services 호출 체인 …
Gateway: canonicalize → sha256 → signatures.sha256
Gateway → L3: PUT snapshots/report-saju/… (JSON)
Gateway → L2: SET report:saju:{profile}:{report_sha} (90d)
Gateway → Client: 200 {signatures.sha256, storage_index}
```

### 7.2 /chat/send (light)
```
Client → Gateway: POST /chat/send(light)
Gateway → L2: GET chat:light:{profile}:{prompt_fp} (HIT?) → 있으면 즉시 반환
없으면 템플릿→LLM→Post-Guard→canonicalize→서명→L2 SET(24h)
```

### 7.3 tokens/reward
```
Client → Gateway: POST /tokens/reward {idempotency_key}
Gateway → Redis: SETNX lock:reward:{hash} (15s)
  ↳ 실패 시 409
Gateway → idempotency_keys UPSERT (reserved)
Gateway → AdNet SSV verify → OK
Gateway → Ledger grant → response_hash 생성
Gateway → idempotency_keys UPDATE (finalized)
Gateway → Redis: DEL lock
Gateway → Client: 200 {granted, balance, signatures.sha256}
```

### 7.4 tokens/consume (reserve→finalize→release)
```
reserve: UPSERT(reserved) → balance check → 200
finalize: UPDATE(finalized) → 200
release: UPDATE(released) → 200
재호출: status 기준 noop/replayed
```

---

## 8) 품질검증(QC) 체크리스트

- ✓ canonical JSON 생성 후 동일 입력 → 동일 sha256 확인
- ✓ `/report/saju`에 `evidence.policies_applied[]` 포함
- ✓ 절기 경계(월운) ±2일 캐시 강제 갱신
- ✓ `unknown_hour:true`는 `pillars.hour=null`로 캐시 키에 반영
- ✓ `zi_hour_mode`, `use_solar_time`, `apply_combination_wuxing_change`는 `flags_hash`에 포함
- ✓ PDF 업로드 시 `Content-MD5`/`ETag` 검증

---

## 9) 테스트 명세

### 단위
- canonicalize 동일 입력 해시 불변
- CacheEnvelope 스키마 통과, TTL 만료 후 MISS
- idempotency_keys: reserve→finalize 멱등, release noop

### 통합
- `/report/saju` 두 번 호출 → 두 번째는 L2/L3 HIT
- `/luck/monthly` 절기 경계 월에서 캐시 새로고침
- `tokens/reward` 동일 idempotency_key 두 번 → 두 번째는 DUPLICATE
- `/chat/send(light)` 동일 prompt_fp → 캐시 HIT

### 경계
- 락 만료 전 재취득 실패(409)
- 장문 컨텍스트(>32k) 경로에서 캐시/스토리지 정상화

---

## 10) 수용 기준(AC)
- 키/TTL 표와 무효화 규칙이 완전하며, `flags_hash`/`inputs_hash` 정의가 포함될 것
- RFC‑8785 기반 서명 규칙과 SignatureBlock 스키마 포함
- 오브젝트 스토리지 경로/보관/서명 URL 정책 명시
- 멱등/락/리트라이 정책과 IdempotencyRecord/LockLease 스키마 포함
- DDL/Redis 키스페이스/시퀀스/QA·테스트 명세 완비

---

## NOW OUTPUT
위 형식을 그대로 따라 Cache·Storage·Idempotency 사양 문서를 생성하라. 불필요한 설명·주석 없이 표/JSON/DDL/시퀀스/테스트만 출력.
