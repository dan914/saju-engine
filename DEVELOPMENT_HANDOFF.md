# [개발자 안내 | 사주 엔진 구현 작업 지시]

안녕하세요, 이번 스프린트에서 구현하실 작업과 기준을 정리했습니다.

**정책·표(JSON)는 디자인팀(PL+Qwen)이 제공하며, 코드는 JsonSchema 검증을 통과한 정책만 로드해야 합니다. 하드코딩 금지.**

---

## 1) 브랜치 & PR 규칙

### 브랜치 명명
```
feat/<epic>-<ticket>
```
예시: `feat/base-a1-contracts`

### PR 템플릿 체크리스트 (필수)
- [ ] 정책 JsonSchema 검증 통과
- [ ] 하드코딩 규칙 없음 (정책 주입)
- [ ] 단위 테스트 ≥3, 필요 시 E2E/Property tests
- [ ] Evidence 필수 필드 포함
- [ ] 성능 영향 (있으면 수치) 기재
- [ ] 변경로그/README 업데이트

---

## 2) 즉시 시작할 티켓 (우선순)

### ✅ A1 계약 고정
**파일**: `app/models/analysis.py`

**작업**:
- Lifecycle/Elements/Luck/Yongshin/Shensha/HiddenStems 필드 선언

**AC (Acceptance Criteria)**:
- 앱 부팅
- OpenAPI 노출
- 더미 /analyze 응답에 빈 구조 포함

---

### ✅ A2 정책 유틸
**파일**:
- `app/core/policy.py`
- `schemas/*.schema.json` (제공)

**작업**:
- `load_policy(path, schema) -> (dict, signature)` 구현

**AC**:
- 잘못된 JSON은 테스트에서 실패

---

### ✅ A3 Evidence & 프리셋
**파일**:
- `app/core/evidence.py`
- `app/core/presets.py`

**작업**:
- EvidenceLog 골격
- SITE_LIKE_V1/TRADITIONAL_KR 상수

**AC**:
- /analyze 더미 호출 시 policy_signature/evidence 포함

---

### ✅ B1 60갑자
**파일**: `rulesets/sixty_jiazi.json` 로더/유효성

**AC**:
- 중복 없음
- 0–59 순환 검증 테스트 통과

---

### ✅ B2 12운성 v0 (甲/乙)
**파일**: `app/core/lifecycle.py`

**AC**:
- 제공 테스트 케이스 통과
- 예시: 乙日: 辰→墓, 酉→絕, 亥→長生, 子→沐浴 등

---

### ✅ B3 Hidden Stems 노출
**파일**: `app/core/engine.py`

**AC**:
- 연/월/일/시 각 배열
- 본기→중기→여기 순서 유지

---

### ✅ B4 Branch Ten Gods
**파일**: `app/core/engine.py`

**AC**:
- 4기둥 주지(Primary 藏干)로 십신 표기
- 천간 십신과 함께 응답

---

### ✅ C1 Elements v0.1
**파일**: `app/core/elements.py`

**AC**:
- ∑=100% (±0.01)
- 라벨 (과다/발달/적정/부족)
- Evidence에 가중·임계 반영

---

### ✅ C2 Luck v1
**파일**: `app/core/luck.py`

**AC**:
- 월주 인덱스 → 방향 → 10개 생성
- 각 항목 십신/12운성 주석

---

**위 1–9까지 머지되면, 사용자 체감이 바로 납니다.**

---

### 🔄 후속 티켓

#### D1 12운성 전간
- 정책 확장 후 테스트 유지

#### D2 Elements ↔ Relations 연동
- 보존/중복금지 Property tests 포함

#### D3 Strength v1 연결
- score/bucket/evidence (항목별 기여)

#### D4 Yongshin v0.1
- 결과/사유 (reasoning) 표기

#### D5 Shensha v2
- per-pillar 매핑
- 吉/凶 집계

---

## 3) 금지/주의

### ❌ 하드코딩 금지
- 표·가중·우선순위는 전부 정책(JSON)에서 로드

### ❌ 교차 import 금지
- 서비스 간 파이썬 import 대신 내부 모듈 또는 HTTP

### ❌ sample 데이터 금지
- `data/canonical_v1`만 사용

### ⚠️ 관계 변환 규칙
- 합은 "원소 보존"으로 처리 (빼고 더함)
- 충/형 중복 차감 금지

---

## 4) 테스트

### 단위 테스트
- 각 모듈 ≥3 케이스 (정상/경계/예외)

### E2E 테스트
- site_like_v1·traditional_kr 스냅샷 (제공)

### Property 테스트
- 합 보존/중복 금지 성질 테스트

---

## 5) 성능/관측

### 목표
- 분석 p95 < 200ms

### 캐시
- LRU (옵션 Redis)
- 키: `(birth_dt_iso, tz, mode, zi)`

### Evidence 샘플링
- 로그 1%

---

## 협업 흐름 (요약)

### 디자인팀 (나 + Qwen)
- 정책/표/스키마/테스트 기대값/ADR 제공
- **디자인 소유**

### 구현팀 (클로드코드)
- 구현/테스트/성능/관측
- **구현 소유**

### 검수
- **Qwen**: PR 체크리스트로 리뷰
- **PL (나)**: 품질 게이트 (스냅샷/성질/성능) 확인

---

## 문의

궁금한 점은 PR에서 태그 주세요. 디자인팀이 정책·표·테스트 기대값을 함께 제공합니다.

감사합니다.
