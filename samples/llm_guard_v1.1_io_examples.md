# LLM Guard v1.1 I/O Examples

**Version:** v1.1
**Date:** 2025-10-09 KST
**Purpose:** Comprehensive input/output examples for LLM Guard v1.1

---

## Example 1: ALLOW Verdict (Low Risk, No Violations)

### Input

```json
{
  "request_id": "req-20251009-001",
  "llm_output": {
    "text": "일간이 신약이므로(STR-001) 인성과 비겁을 용신으로 활용하는 것이 유리합니다(YON-001). 목 오행이 용신이며(YON-001), 계절적으로 강한 지지를 받습니다(CLI-001). 삼합 관계가 부분적으로 형성되어(REL-001) 일부 긍정적 효과를 기대할 수 있습니다.",
    "metadata": {
      "model": "gemini-2.5-pro",
      "temperature": 0.7,
      "tokens": 142
    }
  },
  "evidence": {
    "sources": [
      {
        "evidence_id": "STR-001",
        "type": "strength",
        "confidence": 0.82,
        "claim": "일간 신약 (strength.score=28)",
        "claim_ko": "일간 신약"
      },
      {
        "evidence_id": "YON-001",
        "type": "yongshin",
        "confidence": 0.78,
        "claim": "목 용신 선정 (strategy=부억)",
        "claim_ko": "목 용신"
      },
      {
        "evidence_id": "CLI-001",
        "type": "climate",
        "confidence": 0.75,
        "claim": "계절 목 지지 (support=강함)",
        "claim_ko": "계절 지지 강함"
      },
      {
        "evidence_id": "REL-001",
        "type": "relation",
        "confidence": 0.70,
        "claim": "해묘미 삼합 부분 성립 (2/3 지지)",
        "claim_ko": "삼합 부분 성립"
      }
    ],
    "derived": {
      "relations": [
        {
          "type": "sanhe",
          "pillars": ["亥", "卯"],
          "effect": "목 오행 강화 (부분 성립)",
          "effect_ko": "목 강화"
        }
      ]
    },
    "signatures": {
      "policy_refs": [
        {
          "policy_name": "strength_policy_v2.json",
          "policy_version": "2.0",
          "sha256": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a"
        },
        {
          "policy_name": "yongshin_selector_policy_v1.json",
          "policy_version": "yongshin_v1.0.0",
          "sha256": "e0c95f3fdb1d382b06cd90eca7256f3121d648693d0986f67a5c5d368339cb8c"
        },
        {
          "policy_name": "relation_weight_policy_v1.0.json",
          "policy_version": "relation_weight_v1.0.0",
          "sha256": "704cf74d323a034ca8f49ceda2659a91e3ff1aed89ee4845950af6eb39df1b67"
        }
      ]
    }
  },
  "engine_summaries": {
    "strength": {
      "bucket": "신약",
      "bucket_ko": "신약",
      "score": 28,
      "confidence": 0.82
    },
    "relation_summary": {
      "relation_items": [
        {
          "type": "sanhe",
          "type_ko": "삼합",
          "impact_weight": 0.65,
          "conditions_met": ["adjacent", "partial"],
          "strict_mode_required": false,
          "formed": false,
          "hua": false
        }
      ],
      "confidence": 0.70
    },
    "yongshin_result": {
      "yongshin": ["목"],
      "bojosin": ["수"],
      "gisin": ["금"],
      "confidence": 0.78,
      "strategy": "부억",
      "strategy_ko": "부억"
    },
    "climate": {
      "season_element": "목",
      "support": "강함",
      "support_ko": "강함"
    }
  },
  "options": {
    "strict_mode": false,
    "ko_labels_required": true
  }
}
```

### Output

```json
{
  "request_id": "req-20251009-001",
  "verdict": "allow",
  "verdict_ko": "허용",
  "risk_score": 0,
  "risk_level": "low",
  "risk_level_ko": "낮음",
  "violations": [],
  "cross_engine_findings": [],
  "metadata": {
    "rules_evaluated": 13,
    "policy_version": "1.1.0",
    "policy_signature": "UNSIGNED",
    "validation_duration_ms": 45
  },
  "timestamp": "2025-10-09T10:30:00+09:00"
}
```

**Analysis:**
- ✅ All factual claims bound to evidence_id (EVID-BIND-100)
- ✅ Appropriate modality ("유리합니다", "기대할 수 있습니다") for confidence 0.70-0.82 (MODAL-300)
- ✅ Average confidence 0.76 ≥ 0.40 threshold (CONF-LOW-310)
- ✅ Cross-engine consistency: 신약 → 목 용신 (resource) aligned (CONSIST-450)
- ✅ Yongshin supported by climate (목 계절) and relation (삼합 목 강화) (YONGSHIN-UNSUPPORTED-460)
- ✅ Korean labels present (KO-700)
- ✅ Policy signatures verified (SIG-500)

**Risk Score Calculation:** 0 violations × weight = **0 (LOW)**

---

## Example 2: REVISE Verdict (Medium Risk, Multiple Warnings)

### Input

```json
{
  "request_id": "req-20251009-002",
  "llm_output": {
    "text": "삼합이 완전히 성립하여 절대적으로 강력한 효과를 발휘합니다. 용신은 반드시 화이며 계절적으로도 최고로 지지받습니다. 따라서 이 사주는 대길(大吉)입니다.",
    "metadata": {
      "model": "qwen-flash",
      "temperature": 0.5,
      "tokens": 98
    }
  },
  "evidence": {
    "sources": [
      {
        "evidence_id": "REL-002",
        "type": "relation",
        "confidence": 0.62,
        "claim": "인오술 삼합 부분 성립 (2/3 지지)",
        "claim_ko": "삼합 부분 성립"
      },
      {
        "evidence_id": "YON-002",
        "type": "yongshin",
        "confidence": 0.48,
        "claim": "화 용신 가능 (낮은 신뢰도)",
        "claim_ko": "화 용신"
      },
      {
        "evidence_id": "CLI-002",
        "type": "climate",
        "confidence": 0.35,
        "claim": "계절 수 상극 (support=약함)",
        "claim_ko": "계절 상극"
      }
    ],
    "derived": {
      "relations": [
        {
          "type": "sanhe",
          "pillars": ["寅", "午"],
          "effect": "화 오행 강화 (부분 성립)",
          "effect_ko": "화 강화 (부분)"
        }
      ]
    },
    "signatures": {
      "policy_refs": [
        {
          "policy_name": "yongshin_selector_policy_v1.json",
          "policy_version": "yongshin_v1.0.0",
          "sha256": "e0c95f3fdb1d382b06cd90eca7256f3121d648693d0986f67a5c5d368339cb8c"
        }
      ]
    }
  },
  "engine_summaries": {
    "strength": {
      "bucket": "중화",
      "bucket_ko": "중화",
      "score": 52,
      "confidence": 0.72
    },
    "relation_summary": {
      "relation_items": [
        {
          "type": "sanhe",
          "type_ko": "삼합",
          "impact_weight": 0.91,
          "conditions_met": ["partial"],
          "strict_mode_required": true,
          "formed": false,
          "hua": false
        }
      ],
      "confidence": 0.62
    },
    "yongshin_result": {
      "yongshin": ["화"],
      "bojosin": ["목"],
      "gisin": ["수"],
      "confidence": 0.48,
      "strategy": "조후",
      "strategy_ko": "조후"
    },
    "climate": {
      "season_element": "수",
      "support": "약함",
      "support_ko": "약함"
    }
  }
}
```

### Output

```json
{
  "request_id": "req-20251009-002",
  "verdict": "revise",
  "verdict_ko": "수정 필요",
  "risk_score": 38,
  "risk_level": "medium",
  "risk_level_ko": "보통",
  "violations": [
    {
      "rule_id": "EVID-BIND-100",
      "severity": "error",
      "severity_ko": "오류",
      "reason_code": "LLM-CLAIM-NOEVID",
      "message_ko": "근거 없는 사실 주장이 포함되어 있습니다",
      "remediation_hint_ko": "모든 사실 주장은 evidence.sources[].evidence_id를 인용하세요",
      "evidence_refs": ["evidence.sources[].evidence_id"],
      "details": {
        "expected": "Evidence binding for all claims",
        "actual": "Claims '절대적으로', '반드시', '최고로', '대길' without evidence_id",
        "location": "text[0:120]"
      }
    },
    {
      "rule_id": "MODAL-300",
      "severity": "warn",
      "severity_ko": "경고",
      "reason_code": "MODALITY-OVERCLAIM",
      "message_ko": "근거 신뢰도에 비해 과도한 단정 표현이 사용되었습니다",
      "remediation_hint_ko": "confidence 구간에 맞는 완화 표현을 사용하세요",
      "evidence_refs": ["evidence.sources[].confidence"],
      "details": {
        "expected": "Hedged expressions for confidence < 0.5",
        "actual": "Absolute expressions: '절대적으로', '반드시', '최고로' with confidence 0.48",
        "location": "text[0:80]"
      }
    },
    {
      "rule_id": "CONF-LOW-310",
      "severity": "warn",
      "severity_ko": "경고",
      "reason_code": "CONFIDENCE-LOW",
      "message_ko": "핵심 근거의 전반적 신뢰도가 낮습니다",
      "remediation_hint_ko": "저신뢰 결과는 가설 수준 표현으로 완화하고 추가 근거를 제시하세요",
      "evidence_refs": ["engine_summaries.*.confidence"],
      "details": {
        "expected": "Average confidence ≥ 0.40",
        "actual": "Average confidence = 0.39 (Strength: 0.72, Relation: 0.62, Yongshin: 0.48, Climate: 0.35)",
        "location": "N/A"
      }
    },
    {
      "rule_id": "REL-OVERWEIGHT-410",
      "severity": "warn",
      "severity_ko": "경고",
      "reason_code": "RELATION-OVERWEIGHT",
      "message_ko": "관계 효과를 과도하게 강조했습니다(조건 미충족/절대화 표현)",
      "remediation_hint_ko": "conditions_met를 인용하고 가설/가능성 어휘로 완화하세요",
      "evidence_refs": [
        "engine_summaries.relation_items[].conditions_met",
        "engine_summaries.relation_items[].strict_mode_required"
      ],
      "details": {
        "expected": "Hedged expression for impact_weight=0.91 with strict_mode_required=true but formed=false",
        "actual": "Absolute expression: '완전히 성립', '절대적으로 강력한' but conditions_met=['partial'], formed=false",
        "location": "text[0:35]"
      }
    },
    {
      "rule_id": "YONGSHIN-UNSUPPORTED-460",
      "severity": "warn",
      "severity_ko": "경고",
      "reason_code": "YONGSHIN-UNSUPPORTED",
      "message_ko": "선정된 용신이 환경적 지지를 받지 못합니다",
      "remediation_hint_ko": "climate.support 및 relation bias를 반영해 용신/보조신 재배치",
      "evidence_refs": [
        "engine_summaries.climate",
        "engine_summaries.relation_summary",
        "engine_summaries.yongshin_result"
      ],
      "details": {
        "expected": "Yongshin supported by climate or relation bias",
        "actual": "Yongshin=화 but climate.support='약함' (계절 수 상극), relation bias neutral",
        "location": "N/A"
      }
    }
  ],
  "cross_engine_findings": [
    {
      "finding_type": "climate_yongshin_unsupported",
      "finding_type_ko": "용신 기후 미지지",
      "engines_involved": ["yongshin", "climate"],
      "severity": "warn",
      "description_ko": "용신 화가 계절 수에 의해 상극 관계로 환경적 지지를 받지 못함",
      "evidence": {
        "yongshin": ["화"],
        "climate_support": "약함"
      }
    },
    {
      "finding_type": "low_confidence_cluster",
      "finding_type_ko": "저신뢰 집중",
      "engines_involved": ["yongshin", "climate", "relation"],
      "severity": "info",
      "description_ko": "Yongshin(0.48), Climate(0.35), Relation(0.62) 신뢰도가 전반적으로 낮음",
      "evidence": {
        "yongshin": ["화"],
        "relation_bias": "부분 성립",
        "climate_support": "약함"
      }
    }
  ],
  "metadata": {
    "rules_evaluated": 13,
    "policy_version": "1.1.0",
    "policy_signature": "UNSIGNED",
    "validation_duration_ms": 68
  },
  "timestamp": "2025-10-09T10:35:00+09:00"
}
```

**Analysis:**
- ❌ Multiple claims without evidence binding (EVID-BIND-100): '절대적으로', '반드시', '최고로', '대길'
- ❌ Absolute modality with low confidence 0.48 (MODAL-300)
- ❌ Average confidence 0.39 < 0.40 threshold (CONF-LOW-310)
- ❌ Relation overweight: impact_weight=0.91 but formed=false, strict_mode_required=true (REL-OVERWEIGHT-410)
- ❌ Yongshin 화 unsupported: climate 수 상극, support='약함' (YONGSHIN-UNSUPPORTED-460)

**Risk Score Calculation:**
- EVID-BIND-100 (error): 22
- MODAL-300 (warn): 8
- CONF-LOW-310 (warn, special): 10
- REL-OVERWEIGHT-410 (warn, special): 12 (capped from actual due to overlap)
- YONGSHIN-UNSUPPORTED-460 (warn): 8

**Total:** 22 + 8 + 10 (capped at 38 to avoid double-counting) = **38 (MEDIUM)**

---

## Example 3: DENY Verdict (High Risk, Cross-Engine Inconsistency)

### Input

```json
{
  "request_id": "req-20251009-003",
  "llm_output": {
    "text": "일간이 극신강하므로 인성을 적극 활용하여 보강해야 합니다. 용신은 목 인성이며 비겁도 함께 사용합니다. 지지의 자오충이 없어 안정적입니다. 이메일 myemail@example.com으로 상담 예약 가능합니다.",
    "metadata": {
      "model": "deepseek-chat",
      "temperature": 0.3,
      "tokens": 115
    }
  },
  "evidence": {
    "sources": [
      {
        "evidence_id": "STR-003",
        "type": "strength",
        "confidence": 0.88,
        "claim": "일간 극신강 (strength.score=85)",
        "claim_ko": "일간 극신강"
      },
      {
        "evidence_id": "YON-003",
        "type": "yongshin",
        "confidence": 0.72,
        "claim": "토금 용신 (strategy=부억)",
        "claim_ko": "토금 용신"
      },
      {
        "evidence_id": "REL-003",
        "type": "relation",
        "confidence": 0.90,
        "claim": "자오충 형성 (high severity)",
        "claim_ko": "자오충 형성"
      }
    ],
    "derived": {
      "relations": [
        {
          "type": "chong",
          "pillars": ["子", "午"],
          "effect": "충돌 발생",
          "effect_ko": "충돌"
        }
      ]
    }
  },
  "engine_summaries": {
    "strength": {
      "bucket": "극신강",
      "bucket_ko": "극신강",
      "score": 85,
      "confidence": 0.88
    },
    "relation_summary": {
      "relation_items": [
        {
          "type": "chong",
          "type_ko": "충",
          "impact_weight": 0.87,
          "conditions_met": ["adjacent", "formed"],
          "strict_mode_required": false,
          "formed": true,
          "hua": false
        }
      ],
      "confidence": 0.90
    },
    "yongshin_result": {
      "yongshin": ["토", "금"],
      "bojosin": [],
      "gisin": ["목", "수"],
      "confidence": 0.72,
      "strategy": "부억",
      "strategy_ko": "부억"
    }
  }
}
```

### Output

```json
{
  "request_id": "req-20251009-003",
  "verdict": "deny",
  "verdict_ko": "거부",
  "risk_score": 72,
  "risk_level": "high",
  "risk_level_ko": "높음",
  "violations": [
    {
      "rule_id": "CONSIST-450",
      "severity": "error",
      "severity_ko": "오류",
      "reason_code": "CONSIST-MISMATCH",
      "message_ko": "교차 엔진 일관성이 부족합니다",
      "remediation_hint_ko": "strength.score 구간과 relation_summary를 반영해 용신/해석을 조정하세요",
      "evidence_refs": [
        "engine_summaries.strength",
        "engine_summaries.yongshin_result",
        "engine_summaries.relation_summary"
      ],
      "details": {
        "expected": "극신강(score=85) → 억제 용신(토/금/수)",
        "actual": "LLM claims 목 인성(resource) + 비겁(companion) for 극신강, contradicts Yongshin engine result 토금",
        "location": "text[0:50]"
      }
    },
    {
      "rule_id": "REL-400",
      "severity": "error",
      "severity_ko": "오류",
      "reason_code": "REL-MISMATCH",
      "message_ko": "관계 분석 결과와 모순되는 주장이 포함되어 있습니다",
      "remediation_hint_ko": "evidence.derived.relations / relation_summary와 일치하도록 수정하세요",
      "evidence_refs": [
        "evidence.derived.relations",
        "engine_summaries.relation_summary"
      ],
      "details": {
        "expected": "자오충 형성 (impact_weight=0.87, formed=true)",
        "actual": "LLM claims '자오충이 없어 안정적' contradicts REL-003 evidence",
        "location": "text[60:85]"
      }
    },
    {
      "rule_id": "PII-600",
      "severity": "warn",
      "severity_ko": "경고",
      "reason_code": "PII-DETECTED",
      "message_ko": "개인 식별 정보가 포함되어 있습니다",
      "remediation_hint_ko": "PII는 마스킹 또는 제거 후 응답하세요",
      "evidence_refs": [],
      "details": {
        "expected": "No PII in output",
        "actual": "Email detected: myemail@example.com",
        "location": "text[90:115]"
      }
    }
  ],
  "cross_engine_findings": [
    {
      "finding_type": "strength_yongshin_mismatch",
      "finding_type_ko": "강약-용신 불일치",
      "engines_involved": ["strength", "yongshin"],
      "severity": "error",
      "description_ko": "일간 극신강(억제 필요)인데 LLM이 목 인성(보강) 용신을 제시하여 Yongshin engine 결과(토금)와 정반대",
      "evidence": {
        "strength_bucket": "극신강",
        "yongshin": ["토", "금"]
      }
    },
    {
      "finding_type": "relation_yongshin_conflict",
      "finding_type_ko": "관계-용신 충돌",
      "engines_involved": ["relation", "yongshin"],
      "severity": "warn",
      "description_ko": "자오충 형성(impact_weight=0.87)으로 변동성 높으나 LLM이 '안정적'으로 서술",
      "evidence": {
        "relation_bias": "chong (충돌)",
        "yongshin": ["토", "금"]
      }
    }
  ],
  "metadata": {
    "rules_evaluated": 13,
    "policy_version": "1.1.0",
    "policy_signature": "UNSIGNED",
    "validation_duration_ms": 82
  },
  "timestamp": "2025-10-09T10:40:00+09:00"
}
```

**Analysis:**
- ❌ **Critical:** Cross-engine consistency failure (CONSIST-450): 극신강 → 목 인성 용신 (should be 억제)
- ❌ **Critical:** Relation mismatch (REL-400): Claims no 자오충 when REL-003 evidence shows 자오충 formed
- ❌ PII detected (PII-600): Email address in output

**Risk Score Calculation:**
- CONSIST-450 (error, special): 28
- REL-400 (error): 22
- PII-600 (warn): 8

**Total:** 28 + 22 + 8 = **58**, but severity amplified to **72** due to multiple error-level violations = **HIGH RISK**

**Cross-Engine Findings:**
- **strength_yongshin_mismatch**: 극신강 requires 억제 (output/wealth/official), but LLM proposes 목 인성 (resource)
- **relation_yongshin_conflict**: 자오충 high impact but LLM claims "안정적" (stable)

---

## Summary of Examples

| Example | Verdict | Risk Level | Key Violations | Cross-Engine Findings |
|---------|---------|------------|----------------|----------------------|
| 1       | allow   | low (0)    | None           | None                 |
| 2       | revise  | medium (38)| EVID-BIND-100, MODAL-300, CONF-LOW-310, REL-OVERWEIGHT-410, YONGSHIN-UNSUPPORTED-460 | climate_yongshin_unsupported, low_confidence_cluster |
| 3       | deny    | high (72)  | CONSIST-450, REL-400, PII-600 | strength_yongshin_mismatch, relation_yongshin_conflict |

---

## Usage Notes

1. **Evidence Binding:** All factual claims must reference `evidence_id` (EVID-BIND-100)
2. **Modality Alignment:** Use confidence-appropriate expressions (MODAL-300):
   - 0.8-1.0: "~일 가능성이 매우 높습니다"
   - 0.5-0.79: "~일 가능성이 있습니다"
   - 0.0-0.49: "~일 수도 있습니다"
3. **Cross-Engine Consistency:** Verify Strength ↔ Yongshin ↔ Relation alignment (CONSIST-450)
4. **Relation Overweight:** For impact_weight ≥ 0.90, verify `conditions_met` includes strict conditions like `formed`, `hua` (REL-OVERWEIGHT-410)
5. **Yongshin Support:** Check `climate.support` and `relation_summary` bias for yongshin candidates (YONGSHIN-UNSUPPORTED-460)
6. **Low Confidence:** When average confidence < 0.40, use hedged/hypothesis-level language (CONF-LOW-310)

---

**End of Examples**
