# LLM Guard v1.0 — Changelog

**Policy Version:** 1.0.0
**Release Date:** 2025-10-09
**Policy Signature:** UNSIGNED (Policy Signature Auditor v1.0이 채움)

---

## [1.0.0] - 2025-10-09

### 초기 릴리스

**정책 파일:**
- `policy/llm_guard_policy_v1.json` (9개 규칙 세트)

**스키마 파일:**
- `schema/llm_guard_input_schema_v1.json` (Draft 2020-12)
- `schema/llm_guard_output_schema_v1.json` (Draft 2020-12)

**테스트 케이스:**
- `tests/llm_guard_cases_v1.jsonl` (18건)
  - allow: 6건
  - revise: 6건
  - deny: 6건

**예시 문서:**
- `samples/llm_guard_io_examples_v1.md` (좋은 예/나쁜 예, UI 모드별 응답 포맷)

**변경 이력:**
- `CHANGELOG_llm_guard_v1.md` (이 파일)

---

## 규칙 세트 (v1.0.0)

| Rule ID | Severity | Action | Reason Code | Description |
|---------|----------|--------|-------------|-------------|
| STRUCT-000 | error | deny | INPUT-INVALID | 입력 스키마 위반 |
| EVID-BIND-100 | error | revise | LLM-CLAIM-NOEVID | 근거 없는 사실 주장 |
| SCOPE-200 | error | deny | OUT-OF-SCOPE | 범위 외 요청 (의료/법률/투자 단정, 출생시각 추정) |
| MODAL-300 | warn | revise | MODALITY-OVERCLAIM | 과도한 단정 표현 (confidence 미달) |
| REL-400 | error | revise | REL-MISMATCH | Relation 결과 모순 |
| SIG-500 | error | deny | POLICY-SIG-MISMATCH | 정책 서명 검증 실패 |
| PII-600 | warn | revise/deny | PII-DETECTED | PII 포함 (전화번호/이메일/주소/주민번호) |
| KO-700 | warn | revise | LABEL-NONCOMPLIANT | KO-first 라벨 미준수 |
| AMBIG-800 | warn | revise | AMBIG-SOURCE | 고전/정책 출처 모호 |

---

## Modality Mapping

| Confidence | Label (KO) | Allowed Expressions |
|------------|------------|---------------------|
| 0.80 ~ 1.00 | 개연성이 매우 높음 | "~일 가능성이 매우 높습니다", "~로 해석됩니다" |
| 0.50 ~ 0.79 | 개연성이 높음 | "~일 가능성이 있습니다", "~로 볼 수 있습니다" |
| 0.00 ~ 0.49 | 가설 수준 | "~일 수도 있습니다", "~로 추정됩니다 (확정 아님)" |

---

## PII Patterns

| Type | Pattern | Example |
|------|---------|---------|
| phone_kr | `01[0-9]-?[0-9]{3,4}-?[0-9]{4}` | 010-1234-5678 |
| email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | user@example.com |
| address_detailed | `(시\|구\|동\|로\|길)\s*[0-9-]+.*호` | 강남구 테헤란로 123-45 101호 |
| ssn_like | `[0-9]{6}-?[1-4][0-9]{6}` | 920715-1234567 |

---

## Decision Algorithm

```
순차 평가:
  FOR EACH rule IN evaluation_order:
    evaluate(rule, input)
    IF rule.result == "fail":
      LOG trace entry
      IF rule.action == "deny":
        RETURN {"decision": "deny", "reasons": [rule.reason_code]}
      ELIF rule.action == "revise":
        COLLECT remediation

  IF any revise collected:
    RETURN {"decision": "revise", "reasons": [...], "remediations": [...]}
  ELSE:
    RETURN {"decision": "allow", "reasons": []}
```

---

## Risk Score Calculation

```
risk_score = 0
FOR EACH failed_rule:
  risk_score += 10
  IF failed_rule.severity == "error":
    risk_score += 20
  ELIF failed_rule.severity == "warn":
    risk_score += 5

risk_score = min(risk_score, 100)
```

---

## Test Coverage

| Category | Count | Examples |
|----------|-------|----------|
| allow | 6 | Evidence 인용 + 적절 모달리티, Relation 일치, KO 라벨 준수 |
| revise | 6 | 근거 없음, 과대 단정, Relation 불일치, PII 포함, 라벨 미준수, 출처 모호 |
| deny | 6 | 의료 진단, 출생시각 추정, 사망일 예측, 스키마 위반, 정책 서명 실패, 심각 PII |

---

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| strength_policy_v2.json | 2.0+ | 강약 평가 근거 검증 |
| relation_policy_v1.1.x | 1.1+ | 관계 분석 결과 검증 |
| evidence_builder_v2.json | 2.0+ | Evidence 구조 검증 |

---

## Migration Guide

### From Pre-v1.0 (없음)

v1.0.0이 초기 릴리스이므로 마이그레이션 불필요.

### To Future v1.1.0 (예정)

예상 변경사항:
- 추가 규칙: TWELVE-STAGE-900 (12운성 검증)
- 추가 규칙: YONGSHIN-1000 (용신 근거 검증)
- PII 패턴 확장: 신용카드 번호, 계좌번호

---

## Known Issues

없음 (v1.0.0 초기 릴리스)

---

## Future Roadmap

### v1.1.0 (2025-Q4)
- [ ] 12운성(lifecycle_stages) 검증 규칙 추가
- [ ] 용신(yongshin) 근거 검증 규칙 추가
- [ ] PII 패턴 확장 (신용카드, 계좌번호)

### v1.2.0 (2026-Q1)
- [ ] 조후(climate) 근거 검증 규칙 추가
- [ ] 다국어 지원 확장 (en-US, zh-CN)

### v2.0.0 (2026-Q2)
- [ ] ML 기반 confidence 예측 통합
- [ ] 실시간 정책 업데이트 지원

---

## Acknowledgments

- **정책 설계:** Policy Architecture Team
- **스키마 검증:** Schema Validation Team
- **테스트 케이스:** QA Team
- **문서화:** Documentation Team

---

## License

Internal Use Only — Proprietary

---

**Signature Status:** UNSIGNED

> **Note:** Policy Signature Auditor v1.0이 `policy_signature` 필드에 SHA-256 해시를 채운 후, 이 문서의 signature status를 업데이트합니다.

---

**End of Changelog**
