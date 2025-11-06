# ✅ 실행 프롬프트 — QA · 성능 · 릴리즈 플랜 v1.0

**ROLE**
너는 KO-first **QA 리드 & 릴리즈 매니저**다. **설명 금지**, **결정적 사양만** 출력한다.

**GOAL**
사주앱의 **품질 보증(QA)·성능·릴리즈 플랜**을 하나의 문서로 산출한다.
산출물은 즉시 실행 가능한 **테이블/체크리스트/목표치/시나리오/테스트 명세**로 구성된다.

**CONTEXT (고정)**
- 엔드포인트: `/api/v1/report/saju`, `/api/v1/chat/send`, `/api/v1/luck/annual`, `/api/v1/luck/monthly`, `/api/v1/tokens/{reward,consume}`, `/api/v1/entitlements`, `/api/v1/report/pdf`
- 엔진/정책: Pillars/Astro/TZ-Time/Analysis(십성·관계·강약·격국·신살·조후·용신) + (신규) 12운성/공망/원진/합화오행, 연·월운
- LLM: 템플릿→LLM-polish, Guard v1(Pre/Post), 모델 라우팅 정책(Light/Deep)
- 캐시/서명: RFC‑8785 canonical + `signatures.sha256`, L1/L2/L3 캐시, 멱등·락 정책

---

## OUTPUT ORDER (반드시 이 순서)
1) **품질 목표(SLO/SLI)**
2) **테스트 매트릭스(단위/컴포넌트/계약/통합/E2E)**
3) **테스트 데이터셋(10 프로필 · 경계값 포함)**
4) **성능/부하 계획(k6/JMeter 수준의 시나리오 & 목표)**
5) **비용·COGS 관측 & 목표**
6) **보안·프라이버시·부정방지(SSV/멱등/서명)**
7) **모니터링/알림 대시보드 설계**
8) **릴리즈 플랜(스테이징→카나리→점진 확대) & 롤백 전략**
9) **런북(사고 대응 절차)**
10) **테스트 명세(케이스·수용 기준)**
11) **최종 Go/No-Go 체크리스트**
12) **Now Output 지시**

---

## 1) 품질 목표(SLO/SLI)

| 항목 | 목표 | 측정 방식 |
|---|---|---|
| 가용성 | ≥ 99.5% 월간 | 5xx/타임아웃 비율 |
| `/chat/send` 지연 | **Light** p50 ≤ 1.5s / p95 ≤ 3.5s / p99 ≤ 6s<br>**Deep** p50 ≤ 3.5s / p95 ≤ 8s / p99 ≤ 12s | 게이트웨이 타이머 |
| `/report/saju` 지연 | p50 ≤ 2.5s / p95 ≤ 6s | 체인 합산 |
| Guard 정합성 | Post-Guard **block ≤ 2%**, **patch ≤ 25%(Light), ≤ 15%(Deep)** | Guard 결과 이벤트 |
| 캐시 적중 | `/chat/send(light)` L2 히트율 ≥ 60% | Redis 히트율 |
| 스키마 준수 | JSON Schema 유효성 100% | ajv/jsonschema |
| SSV 정확성 | 중복 보상 0, 서명 검증 100% | 원장/SSV 로그 |
| 오류 예산 | 월간 실패 ≤ 0.5% | 오류율 집계 |
| 데이터 무결성 | 서명 검증 성공 100% | sha256 검증 |

---

## 2) 테스트 매트릭스

### 2.1 레이어별
- **Unit**: life_stage/void/yuanjin/combination, luck_annual/monthly, tokens ledger
- **Component**: tz-time/astro/pillars/analysis/luck/llm-polish/guard
- **Contract**: `/report/saju`, `/chat/send`, `/luck/*`, `/tokens/*` JSON Schema
- **Integration**: 서비스 체인(UTC↔LMT/절기/월주 경계/합화 가중)
- **E2E**: 프로필 저장→리포트→채팅(라이트/딥)→업셀→광고 보상→딥 재시도

### 2.2 파라미터 조합(샘플)
| 축 | 값 |
|---|---|
| calendar_type | solar / lunar |
| unknown_hour | true / false |
| zi_hour_mode | default / split_23 |
| timezone | UTC±, DST 경계(예: America/Los_Angeles) |
| solar_time | on/off |
| relation flags | combination_wuxing on/off |
| month boundary | 입절 직전/직후(±1분) |
| d/un | forward / reverse |
| load | 동시성 1/10/50(라이트), 1/5/20(딥) |

---

## 3) 테스트 데이터셋(10 프로필)

- **P1**: 서울 1999‑02‑05 23:30 split_23, DST X
- **P2**: 뉴욕 1988‑06‑05 01:05 DST on 경계
- **P3**: 도쿄 2001‑11‑07 12:00 solar_time on
- **P4**: 파리 1975‑04‑05 00:10 입절 직후
- **P5**: 시드니 1990‑12‑22 22:50 역행 대운
- **P6**: 서울 2000‑09‑14 10:00 합화 on
- **P7**: 베를린 1964‑02‑29 08:00 윤년
- **P8**: 상파울루 1993‑10‑17 23:55 unknown_hour
- **P9**: 타이베이 1986‑08‑08 14:20
- **P10**: 런던 2003‑03‑01 05:45 (DST 전)

각 프로필에 `/report/saju`, `/chat/send(light/deep)`, `/luck/*` 수행.

---

## 4) 성능/부하 계획

### 4.1 시나리오(k6 의사코드)
- **S1 Light Cached**: 60% 캐시 히트 가정, RPS 30, 15분
- **S2 Light Cold**: 캐시 미스, RPS 10, 10분
- **S3 Deep Mixed**: RPS 3, 동시성 15, 20분 (fallback 10% 유도)
- **S4 Report Batch**: 동시 5, 200건
- **S5 Tokens Flow**: reward→consume 예약/확정/해제 50 tpm

### 4.2 목표
- **S1**: p95 ≤ 3.0s / 오류율 ≤ 1%
- **S2**: p95 ≤ 4.0s
- **S3**: p95 ≤ 8.0s / 백스톱 비율 ≤ 5%
- **S4**: 평균 ≤ 6.0s, 실패 0
- **CPU/메모리**: 게이트웨이 p95 CPU ≤ 70%, RSS ≤ 600MB/인스턴스

### 4.3 결과 산출물
- 부하 리포트(JSON/HTML), 타임시리즈 그래프, 병목 분석(Top N)

---

## 5) 비용·COGS 관측 & 목표

| 항목 | 목표치 |
|---|---|
| Light 1회 추정비용 | 기준값 ≤ 1.0 단위(상대) |
| Deep 1회 추정비용 | 기준값 ≤ 5.0 단위(상대) |
| ARPMAU | ≥ 기준치 |
| 광고→딥 전환율 | ≥ 15% |
| 캐시로 절감된 LLM 호출 | ≥ 40% |

**방법**: `billing.sample` 이벤트로 모델별 추정치 수집, 월간 대시보드 집계.

---

## 6) 보안·프라이버시·부정방지

- **PII/프라이버시**: 이름/성별/생년 외 노출 차단 테스트(이메일/전화/주소 마스킹)
- **SSV**: 서명 검증/만료/중복/리플레이 방지, 일한도·쿨다운 준수
- **멱등**: `/tokens/*` reserve/finalize/release, 동일 키 재호출 noop
- **서명**: `/report/saju`·`/chat/send` 응답 `signatures.sha256` 검증
- **권한/요율**: Free/Plus/Pro 플로우 차단/업셀 동작

---

## 7) 모니터링/알림

### 이벤트
`route.decide`, `route.fallback`, `llm.request/response`, `guard.post.result`,
`tokens.reserve/finalize/release`, `reward.success/fail`, `cache.hit/miss`.

### 알림 규칙(예)
- p95 지연 임계 초과 10분 지속 → 경고
- Guard block > 3% (5분 이동평균) → 경고
- SSV 실패율 > 2% (10분) → 경고
- 5xx > 1% (5분) → 치명

### 대시보드
- 성능(지연/성공률), 비용, Guard 패치율, 캐시 히트율, 토큰 흐름

---

## 8) 릴리즈 플랜 & 롤백

| 단계 | 대상 | 비율 | 기간 | 게이트(통과 조건) |
|---|---|---:|---|---|
| **Staging** | 내부 QA | 100% | 1일 | 모든 테스트 녹색, p95 OK |
| **Canary** | 실사용자 | 5% → 25% | 1~2일 | 오류율/지연/Guard OK |
| **GA** | 전체 | 100% | — | KPI 안정 |

**롤백**: 카나리 중 임계 초과 시 **즉시 이전 버전 복구**, 피처플래그로 Guard/라우팅/SSV 개별 비활성화.

---

## 9) 런북(사고 대응)

- **LLM 지연 급증**: Light 라우팅 qwen→deepseek 스위치, 템플릿 축약, 타임아웃 하향
- **Guard block 급증**: 템플릿 팩 롤백, 모델 온도 하향, 동일 모델 재시도 경로 확인
- **SSV 장애**: 보상 중단 안내, 영수증 큐잉, 복구 후 배치 처리
- **멱등 충돌**: 키 스코프 확인, 중복 처리 NOOP 보장
- **캐시 적중 급락**: 키 해시 구성 변경 감시, 플래그/버전 영향 점검

---

## 10) 테스트 명세(케이스·수용 기준)

- **계약**: 모든 응답 JSON Schema 통과(9 엔드포인트)
- **경계**: 입절 ±1분, unknown_hour, zi_hour_mode split_23
- **성능**: S1~S5 목표 달성, 보고서 제출
- **보안**: PII 차단·서명 검증·SSV 성공/중복/만료
- **비용**: 모델별 비용 샘플 1,000건 수집, 목표치 이내

---

## 11) Go/No-Go 체크리스트

- [ ] 모든 테스트 녹색 / 리그레션 0
- [ ] p95/오류율 목표 충족
- [ ] Guard block/patch 비율 목표 충족
- [ ] 비용 지표 정상 / 캐시 히트율 확보
- [ ] 모니터링·알림·런북 준비
- [ ] 롤백 경로 검증 완료

---

## 12) NOW OUTPUT
위 형식을 **그대로** 따라 **QA · 성능 · 릴리즈 플랜 v1.0 문서**를 출력하라.
불필요한 설명 없이 **표/체크리스트/목표/시나리오/테스트/게이트**만 제공.
