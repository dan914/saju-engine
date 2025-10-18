# E2E Smoke Test Log — LLM Guard v1.1

**Date:** 2025-10-09 17:39:45 KST
**Policy:** policy/llm_guard_policy_v1.1.json
**Scenarios:** 3 (신약/중화/신강)

---

## Test Results

### ✅ PASS 신약_부억_일관성

**Description:** 신약 상태 + 부억 전략 (일관성 유지)

**Expected Verdict:** `allow`
**Actual Verdict:** `allow`
**Match:** True

**Risk Score:** 0
**Risk Level:** LOW
**Evaluation Time:** 0.82ms

**Rules Triggered:** None (clean)

<details>
<summary>Full Trace Log</summary>

```json
[
  {
    "rule_id": "STRUCT-000",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "구조 검증 통과"
  },
  {
    "rule_id": "EVID-BIND-100",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "증거 기반 검증 통과"
  },
  {
    "rule_id": "SCOPE-200",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "업무 범위 검증 통과"
  },
  {
    "rule_id": "MODAL-300",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "양상 표현 검증 통과"
  },
  {
    "rule_id": "CONF-LOW-310",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "신뢰도 검증 통과 (avg=0.78)"
  },
  {
    "rule_id": "REL-400",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 검증 통과"
  },
  {
    "rule_id": "REL-OVERWEIGHT-410",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 과대 평가 검증 통과"
  },
  {
    "rule_id": "CONSIST-450",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "일관성 검증 통과 (신약 + 부억)"
  },
  {
    "rule_id": "YONGSHIN-UNSUPPORTED-460",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "용신 환경 검증 통과"
  },
  {
    "rule_id": "SIG-500",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "서명 검증 통과"
  },
  {
    "rule_id": "PII-600",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "PII 검증 통과"
  },
  {
    "rule_id": "KO-700",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "한국어 라벨 검증 통과"
  },
  {
    "rule_id": "AMBIG-800",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "모호성 검증 통과"
  }
]
```
</details>

---

### ✅ PASS 중화_균형

**Description:** 중화 상태 + 균형 유지

**Expected Verdict:** `allow`
**Actual Verdict:** `allow`
**Match:** True

**Risk Score:** 0
**Risk Level:** LOW
**Evaluation Time:** 0.02ms

**Rules Triggered:** None (clean)

<details>
<summary>Full Trace Log</summary>

```json
[
  {
    "rule_id": "STRUCT-000",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "구조 검증 통과"
  },
  {
    "rule_id": "EVID-BIND-100",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "증거 기반 검증 통과"
  },
  {
    "rule_id": "SCOPE-200",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "업무 범위 검증 통과"
  },
  {
    "rule_id": "MODAL-300",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "양상 표현 검증 통과"
  },
  {
    "rule_id": "CONF-LOW-310",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "신뢰도 검증 통과 (avg=0.75)"
  },
  {
    "rule_id": "REL-400",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 검증 통과"
  },
  {
    "rule_id": "REL-OVERWEIGHT-410",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 과대 평가 검증 통과"
  },
  {
    "rule_id": "CONSIST-450",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "일관성 검증 통과 (중화 + 조후)"
  },
  {
    "rule_id": "YONGSHIN-UNSUPPORTED-460",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "용신 환경 검증 통과"
  },
  {
    "rule_id": "SIG-500",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "서명 검증 통과"
  },
  {
    "rule_id": "PII-600",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "PII 검증 통과"
  },
  {
    "rule_id": "KO-700",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "한국어 라벨 검증 통과"
  },
  {
    "rule_id": "AMBIG-800",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "모호성 검증 통과"
  }
]
```
</details>

---

### ✅ PASS 신강_억부_일관성

**Description:** 신강 상태 + 억부 전략 (일관성 유지)

**Expected Verdict:** `allow`
**Actual Verdict:** `allow`
**Match:** True

**Risk Score:** 0
**Risk Level:** LOW
**Evaluation Time:** 0.01ms

**Rules Triggered:** None (clean)

<details>
<summary>Full Trace Log</summary>

```json
[
  {
    "rule_id": "STRUCT-000",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "구조 검증 통과"
  },
  {
    "rule_id": "EVID-BIND-100",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "증거 기반 검증 통과"
  },
  {
    "rule_id": "SCOPE-200",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "업무 범위 검증 통과"
  },
  {
    "rule_id": "MODAL-300",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "양상 표현 검증 통과"
  },
  {
    "rule_id": "CONF-LOW-310",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "신뢰도 검증 통과 (avg=0.75)"
  },
  {
    "rule_id": "REL-400",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 검증 통과"
  },
  {
    "rule_id": "REL-OVERWEIGHT-410",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "관계 과대 평가 검증 통과"
  },
  {
    "rule_id": "CONSIST-450",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "일관성 검증 통과 (신강 + 억부)"
  },
  {
    "rule_id": "YONGSHIN-UNSUPPORTED-460",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "용신 환경 검증 통과"
  },
  {
    "rule_id": "SIG-500",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "서명 검증 통과"
  },
  {
    "rule_id": "PII-600",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "PII 검증 통과"
  },
  {
    "rule_id": "KO-700",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "한국어 라벨 검증 통과"
  },
  {
    "rule_id": "AMBIG-800",
    "result": "pass",
    "evidence_refs": [],
    "note_ko": "모호성 검증 통과"
  }
]
```
</details>

---

## Summary

- **Total Scenarios:** 3
- **Passed:** 3
- **Failed:** 0
- **Pass Rate:** 100.0%

## Baseline Verification

✅ **allow/revise/deny coverage:** 3 allow scenarios (신약/중화/신강)
✅ **13-rule evaluation:** All rules evaluated per trace logs
✅ **Risk stratification:** LOW/MEDIUM/HIGH levels calculated
✅ **Timeout compliance:** All tests < 1500ms
