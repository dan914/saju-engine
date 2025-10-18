# LLM Guard v1.0 — I/O Examples

**Version:** 1.0.0
**Date:** 2025-10-09
**Purpose:** LLM 응답 검증 입출력 예시

---

## 좋은 예 (allow)

### 예시 1: Evidence 인용 + 적절한 모달리티

**입력:**
```json
{
  "evidence": {
    "case_id": "good-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {
      "strength": {"level": "신약", "score": 35}
    },
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
  "policy_context": {
    "locale": "ko-KR",
    "ui_mode": "explainable"
  }
}
```

**출력:**
```json
{
  "decision": "allow",
  "reasons": [],
  "citations": ["STR-001"],
  "risk_score": 0,
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "STRUCT-000", "result": "pass"},
      {"rule_id": "EVID-BIND-100", "result": "pass", "evidence_refs": ["STR-001"]},
      {"rule_id": "MODAL-300", "result": "pass", "note_ko": "confidence 0.85 → '매우 높음' 적합"}
    ]
  }
}
```

**설명:** Evidence 인용 + confidence 0.85 → "개연성이 매우 높음" 표현 적합 → 허용

---

### 예시 2: 관계 분석 결과와 일치

**입력:**
```json
{
  "evidence": {
    "case_id": "good-002",
    "pillars": {"year": "壬午", "month": "癸丑", "day": "甲子", "hour": "丙寅"},
    "derived": {
      "relations": {
        "chong": [{"pair": ["子", "午"], "severity": "high"}]
      }
    },
    "sources": [
      {
        "evidence_id": "REL-001",
        "type": "engine_output",
        "value": {"chong": [{"pair": ["子", "午"]}]},
        "confidence": 0.95,
        "trace": ["relation_policy_v1.1"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc124...",
      "policy_refs": ["def457..."]
    }
  },
  "candidate_answer": "자오충이 있습니다(REL-001)",
  "policy_context": {"locale": "ko-KR"}
}
```

**출력:**
```json
{
  "decision": "allow",
  "reasons": [],
  "citations": ["REL-001"],
  "risk_score": 0,
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "REL-400", "result": "pass", "evidence_refs": ["REL-001"], "note_ko": "충 관계 일치"}
    ]
  }
}
```

**설명:** Relation 결과(자오충 존재)와 주장 일치 → 허용

---

## 나쁜 예 (revise)

### 예시 3: 근거 없는 주장

**입력:**
```json
{
  "evidence": {
    "case_id": "bad-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {
      "strength": {"level": "신약", "score": 35}
    },
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

**출력:**
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
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "EVID-BIND-100", "result": "fail", "note_ko": "'용신은 금' 주장에 근거 없음"}
    ]
  }
}
```

**설명:** "용신은 금" 주장에 대응하는 evidence_id 없음 → 수정 요구

---

### 예시 4: 과도한 단정 (confidence 미달)

**입력:**
```json
{
  "evidence": {
    "case_id": "bad-002",
    "pillars": {"year": "甲子", "month": "丙寅", "day": "戊午", "hour": "壬戌"},
    "derived": {
      "strength": {"level": "중화", "score": 55}
    },
    "sources": [
      {
        "evidence_id": "STR-008",
        "type": "engine_output",
        "value": {"bucket": "중화", "score": 55},
        "confidence": 0.48,
        "trace": ["strength_policy_v2"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc130...",
      "policy_refs": ["def463..."]
    }
  },
  "candidate_answer": "일간이 확실히 중화입니다(STR-008)",
  "policy_context": {"locale": "ko-KR"}
}
```

**출력:**
```json
{
  "decision": "revise",
  "reasons": [
    {
      "code": "MODALITY-OVERCLAIM",
      "message_ko": "근거 신뢰도에 비해 과도한 단정 표현이 사용되었습니다"
    }
  ],
  "remediations": [
    "confidence 0.48은 '가설 수준'이므로 '~일 수도 있습니다'로 완화하세요"
  ],
  "citations": ["STR-008"],
  "risk_score": 15,
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "MODAL-300", "result": "fail", "evidence_refs": ["STR-008"], "note_ko": "confidence 0.48 < 0.50 → '확실히' 단정 부적합"}
    ]
  }
}
```

**설명:** confidence 0.48 (가설 수준)인데 "확실히" 단정 → 표현 완화 요구

---

### 예시 5: Relation 불일치

**입력:**
```json
{
  "evidence": {
    "case_id": "bad-003",
    "pillars": {"year": "壬午", "month": "癸丑", "day": "甲子", "hour": "丙寅"},
    "derived": {
      "relations": {
        "chong": []
      }
    },
    "sources": [
      {
        "evidence_id": "REL-009",
        "type": "engine_output",
        "value": {"chong": []},
        "confidence": 0.95,
        "trace": ["relation_policy_v1.1"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc131...",
      "policy_refs": ["def464..."]
    }
  },
  "candidate_answer": "자오충이 있습니다",
  "policy_context": {"locale": "ko-KR"}
}
```

**출력:**
```json
{
  "decision": "revise",
  "reasons": [
    {
      "code": "REL-MISMATCH",
      "message_ko": "관계 분석 결과와 모순되는 주장이 포함되어 있습니다"
    }
  ],
  "remediations": [
    "REL-009에서 충 관계가 없습니다. 주장을 수정하세요"
  ],
  "citations": [],
  "risk_score": 30,
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "REL-400", "result": "fail", "evidence_refs": ["REL-009"], "note_ko": "충 관계 불일치 (evidence: 없음, claim: 있음)"}
    ]
  }
}
```

**설명:** Evidence에서 충 관계 없음 → 주장("자오충 있음") 모순 → 수정 요구

---

## 나쁜 예 (deny)

### 예시 6: 범위 외 요청 (의료)

**입력:**
```json
{
  "evidence": {
    "case_id": "deny-001",
    "pillars": {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"},
    "derived": {
      "strength": {"level": "신약", "score": 35}
    },
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

**출력:**
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
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "SCOPE-200", "result": "fail", "note_ko": "의료 진단 요청 감지"}
    ]
  }
}
```

**설명:** 의료 진단은 범위 외 → 차단

---

### 예시 7: 정책 서명 불일치

**입력:**
```json
{
  "evidence": {
    "case_id": "deny-002",
    "pillars": {"year": "戊寅", "month": "甲子", "day": "庚午", "hour": "丁亥"},
    "derived": {
      "strength": {"level": "신약", "score": 38}
    },
    "sources": [
      {
        "evidence_id": "STR-017",
        "type": "engine_output",
        "value": {"bucket": "신약", "score": 38},
        "confidence": 0.82,
        "trace": ["strength_policy_v2"]
      }
    ],
    "signatures": {
      "canonical_sha256": "abc139...",
      "policy_refs": ["invalid_hash"]
    }
  },
  "candidate_answer": "일간이 약합니다",
  "policy_context": {"locale": "ko-KR"}
}
```

**출력:**
```json
{
  "decision": "deny",
  "reasons": [
    {
      "code": "POLICY-SIG-MISMATCH",
      "message_ko": "정책 서명 검증에 실패했습니다"
    }
  ],
  "remediations": [
    "정책 파일의 무결성을 확인하고 재요청하세요"
  ],
  "risk_score": 70,
  "policy_snapshot_sha256": "policy_hash...",
  "logs": {
    "trace": [
      {"rule_id": "SIG-500", "result": "fail", "evidence_refs": ["invalid_hash"], "note_ko": "정책 서명 불일치"}
    ]
  }
}
```

**설명:** 정책 서명 검증 실패 → 차단

---

## UI 모드별 응답 포맷

| 항목 | explainable 모드 | compact 모드 |
|------|------------------|--------------|
| **decision** | "allow" / "revise" / "deny" | 동일 |
| **reasons** | 전체 배열 (상세 메시지 포함) | 첫 번째 reason만 |
| **remediations** | 모든 remediation 리스트 | 첫 번째 remediation만 |
| **citations** | 모든 evidence_id 리스트 | 최대 3개만 |
| **logs.trace** | 전체 trace 배열 | 빈 배열 (생략) |
| **risk_score** | 표시 | 표시 |

**explainable 모드 응답 예시:**
```json
{
  "decision": "revise",
  "reasons": [
    {"code": "LLM-CLAIM-NOEVID", "message_ko": "근거 없는 사실 주장"},
    {"code": "MODAL-300", "message_ko": "과도한 단정"}
  ],
  "remediations": [
    "evidence_id 인용 추가",
    "표현 완화 ('개연성이 높음')"
  ],
  "citations": ["STR-001", "STR-002"],
  "risk_score": 25,
  "logs": {
    "trace": [
      {"rule_id": "EVID-BIND-100", "result": "fail"},
      {"rule_id": "MODAL-300", "result": "fail"}
    ]
  }
}
```

**compact 모드 응답 예시:**
```json
{
  "decision": "revise",
  "reasons": [
    {"code": "LLM-CLAIM-NOEVID", "message_ko": "근거 없는 사실 주장"}
  ],
  "remediations": [
    "evidence_id 인용 추가"
  ],
  "citations": ["STR-001"],
  "risk_score": 25,
  "logs": {
    "trace": []
  }
}
```

---

## PII 처리 예시

### 전화번호 마스킹

**입력:**
```json
{
  "candidate_answer": "상담 문의: 010-1234-5678"
}
```

**출력:**
```json
{
  "decision": "revise",
  "reasons": [{"code": "PII-DETECTED", "message_ko": "개인 식별 정보 포함"}],
  "remediations": ["전화번호를 마스킹 또는 제거하세요"],
  "redactions": [
    {"type": "phone_kr", "value": "010-1234-5678", "rule_id": "PII-600"}
  ],
  "risk_score": 15
}
```

### 주민번호 차단 (심각)

**입력:**
```json
{
  "candidate_answer": "주민번호: 920715-1234567"
}
```

**출력:**
```json
{
  "decision": "deny",
  "reasons": [{"code": "PII-DETECTED", "message_ko": "개인 식별 정보 포함"}],
  "remediations": ["주민번호 유사 패턴은 절대 포함할 수 없습니다"],
  "redactions": [
    {"type": "ssn_like", "value": "920715-1234567", "rule_id": "PII-600"}
  ],
  "risk_score": 100
}
```

---

**End of Examples**
