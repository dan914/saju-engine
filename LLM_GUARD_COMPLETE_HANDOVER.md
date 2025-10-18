# LLM Guard v1.0 - Complete Handover Document

**Date**: 2025-10-09 KST
**Version**: 1.0.0
**Status**: Policy complete, runtime implementation partial
**Policy Signature**: `a4dec83545592db3f3d7f3bdfaaf556a325e2c78f5ce7a39813ec6a077960ad2`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Current Implementation](#current-implementation)
4. [Policy Specification](#policy-specification)
5. [Schemas](#schemas)
6. [Test Cases](#test-cases)
7. [Examples](#examples)
8. [Implementation Roadmap](#implementation-roadmap)
9. [File Locations](#file-locations)

---

## Executive Summary

### What is LLM Guard?

LLM Guard is a policy-based validation system that ensures LLM-generated responses:
- **Are grounded in evidence** (no hallucinations)
- **Match confidence levels** (no overconfident claims)
- **Respect scope boundaries** (no medical/legal/investment advice)
- **Protect privacy** (PII detection and masking)
- **Use Korean-first labels** (KO-first compliance)
- **Maintain traceability** (immutable trace metadata)

### Current State

- ✅ **Policy v1.0**: Complete (181 lines, 9 rules, signed)
- ✅ **Schemas**: Input/output validation (JSON Schema Draft 2020-12)
- ✅ **Test cases**: 18 JSONL scenarios covering all rules
- ✅ **Minimal runtime**: Basic wrapper (63 lines) - production ready
- 🟡 **Full runtime**: Needs implementation (~500 lines estimated)

### Key Metrics

- **Rules**: 9 (3 deny, 6 revise/warn)
- **Modality ranges**: 3 (0.0-0.49, 0.5-0.79, 0.8-1.0)
- **PII patterns**: 4 (phone, email, address, SSN)
- **Exit codes**: allow, revise, deny
- **Risk score**: 0-100 (weighted by severity)

---

## System Architecture

### Execution Flow

```
LLM Response (candidate_answer)
    ↓
LLM Guard Input Validator
    ↓
Sequential Rule Evaluation (STRUCT → EVID → SCOPE → MODAL → REL → SIG → PII → KO → AMBIG)
    ↓
First Failure → Immediate Action (deny/revise)
    ↓
All Pass → allow
    ↓
LLM Guard Output (decision, reasons, remediations, risk_score, logs)
```

### Rule Evaluation Order

1. **STRUCT-000**: Schema validation (deny on fail)
2. **EVID-BIND-100**: Evidence binding check (revise on fail)
3. **SCOPE-200**: Out-of-scope requests (deny on fail)
4. **MODAL-300**: Modality matching (revise on fail)
5. **REL-400**: Relation consistency (revise on fail)
6. **SIG-500**: Policy signature verification (deny on fail)
7. **PII-600**: PII detection (revise/deny on fail)
8. **KO-700**: Korean label compliance (revise on fail)
9. **AMBIG-800**: Source citation clarity (revise on fail)

**Note**: First failure stops evaluation and returns action. All results logged in `logs.trace[]`.

---

## Current Implementation

### File: `services/analysis-service/app/core/llm_guard.py`

**Lines**: 63
**Status**: ✅ Production-ready (minimal version)

```python
"""LLM validation and guard utilities for analysis responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import AnalysisResponse
from .recommendation import RecommendationGuard
from .text_guard import TextGuard


@dataclass(slots=True)
class LLMGuard:
    """Provide JSON validation and post-processing for LLM workflow."""

    text_guard: TextGuard
    recommendation_guard: RecommendationGuard

    @classmethod
    def default(cls) -> "LLMGuard":
        return cls(
            text_guard=TextGuard.from_file(),
            recommendation_guard=RecommendationGuard.from_file(),
        )

    def prepare_payload(self, response: AnalysisResponse) -> dict:
        """Convert response to plain dict before giving it to an LLM."""
        # Pydantic ensures structure; raising early if invalid.
        AnalysisResponse.model_validate(response.model_dump())
        return response.model_dump()

    def postprocess(
        self,
        original: AnalysisResponse,
        llm_payload: dict,
        *,
        structure_primary: str | None = None,
        topic_tags: Iterable[str] | None = None,
    ) -> AnalysisResponse:
        """Validate LLM output and enforce guards."""
        candidate = AnalysisResponse.model_validate(llm_payload)

        # Trace must remain identical (LLM은 수정 불가).
        if candidate.trace != original.trace:
            raise ValueError("LLM output modified trace metadata")

        # Text guard for trace notes (향후 확장 대비).
        notes = candidate.trace.get("notes")
        if isinstance(notes, str):
            candidate.trace["notes"] = self.text_guard.guard(notes, topic_tags or [])

        # Recommendation guard: result는 trace에 advisory 필드로 기록.
        rec = self.recommendation_guard.decide(structure_primary=structure_primary)
        candidate.trace.setdefault("recommendation", rec)
        candidate.recommendation = candidate.recommendation.__class__(**rec)

        return candidate

    def validate_llm_output(self, llm_payload: dict) -> None:
        """Standalone validation for test/CI usage."""
        AnalysisResponse.model_validate(llm_payload)
```

### Tests: `services/analysis-service/tests/test_llm_guard.py`

**Lines**: 35
**Status**: ✅ 2/2 passing

```python
from app.core.engine import AnalysisEngine
from app.core.llm_guard import LLMGuard
from app.models import AnalysisRequest


def test_llm_guard_roundtrip() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = AnalysisRequest(pillars={}, options={})
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    result = guard.postprocess(
        response,
        payload,
        structure_primary=response.structure.primary,
        topic_tags=["건강"],
    )
    assert result.trace["recommendation"]["enabled"] is False
    assert result.recommendation.enabled is False


def test_llm_guard_detects_trace_mutation() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = AnalysisRequest(pillars={}, options={})
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    payload["trace"]["rule_id"] = "mutated"
    try:
        guard.postprocess(response, payload, structure_primary=response.structure.primary)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError when trace mutated")
```

---

## Policy Specification

### File: `policy/llm_guard_policy_v1.json`

**Lines**: 181
**Signature**: `a4dec83545592db3f3d7f3bdfaaf556a325e2c78f5ce7a39813ec6a077960ad2`
**Status**: ✅ Signed and verified

```json
{
  "engine": "llm_guard",
  "policy_version": "1.0.0",
  "policy_date": "2025-10-09",
  "policy_signature": "a4dec83545592db3f3d7f3bdfaaf556a325e2c78f5ce7a39813ec6a077960ad2",
  "ko_labels": true,
  "dependencies": [
    "strength_policy_v2.json",
    "relation_policy_v1.1.x",
    "evidence_builder_v2.json"
  ],
  "evaluation_order": [
    "STRUCT-000",
    "EVID-BIND-100",
    "SCOPE-200",
    "MODAL-300",
    "REL-400",
    "SIG-500",
    "PII-600",
    "KO-700",
    "AMBIG-800"
  ],
  "rules": [
    {
      "rule_id": "STRUCT-000",
      "severity": "error",
      "when": "입력 스키마 위반 또는 필수 필드 누락",
      "check_type": "schema",
      "action": "deny",
      "reason_code": "INPUT-INVALID",
      "message_ko": "입력 구조가 스키마를 위반했습니다",
      "remediation_hint_ko": "입력 스키마를 준수하여 재요청하세요",
      "evidence_refs": []
    },
    {
      "rule_id": "EVID-BIND-100",
      "severity": "error",
      "when": "사실 주장에 대응하는 evidence_id 바인딩이 누락됨",
      "check_type": "match",
      "action": "revise",
      "reason_code": "LLM-CLAIM-NOEVID",
      "message_ko": "근거 없는 사실 주장이 포함되어 있습니다",
      "remediation_hint_ko": "모든 사실 주장은 evidence.sources[].evidence_id를 인용하세요",
      "evidence_refs": ["evidence.sources[].evidence_id"]
    },
    {
      "rule_id": "SCOPE-200",
      "severity": "error",
      "when": "의료/법률/투자 구체 단정, 출생시각 추정, 사망일 예측 등 범위 외 요청",
      "check_type": "match",
      "action": "deny",
      "reason_code": "OUT-OF-SCOPE",
      "message_ko": "허용되지 않는 범위의 요청입니다",
      "remediation_hint_ko": "의료/법률/투자 단정, 출생시각 추정, 사망일 예측은 제공할 수 없습니다",
      "evidence_refs": []
    },
    {
      "rule_id": "MODAL-300",
      "severity": "warn",
      "when": "근거 confidence < 0.5인데 단정 표현('확실하다', '~이다') 사용",
      "check_type": "calc",
      "action": "revise",
      "reason_code": "MODALITY-OVERCLAIM",
      "message_ko": "근거 신뢰도에 비해 과도한 단정 표현이 사용되었습니다",
      "remediation_hint_ko": "confidence에 맞는 완화 표현을 사용하세요 (>=0.80: '개연성이 매우 높음', 0.50-0.79: '개연성이 높음', <0.50: '가설 수준')",
      "evidence_refs": ["evidence.sources[].confidence"]
    },
    {
      "rule_id": "REL-400",
      "severity": "error",
      "when": "Relation 탐지 결과와 모순되는 단정 (예: 충 관계 없는데 '충이 있다' 주장)",
      "check_type": "match",
      "action": "revise",
      "reason_code": "REL-MISMATCH",
      "message_ko": "관계 분석 결과와 모순되는 주장이 포함되어 있습니다",
      "remediation_hint_ko": "evidence.derived.relations 결과와 일치하도록 수정하세요",
      "evidence_refs": ["evidence.derived.relations"]
    },
    {
      "rule_id": "SIG-500",
      "severity": "error",
      "when": "입력 signatures.policy_refs[] 서명 검증 실패",
      "check_type": "calc",
      "action": "deny",
      "reason_code": "POLICY-SIG-MISMATCH",
      "message_ko": "정책 서명 검증에 실패했습니다",
      "remediation_hint_ko": "정책 파일의 무결성을 확인하고 재요청하세요",
      "evidence_refs": ["evidence.signatures.policy_refs"]
    },
    {
      "rule_id": "PII-600",
      "severity": "warn",
      "when": "PII (전화번호, 이메일, 상세주소, 주민번호 유사) 포함",
      "check_type": "match",
      "action": "revise",
      "reason_code": "PII-DETECTED",
      "message_ko": "개인 식별 정보가 포함되어 있습니다",
      "remediation_hint_ko": "PII는 마스킹 또는 제거 후 응답하세요 (redactions[] 활용)",
      "evidence_refs": []
    },
    {
      "rule_id": "KO-700",
      "severity": "warn",
      "when": "KO-first 라벨 미사용 또는 영문 전용 응답",
      "check_type": "match",
      "action": "revise",
      "reason_code": "LABEL-NONCOMPLIANT",
      "message_ko": "한국어 우선(KO-first) 라벨이 누락되었습니다",
      "remediation_hint_ko": "모든 enum/code 필드에 *_ko 병행 라벨을 제공하세요",
      "evidence_refs": []
    },
    {
      "rule_id": "AMBIG-800",
      "severity": "warn",
      "when": "고전/정책 출처 라벨 또는 근거 누락",
      "check_type": "match",
      "action": "revise",
      "reason_code": "AMBIG-SOURCE",
      "message_ko": "고전 또는 정책 출처 근거가 모호합니다",
      "remediation_hint_ko": "고전 인용 시 출전(예: '자평진전'), 정책 인용 시 정책명(예: 'strength_policy_v2')을 명시하세요",
      "evidence_refs": []
    }
  ],
  "modality_mapping": [
    {
      "confidence_min": 0.8,
      "confidence_max": 1.0,
      "label_ko": "개연성이 매우 높음",
      "allowed_expressions": [
        "~일 가능성이 매우 높습니다",
        "~로 해석됩니다"
      ]
    },
    {
      "confidence_min": 0.5,
      "confidence_max": 0.79,
      "label_ko": "개연성이 높음",
      "allowed_expressions": [
        "~일 가능성이 있습니다",
        "~로 볼 수 있습니다"
      ]
    },
    {
      "confidence_min": 0.0,
      "confidence_max": 0.49,
      "label_ko": "가설 수준",
      "allowed_expressions": [
        "~일 수도 있습니다",
        "~로 추정됩니다 (확정 아님)"
      ]
    }
  ],
  "pii_patterns": [
    {
      "type": "phone_kr",
      "pattern": "01[0-9]-?[0-9]{3,4}-?[0-9]{4}"
    },
    {
      "type": "email",
      "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    },
    {
      "type": "address_detailed",
      "pattern": "(시|구|동|로|길)\\s*[0-9-]+.*호"
    },
    {
      "type": "ssn_like",
      "pattern": "[0-9]{6}-?[1-4][0-9]{6}"
    }
  ],
  "decision_algorithm": "순차 평가: evaluation_order 순서대로 각 규칙 평가 → 첫 위반(fail) 시 해당 action 즉시 반환 → logs.trace[]에 모든 규칙 결과 기록 → decision/reasons/remediations 생성 → risk_score 계산",
  "risk_score_heuristics": "위반 갯수 × 10 + (severity='error' 시 +20, 'warn' 시 +5) 가중 합산, 최대 100으로 클램프"
}
```

---

## Schemas

### Input Schema: `schema/llm_guard_input_schema_v1.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "/schemas/llm_guard_input_v1.schema.json",
  "title": "llm_guard_input",
  "type": "object",
  "required": ["evidence", "candidate_answer"],
  "properties": {
    "evidence": {
      "type": "object",
      "required": ["case_id", "pillars", "derived", "sources", "signatures"],
      "properties": {
        "case_id": {"type": "string", "minLength": 1},
        "pillars": {
          "type": "object",
          "required": ["year", "month", "day", "hour"],
          "properties": {
            "year": {"type": "string", "pattern": "^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$"},
            "month": {"type": "string", "pattern": "^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$"},
            "day": {"type": "string", "pattern": "^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$"},
            "hour": {"type": ["string", "null"], "pattern": "^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$"}
          }
        },
        "derived": {
          "type": "object",
          "properties": {
            "strength": {"type": "object", "properties": {"level": {"type": "string"}, "score": {"type": "number"}}},
            "shensha": {"type": "array", "items": {"type": "object"}},
            "relations": {"type": "object", "properties": {"he6": {"type": "array"}, "sanhe": {"type": "array"}, "chong": {"type": "array"}, "xing": {"type": "array"}}},
            "wuxing_adjust": {"type": "object"},
            "void": {"type": "object", "properties": {"kong": {"type": "array", "items": {"type": "string"}}}}
          }
        },
        "sources": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["evidence_id", "type", "value", "confidence"],
            "properties": {
              "evidence_id": {"type": "string", "minLength": 1},
              "type": {"type": "string", "enum": ["engine_output", "policy_rule", "classic_text", "calculation"]},
              "value": {"type": "object"},
              "confidence": {"type": "number", "minimum": 0, "maximum": 1},
              "trace": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "signatures": {
          "type": "object",
          "required": ["canonical_sha256", "policy_refs"],
          "properties": {
            "canonical_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "policy_refs": {"type": "array", "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}
          }
        }
      }
    },
    "candidate_answer": {"type": ["string", "object"]},
    "requested_capabilities": {"type": "array", "items": {"type": "string"}},
    "policy_context": {
      "type": "object",
      "properties": {
        "allowed_claim_types": {"type": "array"},
        "forbidden_patterns": {"type": "array"},
        "locale": {"type": "string", "pattern": "^ko-KR$"},
        "ui_mode": {"type": "string", "enum": ["explainable", "compact"]}
      }
    },
    "runtime_info": {
      "type": "object",
      "properties": {
        "model_name": {"type": "string"},
        "prompt_id": {"type": "string"},
        "timestamp": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"}
      }
    }
  }
}
```

### Output Schema: `schema/llm_guard_output_schema_v1.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "/schemas/llm_guard_output_v1.schema.json",
  "title": "llm_guard_output",
  "type": "object",
  "required": ["decision", "reasons", "risk_score", "policy_snapshot_sha256", "logs"],
  "properties": {
    "decision": {"type": "string", "enum": ["allow", "revise", "deny"]},
    "reasons": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "message_ko"],
        "properties": {
          "code": {"type": "string", "enum": ["INPUT-INVALID", "LLM-CLAIM-NOEVID", "OUT-OF-SCOPE", "MODALITY-OVERCLAIM", "REL-MISMATCH", "POLICY-SIG-MISMATCH", "PII-DETECTED", "LABEL-NONCOMPLIANT", "AMBIG-SOURCE"]},
          "message_ko": {"type": "string", "minLength": 1}
        }
      }
    },
    "remediations": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "citations": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "redactions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "value", "rule_id"],
        "properties": {
          "type": {"type": "string"},
          "value": {"type": "string"},
          "rule_id": {"type": "string"}
        }
      }
    },
    "risk_score": {"type": "number", "minimum": 0, "maximum": 100},
    "policy_snapshot_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "logs": {
      "type": "object",
      "required": ["trace"],
      "properties": {
        "trace": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["rule_id", "result"],
            "properties": {
              "rule_id": {"type": "string"},
              "result": {"type": "string", "enum": ["pass", "fail"]},
              "evidence_refs": {"type": "array", "items": {"type": "string"}},
              "note_ko": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

---

## Test Cases

### File: `tests/llm_guard_cases_v1.jsonl`

**18 test cases** (JSONL format, one per line):

**Allow (6 cases):**
1. Normal with evidence citation + proper modality
2. Proper modality expression (confidence 0.72 → "개연성이 높음")
3. Proper Korean labels (bucket_ko present)
4. Relation match (chong detected → claim "자오충 있음")
5. Low confidence hypothesis tone (confidence 0.45 → "가설 수준")
6. Proper citation list

**Revise (6 cases):**
7. No evidence → `LLM-CLAIM-NOEVID`
8. Modality overclaim → `MODALITY-OVERCLAIM` (confidence 0.48 but uses "확실히")
9. Relation mismatch → `REL-MISMATCH` (evidence: no chong, claim: has chong)
10. PII phone → `PII-DETECTED`
11. No Korean labels → `LABEL-NONCOMPLIANT`
12. Ambiguous source → `AMBIG-SOURCE`

**Deny (6 cases):**
13. Out-of-scope medical → `OUT-OF-SCOPE`
14. Out-of-scope birth time → `OUT-OF-SCOPE`
15. Out-of-scope death prediction → `OUT-OF-SCOPE`
16. Invalid input → `INPUT-INVALID`
17. Policy signature fail → `POLICY-SIG-MISMATCH`
18. Severe PII (SSN) → `PII-DETECTED`

**Format**: Each line is a JSON object with `name`, `input`, `expected` fields.

---

## Examples

### Example 1: Allow - Evidence Citation + Proper Modality

**Input:**
```json
{
  "evidence": {
    "case_id": "good-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {"strength": {"level": "신약", "score": 35}},
    "sources": [
      {
        "evidence_id": "STR-001",
        "type": "engine_output",
        "value": {"bucket": "신약", "score": 35},
        "confidence": 0.85,
        "trace": ["strength_policy_v2"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc123...",
      "policy_refs": ["def456..."]
    }
  },
  "candidate_answer": "일간이 약하므로(STR-001) 개연성이 매우 높습니다",
  "policy_context": {"locale": "ko-KR", "ui_mode": "explainable"}
}
```

**Output:**
```json
{
  "decision": "allow",
  "reasons": [],
  "citations": ["STR-001"],
  "risk_score": 0,
  "policy_snapshot_sha256": "a4dec835...",
  "logs": {
    "trace": [
      {"rule_id": "STRUCT-000", "result": "pass"},
      {"rule_id": "EVID-BIND-100", "result": "pass", "evidence_refs": ["STR-001"]},
      {"rule_id": "MODAL-300", "result": "pass", "note_ko": "confidence 0.85 → '매우 높음' 적합"}
    ]
  }
}
```

---

### Example 2: Revise - No Evidence

**Input:**
```json
{
  "evidence": {
    "case_id": "bad-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {"strength": {"level": "신약", "score": 35}},
    "sources": [
      {
        "evidence_id": "STR-007",
        "type": "engine_output",
        "value": {"bucket": "신약", "score": 35},
        "confidence": 0.85,
        "trace": ["strength_policy_v2"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc129...",
      "policy_refs": ["def462..."]
    }
  },
  "candidate_answer": "일간이 약하고 용신은 금입니다",
  "policy_context": {"locale": "ko-KR"}
}
```

**Output:**
```json
{
  "decision": "revise",
  "reasons": [
    {
      "code": "LLM-CLAIM-NOEVID",
      "message_ko": "근거 없는 사실 주장이 포함되어 있습니다"
    }
  ],
  "remediations": [
    "'용신은 금입니다' 주장에 대한 evidence_id를 인용하세요"
  ],
  "citations": ["STR-007"],
  "risk_score": 30,
  "policy_snapshot_sha256": "a4dec835...",
  "logs": {
    "trace": [
      {"rule_id": "EVID-BIND-100", "result": "fail", "note_ko": "'용신은 금' 주장에 근거 없음"}
    ]
  }
}
```

---

### Example 3: Deny - Out of Scope (Medical)

**Input:**
```json
{
  "evidence": {
    "case_id": "deny-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {"strength": {"level": "신약", "score": 35}},
    "sources": [
      {
        "evidence_id": "STR-013",
        "type": "engine_output",
        "value": {"bucket": "신약", "score": 35},
        "confidence": 0.85,
        "trace": ["strength_policy_v2"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc135...",
      "policy_refs": ["def468..."]
    }
  },
  "candidate_answer": "일간이 약하므로 간 질환이 있습니다",
  "policy_context": {"locale": "ko-KR"},
  "requested_capabilities": ["의료 진단"]
}
```

**Output:**
```json
{
  "decision": "deny",
  "reasons": [
    {
      "code": "OUT-OF-SCOPE",
      "message_ko": "허용되지 않는 범위의 요청입니다"
    }
  ],
  "remediations": [
    "의료 진단은 제공할 수 없습니다"
  ],
  "risk_score": 50,
  "policy_snapshot_sha256": "a4dec835...",
  "logs": {
    "trace": [
      {"rule_id": "SCOPE-200", "result": "fail", "note_ko": "의료 진단 요청 감지"}
    ]
  }
}
```

---

## Implementation Roadmap

### Phase 1: Rule Evaluators (Estimated: 2-3 days)

Create individual evaluator classes for each rule:

```python
class StructValidator:
    """STRUCT-000: Schema validation"""
    def evaluate(input_data: dict) -> RuleResult:
        # Validate against llm_guard_input_schema_v1.json
        # Return pass/fail

class EvidenceBindingChecker:
    """EVID-BIND-100: Evidence binding check"""
    def evaluate(candidate_answer: str, sources: list) -> RuleResult:
        # Extract claims from candidate_answer
        # Check each claim has corresponding evidence_id
        # Return pass/fail with missing evidence_ids

class ScopeGuard:
    """SCOPE-200: Out-of-scope request detector"""
    def evaluate(candidate_answer: str, capabilities: list) -> RuleResult:
        # Check for forbidden keywords: 의료/진단/질환/병원/치료
        # Check for forbidden keywords: 법률/소송/계약/투자/주식
        # Check for forbidden keywords: 출생시각/추정/사망일/예측
        # Return pass/fail

class ModalityMatcher:
    """MODAL-300: Confidence-to-expression matcher"""
    def evaluate(candidate_answer: str, sources: list) -> RuleResult:
        # Extract expressions from candidate_answer
        # Check confidence ranges (0.8-1.0, 0.5-0.79, 0.0-0.49)
        # Match expression tone to confidence
        # Return pass/fail with overconfident expressions

class RelationValidator:
    """REL-400: Relation consistency checker"""
    def evaluate(candidate_answer: str, relations: dict) -> RuleResult:
        # Extract relation claims from candidate_answer
        # Compare with evidence.derived.relations
        # Return pass/fail with mismatches

class SignatureVerifier:
    """SIG-500: Policy signature verification"""
    def evaluate(policy_refs: list) -> RuleResult:
        # Use Policy Signature Auditor to verify each hash
        # Return pass/fail with invalid hashes

class PIIDetector:
    """PII-600: PII pattern detection"""
    def evaluate(candidate_answer: str) -> RuleResult:
        # Apply 4 regex patterns (phone_kr, email, address, ssn_like)
        # Return pass/fail with redactions[]

class KoLabelChecker:
    """KO-700: Korean label compliance"""
    def evaluate(candidate_answer: str, sources: list) -> RuleResult:
        # Check for *_ko fields in sources
        # Check for Korean vs English usage
        # Return pass/fail

class SourceCitationChecker:
    """AMBIG-800: Source citation clarity"""
    def evaluate(candidate_answer: str) -> RuleResult:
        # Check for vague phrases: "고전에서", "정책에 따르면"
        # Require specific citations: "자평진전", "strength_policy_v2"
        # Return pass/fail
```

### Phase 2: Decision Engine (Estimated: 1 day)

```python
class LLMGuardV1:
    """Full LLM Guard v1.0 implementation"""

    def __init__(self, policy_path: str):
        self.policy = self._load_policy(policy_path)
        self.evaluators = {
            "STRUCT-000": StructValidator(),
            "EVID-BIND-100": EvidenceBindingChecker(),
            "SCOPE-200": ScopeGuard(),
            "MODAL-300": ModalityMatcher(),
            "REL-400": RelationValidator(),
            "SIG-500": SignatureVerifier(),
            "PII-600": PIIDetector(),
            "KO-700": KoLabelChecker(),
            "AMBIG-800": SourceCitationChecker()
        }

    def evaluate(self, input_data: dict) -> dict:
        """Main evaluation entry point"""
        logs_trace = []
        risk_score = 0

        # Sequential evaluation in policy order
        for rule_id in self.policy["evaluation_order"]:
            rule = self._get_rule(rule_id)
            evaluator = self.evaluators[rule_id]

            # Evaluate rule
            result = evaluator.evaluate(input_data)

            # Log result
            logs_trace.append({
                "rule_id": rule_id,
                "result": "pass" if result.passed else "fail",
                "evidence_refs": result.evidence_refs,
                "note_ko": result.note
            })

            # First failure → immediate action
            if not result.passed:
                risk_score = self._calculate_risk(logs_trace, rule)
                return {
                    "decision": rule["action"],
                    "reasons": [{"code": rule["reason_code"], "message_ko": rule["message_ko"]}],
                    "remediations": [rule["remediation_hint_ko"]],
                    "citations": self._extract_citations(input_data),
                    "redactions": result.redactions,
                    "risk_score": risk_score,
                    "policy_snapshot_sha256": self.policy["policy_signature"],
                    "logs": {"trace": logs_trace}
                }

        # All passed
        return {
            "decision": "allow",
            "reasons": [],
            "citations": self._extract_citations(input_data),
            "risk_score": 0,
            "policy_snapshot_sha256": self.policy["policy_signature"],
            "logs": {"trace": logs_trace}
        }

    def _calculate_risk(self, logs_trace: list, failed_rule: dict) -> int:
        """Calculate risk score: violations × 10 + severity weights"""
        violations = sum(1 for log in logs_trace if log["result"] == "fail")
        severity_weight = 20 if failed_rule["severity"] == "error" else 5
        return min(violations * 10 + severity_weight, 100)
```

### Phase 3: Test Runner (Estimated: 0.5 day)

```python
def run_llm_guard_tests(jsonl_path: str, guard: LLMGuardV1):
    """Run all 18 test cases from JSONL file"""
    cases = load_jsonl(jsonl_path)
    passed = 0
    failed = 0

    for case in cases:
        result = guard.evaluate(case["input"])
        expected = case["expected"]

        # Validate decision
        if result["decision"] == expected["decision"]:
            # Validate reasons codes match
            if all(r["code"] in [e["code"] for e in expected.get("reasons", [])] for r in result["reasons"]):
                passed += 1
                print(f"✅ {case['name']}")
            else:
                failed += 1
                print(f"❌ {case['name']} - reasons mismatch")
        else:
            failed += 1
            print(f"❌ {case['name']} - decision mismatch")

    print(f"\n{passed}/{len(cases)} tests passed")
```

### Phase 4: Integration (Estimated: 1 day)

- Replace minimal `llm_guard.py` with `llm_guard_v1.py`
- Update `AnalysisEngine` to use full guard
- Add guard to LLM polish pipeline
- Update CI to run 18 test cases

---

## File Locations

```
/Users/yujumyeong/coding/ projects/사주/

Policy & Schemas:
├── policy/llm_guard_policy_v1.json                    (181 lines, signed)
├── schema/llm_guard_input_schema_v1.json              (264 lines)
├── schema/llm_guard_output_schema_v1.json             (138 lines)

Current Implementation:
├── services/analysis-service/app/core/llm_guard.py    (63 lines, minimal)
├── services/analysis-service/tests/test_llm_guard.py  (35 lines, 2/2 passing)

Test Cases & Examples:
├── tests/llm_guard_cases_v1.jsonl                     (18 cases)
├── samples/llm_guard_io_examples_v1.md                (516 lines, detailed examples)

Documentation:
├── CHANGELOG_llm_guard_v1.md                          (version history)
├── docs/policy-prompts/30_llm/llm_guard_v1_prompt.md  (implementation guide)
└── LLM_GUARD_COMPLETE_HANDOVER.md                     (this document)
```

---

## Quick Start Guide

### For AI Agent Taking Over:

1. **Read this document** - Everything you need is here
2. **Load policy** - `policy/llm_guard_policy_v1.json`
3. **Review schemas** - Input/output structure
4. **Study test cases** - `tests/llm_guard_cases_v1.jsonl` (18 scenarios)
5. **Implement evaluators** - Follow Phase 1 roadmap (9 rule classes)
6. **Build decision engine** - Follow Phase 2 roadmap (sequential evaluation)
7. **Run tests** - Validate against 18 JSONL cases
8. **Integrate** - Replace minimal guard with full v1.0

### Key Principles:

- **Policy is law**: Don't deviate from policy specifications
- **Sequential evaluation**: Stop at first failure
- **Log everything**: `logs.trace[]` records all rule results
- **Risk scoring**: `violations × 10 + severity_weight`
- **UI modes**: `explainable` (full) vs `compact` (first only)

---

## Contact & Support

**Policy Signature**: `a4dec83545592db3f3d7f3bdfaaf556a325e2c78f5ce7a39813ec6a077960ad2`
**Verification**: Use Policy Signature Auditor v1.0 to verify integrity

```bash
python policy_signature_auditor/psa_cli.py verify policy/llm_guard_policy_v1.json --strict
```

---

**End of Handover Document**

Generated: 2025-10-09 KST
Version: 1.0.0
Total Lines: ~3,500 (policy + schemas + code + tests + docs)
