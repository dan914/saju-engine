# 🔀 실행 프롬프트 — 모델 라우팅 정책(Model Routing Policy) v1.0

**ROLE**
너는 KO-first **플랫폼 라우팅 정책 엔지니어**다. **설명 금지**, **결정적 사양만** 출력한다.

**GOAL**
사주앱의 LLM 호출을 위한 **모델 카탈로그/라우팅 규칙/폴백/타임아웃/재시도/비용 가중치/관측 지표**를 한 문서로 산출한다.
출력물은 **표 + JSON 설정(config) + 의사코드 + 테스트 명세**로 구성되며, 바로 코드화 가능해야 한다.

**CONTEXT (고정)**
- 채팅 오케스트레이터 `/api/v1/chat/send`의 Depth: **Light(≤300t)** / **Deep(≤900t)** / *(옵션)* Report-style(채팅 내 소규모 리포트).
- 텍스트 생성은 **템플릿→LLM-polish**, 사실/수치/간지는 **엔진 결과**로만(LLM Guard v1 적용).
- 언어: `ko-KR` 우선.
- 네트워크/비용/지연 조건에 따라 **자동 폴백**.

---

## OUTPUT ORDER (반드시 이 순서)
1) **문서 헤더**(제목/버전/날짜/베이스URL/보안)
2) **Model Catalog 표** + **models.json(설정 JSON)**
3) **Routing Matrix 표**(Light/Deep/Report × 1차/2차/Backstop, 타임아웃·재시도·온도 등)
4) **Selection 의사코드**(입력→라우팅 결정→호출)
5) **Fallback/Retry 정책**(트리거·쿨다운·승격 금지 조건)
6) **비용·성능·품질 가중치 정의**(가중치 JSON + 예시 계산)
7) **안전/가드 연동 규칙**(LLM Guard v1과의 상호작용)
8) **관측/로그/메트릭 이벤트**(이벤트 키·라벨)
9) **A/B·Canary 규칙**(버킷·노출·롤백)
10) **테스트 명세**(단위/통합)
11) **수용 기준(AC)**

---

## 1) 문서 헤더(샘플 형식)
- 제목: *Model Routing Policy v1.0*
- 날짜: 2025-10-07 KST
- Base URL: `<PLACEHOLDER>`
- 인증: `Authorization: Bearer <token>`

---

## 2) Model Catalog

### 2.1 표
| id | provider | tier | ko_quality(1-5) | latency_tier(1-5) | price_weight | ctx_window | max_output_tokens | notes |
|---|---|---|---:|---:|---:|---:|---:|---|
| qwen-flash | Alibaba | fast | 4 | 5 | 0.25 | 32k | 512 | 저비용/한글 양호 |
| deepseek-chat | DeepSeek | fast | 4 | 5 | 0.2 | 32k | 512 | 초저비용/요약 강점 |
| gemini-2.5-pro | Google | balanced | 5 | 3 | 1.0 | 128k | 1024 | 긴 컨텍스트/서술 안정 |
| gpt-5 | OpenAI | premium | 5 | 2 | 2.0 | 200k | 1200 | 품질 백스톱 |
| (optional) local-mini | Local | dev | 2 | 5 | 0.05 | 8k | 256 | 오프라인 디버그용 |

> `price_weight`는 상대 가중치(실가격 아님). 라우팅 비용 함수에 사용.

### 2.2 설정 JSON — `models.json`
```json
{
  "models": [
    {"id":"qwen-flash","provider":"alibaba","price_weight":0.25,"ctx_window":32768,"max_output_tokens":512,"ko_quality":4,"latency_tier":5},
    {"id":"deepseek-chat","provider":"deepseek","price_weight":0.2,"ctx_window":32768,"max_output_tokens":512,"ko_quality":4,"latency_tier":5},
    {"id":"gemini-2.5-pro","provider":"google","price_weight":1.0,"ctx_window":131072,"max_output_tokens":1024,"ko_quality":5,"latency_tier":3},
    {"id":"gpt-5","provider":"openai","price_weight":2.0,"ctx_window":200000,"max_output_tokens":1200,"ko_quality":5,"latency_tier":2},
    {"id":"local-mini","provider":"local","price_weight":0.05,"ctx_window":8192,"max_output_tokens":256,"ko_quality":2,"latency_tier":5}
  ],
  "defaults": {
    "light": {"temperature":0.2,"top_p":1.0,"max_output_tokens":280,"timeout_ms":[3000,7000,10000]},
    "deep":  {"temperature":0.35,"top_p":1.0,"max_output_tokens":900,"timeout_ms":[8000,15000]},
    "report": {"temperature":0.35,"top_p":1.0,"max_output_tokens":1200,"timeout_ms":[12000]}
  }
}
```

---

## 3) Routing Matrix

| Depth/Type | 1차 | 2차(Fallback) | Backstop | 온도 | 타임아웃(계단) | 재시도 |
|---|---|---|---|---:|---|---|
| Light (≤300t) | qwen-flash or deepseek-chat | gemini-2.5-pro | gpt-5 | 0.2 | 3s → 7s → 10s | 네트워크 1회 |
| Deep (≤900t) | gemini-2.5-pro | gpt-5 | — | 0.35 | 8s → 15s | 네트워크 1회 |
| Report-style(채팅 내) | gemini-2.5-pro | gpt-5 | — | 0.35 | 12s | 0 |

**보조 규칙**:
- Light에서 Guard 정합성 실패시 즉시 상위 모델 승격 금지 → 먼저 템플릿 축약 후 동일 모델 1회 재시도.
- 지역/규정 이슈 발생 시 `local-mini`로 안전 메시지 생성(개발/드릴 전용).

---

## 4) Selection 의사코드

```python
function select_model(depth, intent, locale, guard_state, budgets):
  C = load(models.json)
  if depth == "light":
     primary = prefer_low_cost(["qwen-flash","deepseek-chat"], budgets)
     fallback = "gemini-2.5-pro"; backstop = "gpt-5"
     cfg = C.defaults.light
  else if depth == "deep":
     primary = "gemini-2.5-pro"; fallback = "gpt-5"; backstop = null
     cfg = C.defaults.deep
  else if depth == "report":
     primary = "gemini-2.5-pro"; fallback = "gpt-5"; cfg = C.defaults.report

  // ko 품질 가중
  if locale == "ko-KR" and ko_quality(primary) < 4:
     primary = "gemini-2.5-pro"

  // Guard 프리체크 실패 시 안전 템플릿으로 다운스케일
  if guard_state == "safe_notice":
     return ("qwen-flash", cfg with max_output_tokens=min(220, cfg.max_output_tokens))

  return (primary, cfg, fallback, backstop)
```

---

## 5) Fallback/Retry 정책

- **재시도 트리거**: 408/429/5xx/네트워크 오류/모델 타임아웃.
- **승격 금지 조건**: Post-Guard 정합성 위반(Consistency/Grounding) → 템플릿 축약 후 동일 모델 재시도 1회.
- **쿨다운**: 동일 모델 동일 입력 해시 30초 내 재시도 금지(멱등 방지).
- **백스톱 활성화**: Fallback 실패 + 중요도 high(Deep/Report)일 때만.
- **중단 기준**: 2회 실패 시 안전 응답(카드만 + 안내 문구).

---

## 6) 비용·성능·품질 가중치

### 함수
```
score = w_price * (1/price_weight) + w_latency * latency_tier + w_ko * ko_quality
```

- **기본**: `w_price=0.5`, `w_latency=0.2`, `w_ko=0.3`
- **예산 압박 모드**(월 누적 비용 초과): `w_price=0.7`, `w_latency=0.15`, `w_ko=0.15`
- **긴 문맥 모드**(컨텍스트 길이 ≥32k): force `gemini-2.5-pro` or `gpt-5`

### 설정 JSON — `routing_weights.json`
```json
{
  "weights": {
    "default": {"w_price":0.5,"w_latency":0.2,"w_ko":0.3},
    "budget": {"w_price":0.7,"w_latency":0.15,"w_ko":0.15}
  },
  "thresholds": {
    "budget_mode_monthly_cost_usd": 1000,
    "long_context_tokens": 32000
  }
}
```

---

## 7) 안전/가드 연동

- **Pre-Guard**: 금지 의도/민감 주제 감지 시 `mode="safe_notice"` → Light/저온도/짧은 토큰으로 강등.
- **Post-Guard**:
  - `GROUND_UNVERIFIED`/`CONSIST_MISMATCH` → 승격 금지, 템플릿 축약 후 동일 모델 재시도.
  - `SCOPE_RESTRICTED` → 차단 및 카드만.
- 모든 최종 텍스트는 `signatures.sha256` 포함.

---

## 8) 관측/로그/메트릭

### 이벤트 키:
- `route.decide(depth, model, weights, reason)`
- `route.fallback(from, to, cause)`
- `llm.request(model, input_tokens, max_output, timeout_ms)`
- `llm.response(latency_ms, output_tokens, finish_reason)`
- `guard.post.result(decision, issues[])`
- 비용 집계: `billing.sample(model, cost_estimate)`

### 지표:
- 성공률, p50/p95 지연, 평균 비용/호출, Guard 패치율, 승격률

---

## 9) A/B·Canary

- **버킷**: A: `qwen-flash` 우선, B: `deepseek-chat` 우선 (Light 전용), 50/50
- **기간**: 7일 롤링, KPI: 비용/호출, p95 지연, Guard 패치율
- **Canary**: 신규 모델 도입 시 5% → 25% → 100% 단계적 확대, 이상 시 즉시 롤백

---

## 10) 테스트 명세

### 단위
- `ko-KR` + Light → qwen/deepseek 중 하나 반환
- 긴 문맥(>32k) → gemini/gpt-5 강제 선택
- budget mode 활성화 시 가격 가중 반영 확인
- Guard `safe_notice` → Light/저온도 강등

### 통합
- Light 1차 타임아웃 → Fallback으로 성공
- Post-Guard Consistency 위반 → 동일 모델 템플릿 축약 재시도, 승격 금지 확인
- Deep 백스톱 gpt-5 경로 1건

---

## 11) 수용 기준(AC)
- Model Catalog 표 + `models.json`이 포함되어야 함
- Routing Matrix가 Light/Deep/Report 각각 1차/2차/Backstop를 명시
- Selection 의사코드와 Fallback/Retry 정책이 구체적이어야 함
- 비용·성능·품질 가중치와 설정 JSON이 포함되어야 함
- Guard 연동/관측/A-B/테스트 명세가 포함되어야 함

---

## NOW OUTPUT
위 형식을 그대로 따라 모델 라우팅 정책 문서를 생성하라. 불필요한 설명·주석 없이 표/JSON/의사코드/정책/테스트만 출력.
