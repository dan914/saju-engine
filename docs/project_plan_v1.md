# 사주 앱 v1.4 구현 계획 (Codex 초안)

## 0. 비전 & 불가역 원칙 재확인
- KR_classic v1.4 규칙을 서비스 전 구간에 일관 적용(연주=입춘 315°, 월주=12절, 일주=자시23, 시주=12지 2h, LCRO, ε=1ms).
- 천문/시간 계산은 Astronomy Engine(Primary) + 프리로드 절기 테이블을 사용하고, Swiss Ephemeris 금지.
- ΔT(Espenak–Meeus) 및 IANA tzdb 역사 이력(Seoul DST 1987–88, Pyongyang 2015–18) 강제 반영.
- LLM 레이어는 결과(숫자/판정) 수정 금지, 설명·문체만 조정. “근거 보기”는 UTC/Local/ms, ΔT, tz 이벤트, 규칙 버전을 고정 표기.
- 옵션에서 자정/중기/LMT/RST/연구 모드 제거, 사용자 노출도 제한.

## 1. 시스템 전반 아키텍처 요약
- **Client (Flutter/React)** ↔ **API Gateway/BFF (FastAPI)**
  - `pillars-service`: 4주 산출 엔진 (deterministic, KR_classic v1.4).
  - `astro-service`: 절기/황경 조회 (terms CSV + AE fallback, 캐시 활용).
  - `tz-time-service`: IANA 변환, 역사 이력/DST 플래그, tzdb 버전 감시.
  - `analysis-service`: 십신/관계/강약 도출, trace 포함.
  - `llm-polish`: Qwen3-Max 기반 문체 정리(수치 불변).
  - `llm-checker`: Gemini 2 Pro 기반 규칙 위반 여부 설명.
- Infra: PostgreSQL 15, Redis 7, Docker, GitHub Actions → 블루/그린 배포, OpenTelemetry 기반 관측.
- 공용 리소스: `rulesets/` JSON, `terms_1600_2200.csv`, 로그/메트릭 스키마.

## 2. 작업 스트림 & 산출물
| 스트림 | 주요 산출물 | 기술 스택/참고 |
|--------|-------------|----------------|
|데이터/천문|`terms_1600_2200.csv` 로더, 절기 조회 API, ΔT 검증|Python 3.11, pandas/pyarrow(선택), Astronomy Engine|
|시간대|tz 변환 모듈, tz 이벤트 플래그, tzdb 버전 감시 Job|`zoneinfo`, `pytzdata` or custom tzdb loader|
|4주 엔진|연/월/일/시주 계산, 오호둔/오서둔, trace|纯 Python, deterministic unit tests|
|분석|십신 계산, 관계(충합형파해), 강약 등급|규칙 JSON + Python 서비스|
|검증|`/rules-validate` 스크립트, 골든셋 ≥200 케이스|pytest + snapshot|
|LLM|Polisher/Checker System prompt, 가드 텍스트, RAG 메모리|LangChain/FastAPI, 벡터스토어|
|BFF/UI|/v2 API 라우팅, 근거 보기 UI, Pyongyang 특수 섹션|FastAPI + React/Flutter|
|DevOps|CI 파이프라인, 컨테이너, 배포 게이트, 모니터링|GitHub Actions, Docker, OTel|

## 3. Phase별 일정 제안 (8주 가정)
### Phase 0 — 킥오프 & 기반 (Week 0–1)
- 리포지터리 구조화(monorepo: `services/`, `rulesets/`, `data/`, `clients/`).
- 코딩 규약/포맷터/CI 스켈레톤(black, isort, mypy, pytest, pre-commit).
- 기본 Dockerfile, compose 템플릿, 로컬 개발 문서화.
- `rulesets/` JSON 검증 스키마 정의(jsonschema) + lint 스크립트.

### Phase 1 — 천문 & 시간대 레이어 (Week 1–3)
- `astro-service` 초벌: CSV 로더, API `/v2/terms`, 캐시, AE fallback.
- ΔT 적용 모듈 구현 및 단위 테스트(경계 연도 케이스 포함).
- `tz-time-service` 기본 기능: UTC↔local 변환, tz 이벤트 로깅, 버전 감시 API.
- Seoul/Pyongyang 역사 케이스 유닛 테스트, transition 플래그 검증.

### Phase 2 — Pillars Core (Week 3–5)
- `pillars-service` 핵심 계산 모듈: 연주(입춘), 월주(12절), 일주(자시23 JDN), 시주(오서둔).
- LCRO + ε=1ms 경계 처리, edge flag 세트 구현.
- Trace 구조 통일(rule_id, ΔT, tz 이벤트, astro diff 등) 및 API `/v2/pillars/compute` 완성.
- 골든셋 중 경계/타임존 케이스 50건으로 1차 자동검증.

### Phase 3 — 분석 서비스 (Week 5–6)
- 십신 매핑(오행 생극 + 음양) → `ten_gods` 결과 구조 확정.
- 관계도(六合/三合/冲/害/破/刑) 계산 로직 및 테스트.
- 강약(정성 등급) 계산: `strength_criteria_v1.json` 적용, 편향 검토.
- `/v2/analyze` API, trace(rule_id) 포함, 범용 옵션 구조 마련.

### Phase 4 — LLM 및 UI/BFF (Week 6–7)
- `llm-polish`: System prompt + 수치 불변 검증 Hook(전/후 diff).
- `llm-checker`: 규칙 요약 출력, /rules-validate 연동.
- BFF `/v2/report`, 메모리 스토어(mem_profile/survey/insights)을 Redis+Postgres 연동.
- 클라이언트 “근거 보기” 탭 구현, Pyongyang 타임존 섹션 UI, 접근성(큰글씨/TTS) 체크리스트.

### Phase 5 — 통합 검증 & 배포 게이트 (Week 7–8)
- 골든셋 ≥200 실행, 회귀 리포트 자동화(diff >1s Fail).
- 성능 측정: `astro-service` P95 < 40ms, `pillars-service` P95 < 120ms → 부하테스트.
- OpenTelemetry 트레이싱/메트릭 대시보드, 구조화 로그 필드 확정.
- GitHub Actions 배포 파이프라인, 블루-그린 자동 전환 스크립트, 문서 "운영 Runbook" 작성.

## 4. 테스트 전략
- 단위: 각 서비스별 pytest + property-based(예: 일주 60갑자 순환성 검사).
- 골든셋: 절기/경계/타임존/연대 시나리오 200케이스 YAML → 통합 테스트 러너.
- 계약 테스트: `/v2` API 스키마(JSON Schema) + FastAPI `TestClient`.
- 회귀: tzdb 업데이트 시 샘플 20건 재계산 파이프라인.
- LLM 안전망: 수치 변조 감지, prompt 기반 시뮬레이션 테스트.

## 5. 데이터 & 설정 관리
- `data/terms_1600_2200.csv`: 앱 기동 시 메모리 로드, Parquet 캐싱 옵션 검토.
- `rulesets/`: 버전 관리(semver), 변경 시 마이그레이션 로그.
- 환경 변수 템플릿 `.env.example` 생성 (ASTRO_SOURCE, RULESET_ID 등).
- tzdb 버전 알림: 주 1회 크론 잡, 변경 시 슬랙 알림 + 샘플 회귀.

## 6. 운영 & 보안
- 개인정보 저장 분리 설계: PII DB ↔ 결과 DB 분리, 개인정보 암호화.
- 로그 마스킹(생년월일 등), 감사 추적(ID, rule_id, tzdbVersion).
- 삭제/내보내기 API(비동기 Job) 설계 초안.
- 면책 문구/AI 고지 문구 클라이언트 + API 공통 템플릿.

## 7. 리스크 & 완화 전략
- **절기 테이블 정확도**: AE 결과와 csv diff 테스트, 주기적 검증.
- **타임존 이력**: tzdb 업데이트 누락 방지 → 감시 Job + 회귀 자동화.
- **LLM 수치 변조**: pre/post diff, 실패 시 fallback(원문 그대로 전달).
- **성능**: 프리로드/캐시 설계, 비동기 FastAPI, Redis 캐시 튜닝.
- **품질 게이트 미통과**: CI에서 조기 차단, 핫픽스 절차 정의.

## 8. 커뮤니케이션 & 다음 단계
- 위 계획을 기준으로 JIRA/Linear 이슈화(스트림별 Epic → Story 분해).
- 주 2회 스탠드업, 주간 데모 & 품질 리포트 공유.
- 승인 후 Phase 0 작업(리포 구조/CI 스켈레톤) 즉시 착수.

