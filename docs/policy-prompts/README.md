# 📚 사주 프로젝트 — Policy Prompts Hub (README)

**Version:** v1.0
**Date:** 2025-10-07 KST
**Path:** `docs/policy-prompts/README.md`

---

## 목적

정책/프롬프트/스키마/플로우를 한 곳에서 관리해, **Claude(코딩)**, **GPT-5 Pro(정책/스키마)**, 기타 모델들이 일관된 산출물을 내도록 하는 **중앙 허브**.

**문서 톤:** KO-first / 결정적(Deterministic) / Schema-first
**배치 위치:** 개발 리포지토리 최상단 `docs/policy-prompts/`

**핵심 원칙:**
- 모든 산출물은 **RFC-8785 canonical JSON + SHA-256 서명** 예시 포함
- **정책 결정**은 엔진/정책 파일이 단독 수행 → LLM은 수정 금지
- **LLM 역할**은 설명/코칭/요약/문장 다듬기만 (템플릿 우선 → LLM 보강)

---

## 0) 빠른 사용법 (Claude Runbook)

1. **항상 이 README를 먼저 읽고**, 각 섹션의 마스터 프롬프트를 열어 그대로 실행.
2. 산출물은 `specs/` 또는 해당 서비스 폴더 하위에 커밋.
3. **PR 제목 규칙:** `spec: <모듈명> vX.Y` (예: `spec: /chat/send spec v1.0`)
4. **테스트/샘플 포함 여부** 체크리스트 통과 후 머지.

---

## 1) 전체 흐름도 (엔진·서비스·LLM)

```
Client (앱 4탭: 홈/채팅/더보기/사주계산)
  ↓
API Gateway
  ↓
  ├─→ tz-time-service → astro-service → pillars-service
  │     ↓
  ├─→ analysis-service (십성/관계/강약/격국/신살/조후/용신)
  │     + (신규) TwelveStage / Void / Yuanjin / CombinationElement
  │     ↓
  ├─→ luck-service (Annual/Monthly)
  │     ↓
  ├─→ llm-polish (템플릿→문장화)
  │     ↓
  ├─→ LLMGuard (Pre/Post)
  │     ↓
  ├─→ billing/entitlement/tokens (권한·토큰·리워디드)
  │     ↓
  └─→ report-service (PDF)
```

**정책 결정(룰/수치/관계/버킷):** 엔진/정책이 단독 결정 → LLM은 수정 금지
**LLM 역할:** 설명/코칭/요약/문장 다듬기만 수행 (템플릿 우선 → LLM 보강)

---

## 2) 폴더 구조 권장안

```
/docs/policy-prompts/
  README.md                         # (현재 문서)
  00_master/                        # 통합 마스터 프롬프트
    Saju_Chat_Report_Integrated_Master_Prompt_v1.md
  10_api-specs/                     # API 사양 프롬프트
    01_openapi_lite_prompt.md       # 9개 엔드포인트 OpenAPI-lite
    02_report_schema_prompt.md      # /report/saju JSON Schema + 샘플
    03_chat_send_spec_prompt.md     # /chat/send 스펙(상태머신·라우팅·스키마)
  20_policy-engines/                # 정책/엔진 프롬프트
    relation_policy_extension_prompt.md
    twelve_stage_void_yuanjin_combo_prompt.md
    annual_monthly_luck_prompt.md
  30_llm/                           # LLM 템플릿·가드·라우팅
    llm_templates_5pack_prompt.md   # 오행/용신/강약/대운/연·월운
    llm_guard_v1_prompt.md
    model_routing_policy_prompt.md
  40_tokens_entitlements_ads/       # 토큰·권한·리워디드
    tokens_entitlements_ssv_prompt.md
  50_cache_storage_qc/              # 캐시/스토리지/QA
    cache_storage_idempotency_prompt.md
    qa_perf_release_plan_prompt.md
```

각 프롬프트는 **결정적 산출물만 출력**하도록 구성 (설명문 X, 스키마/표/코드/정책만).

---

## 3) 현재 준비된 프롬프트 링크

### 통합 마스터
- `00_master/Saju_Chat_Report_Integrated_Master_Prompt_v1.md` (⏳ 대기)

### API
- ✅ `10_api-specs/01_openapi_lite_prompt.md` (완료 → API_SPECIFICATION_v1.0.md)
- ✅ `10_api-specs/02_report_schema_prompt.md` (완료 → SAJU_REPORT_SCHEMA_v1.0.md)
- ✅ `10_api-specs/03_chat_send_spec_prompt.md` (완료 → CHAT_SEND_SPEC_v1.0.md)

### 정책/엔진
- ⏳ `20_policy-engines/relation_policy_extension_prompt.md`
- ⏳ `20_policy-engines/twelve_stage_void_yuanjin_combo_prompt.md`
- ⏳ `20_policy-engines/annual_monthly_luck_prompt.md`

### LLM
- ⏳ `30_llm/llm_templates_5pack_prompt.md`
- 🟡 `30_llm/llm_guard_v1_prompt.md` (계획만: LLM_GUARD_V1_ANALYSIS_AND_PLAN.md)
- ⏳ `30_llm/model_routing_policy_prompt.md`

### 토큰/광고/권한
- ⏳ `40_tokens_entitlements_ads/tokens_entitlements_ssv_prompt.md`

### 캐시/스토리지/QA
- ⏳ `50_cache_storage_qc/cache_storage_idempotency_prompt.md`
- ⏳ `50_cache_storage_qc/qa_perf_release_plan_prompt.md`

실제 파일은 이 README 생성 이후 차례로 추가.

---

## 4) 공통 규약 (필수)

### 파일 머리말

모든 프롬프트는 다음 형식:

```markdown
# <제목>

**버전**: vMAJOR.MINOR
**날짜**: YYYY-MM-DD KST
**경로 권장**: docs/policy-prompts/<섹션>/<파일명>

## ROLE
<역할 정의>

## GOAL
<목표 정의>

## OUTPUT ORDER
<산출물 순서>
```

### 스키마

- **$schema**: `https://json-schema.org/draft/2020-12/schema`
- **$defs** 적극 사용
- **description** 필수

### 서명

샘플 JSON에는 `signatures.sha256` 포함:

```json
{
  "meta": {
    "signatures": {
      "sha256": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a"
    }
  }
}
```

### 한자/KO 라벨

`*_ko` 병행:

```json
{
  "strength": {
    "bucket": "신약",
    "bucket_ko": "신약"
  }
}
```

### 금지사항

- LLM이 정책 수치를 임의변경
- 의료/법률/투자 구체행위 조언

---

## 5) 체크리스트 (PR 머지 전)

### 문서

- [ ] 제목/버전/날짜(KST) 포함
- [ ] ROLE/GOAL/OUTPUT ORDER 정의
- [ ] JSON Schema draft-2020-12 선언
- [ ] $defs 재사용 컴포넌트 분리
- [ ] description 필드 모든 속성에 포함
- [ ] 샘플 JSON 2건 이상 (정상 + 엣지)
- [ ] signatures.sha256 포함
- [ ] *_ko 라벨 병행 (KO-first)
- [ ] enum/pattern 완전성 검증
- [ ] 검증 힌트 섹션 포함

### 코드

- [ ] Pydantic 모델 정의
- [ ] 정책 파일 로딩 구현
- [ ] RFC-8785 서명 검증
- [ ] 단위 테스트 작성 (coverage ≥80%)
- [ ] 통합 테스트 작성
- [ ] Type hints 완전성
- [ ] Docstring 포함
- [ ] 에러 핸들링
- [ ] 로깅 추가
- [ ] Pre-commit hooks 통과

### 정책

- [ ] version 필드 포함
- [ ] signature.sha256 포함
- [ ] JSON Schema 스키마 파일 존재
- [ ] 스키마 검증 통과
- [ ] 샘플 데이터 3건 이상
- [ ] 엔진 통합 완료
- [ ] 테스트 케이스 작성
- [ ] 문서화 (README/claude.md)

---

## 6) 버전·호환성 정책

- **버전 표기:** `vMAJOR.MINOR` (예: v1.0). 브레이킹 변경 시 MAJOR 증가
- **폴더 이름·파일명에 버전 포함** 권장 (예: `*_prompt_v1.md`)
- **스키마는 $id로 버전 URI 명시** (예: `/schemas/report_saju_v1.schema.json`)

---

## 7) 참고: 모델 라우팅(요지)

| Depth        | 1차                     | 2차(Fallback)      | 3차(Backstop) | 용도              |
|--------------|-------------------------|--------------------|---------------|-------------------|
| Light        | Qwen Flash / DeepSeek   | Gemini 2.5 Pro     | GPT-5         | 짧은 코칭 (≤300t) |
| Deep         | Gemini 2.5 Pro          | GPT-5              | —             | 상세 코칭 (≤900t) |
| Report-style | Gemini 2.5 Pro          | GPT-5              | —             | 리포트 자동 생성  |

---

## 8) 다음 액션

1. ✅ `10_api-specs/02_report_schema_prompt.md` 실행 → 스키마 커밋
2. ✅ `10_api-specs/03_chat_send_spec_prompt.md` 실행 → 채팅 사양 커밋
3. ⏳ `40_tokens_entitlements_ads/tokens_entitlements_ssv_prompt.md` 실행 → 권한/토큰/광고 정책 커밋

---

## 문의/유지보수

**Core Architects** (백엔드/정책/데이터) — PR 리뷰 필수

**Version:** v1.0 (2025-10-07 KST)
