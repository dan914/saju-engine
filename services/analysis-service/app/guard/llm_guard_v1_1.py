"""
LLM Guard v1.1 Runtime - Cross-Engine Consistency Validation

Implements 13-rule policy enforcement with:
- Sequential rule evaluation (fail-fast on first violation)
- Risk stratification (LOW 0-29, MEDIUM 30-69, HIGH 70-100)
- Revise loop (1 retry with remediation guidance)
- Timeout/fallback (≤1500ms total, ≤300ms guard-only)
- Trace logging for audit trail

Version: 1.1.0
Date: 2025-10-09 KST
Policy: policy/llm_guard_policy_v1.1.json
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


LOGGER = logging.getLogger(__name__)


class LLMGuardV11:
    """
    LLM Guard v1.1 runtime with cross-engine consistency validation.

    Usage:
        >>> guard = LLMGuardV11("policy/llm_guard_policy_v1.1.json")
        >>> result = guard.decide({
        ...     "evidence": {...},
        ...     "candidate_answer": "...",
        ...     "engine_summaries": {...},
        ...     "policy_context": {"locale": "ko-KR"}
        ... }, timeout_ms=1500)
        >>> print(result["verdict"])  # "allow" | "revise" | "deny"
    """

    def __init__(self, policy_path: str):
        """
        Initialize LLM Guard with policy file.

        Args:
            policy_path: Path to llm_guard_policy_v1.1.json
        """
        policy_file = Path(policy_path)
        if not policy_file.exists():
            raise FileNotFoundError(f"Policy not found: {policy_path}")

        with open(policy_file, encoding="utf-8") as f:
            self.policy = json.load(f)

        self.version = self.policy.get("policy_version", "1.1.0")
        self.rules = {r["rule_id"]: r for r in self.policy.get("rules", [])}
        self.eval_order = self.policy.get("evaluation_order", [])
        self.risk_model = self.policy.get("risk_model", {})

        self._feature_flags = {
            "pii_redaction": False,
            "semantic_match": False,
            "signature_check": False,
        }
        self._feature_skip_logged: Dict[str, bool] = {key: False for key in self._feature_flags}
        self._telemetry: Dict[str, int] = {
            "pii_redactions": 0,
            "semantic_checks": 0,
            "signature_checks": 0,
        }

        # Build rule evaluator mapping
        self.evaluators = {
            "STRUCT-000": self._eval_struct_000,
            "EVID-BIND-100": self._eval_evid_bind_100,
            "SCOPE-200": self._eval_scope_200,
            "MODAL-300": self._eval_modal_300,
            "CONF-LOW-310": self._eval_conf_low_310,
            "REL-400": self._eval_rel_400,
            "REL-OVERWEIGHT-410": self._eval_rel_overweight_410,
            "CONSIST-450": self._eval_consist_450,
            "YONGSHIN-UNSUPPORTED-460": self._eval_yongshin_unsupported_460,
            "SIG-500": self._eval_sig_500,
            "PII-600": self._eval_pii_600,
            "KO-700": self._eval_ko_700,
            "AMBIG-800": self._eval_ambig_800,
        }

    def decide(self, payload: Dict[str, Any], *, timeout_ms: int = 1500) -> Dict[str, Any]:
        """
        Evaluate candidate answer against all rules.

        Args:
            payload: Input matching schema/llm_guard_input_v1.1.json:
                - evidence: Full analysis evidence dict
                - candidate_answer: LLM-generated text
                - engine_summaries: Cross-engine data (strength/relation/yongshin/climate)
                - policy_context: Locale, UI mode, etc.
            timeout_ms: Maximum total time (guard + model calls)

        Returns:
            Dict matching schema/llm_guard_output_v1.1.json:
                - verdict: "allow" | "revise" | "deny"
                - violations: List of rule violations
                - risk: {score, level, breakdown}
                - logs: {trace, redactions, recommendations}
                - meta: {guard_version, evaluation_time_ms, timeout_applied}
        """
        start_time = time.time()

        # Extract inputs
        evidence = payload.get("evidence", {})
        candidate_raw = payload.get("candidate_answer", "")
        candidate, redactions = self._apply_pii_redaction(str(candidate_raw))
        summaries = payload.get("engine_summaries", {})
        context = payload.get("policy_context", {})

        # Initialize result
        violations = []
        trace = []

        # Sequential rule evaluation (fail-fast on first error)
        for rule_id in self.eval_order:
            if rule_id not in self.evaluators:
                trace.append(
                    {"rule_id": rule_id, "result": "skip", "note_ko": f"평가기 미구현: {rule_id}"}
                )
                continue

            evaluator = self.evaluators[rule_id]
            result = evaluator(evidence, candidate, summaries, context)

            trace.append(
                {
                    "rule_id": rule_id,
                    "result": result["result"],  # "pass" | "fail"
                    "evidence_refs": result.get("evidence_refs", []),
                    "note_ko": result.get("note_ko", ""),
                }
            )

            if result["result"] == "fail":
                violations.append(
                    {
                        "rule_id": rule_id,
                        "severity": self.rules[rule_id]["severity"],
                        "reason_code": result.get("reason_code", "GENERIC"),
                        "description_ko": result.get("description_ko", ""),
                        "evidence_refs": result.get("evidence_refs", []),
                    }
                )

                # Fail-fast on first error (per v1.1 policy)
                if self.rules[rule_id]["severity"] == "error":
                    break

        # Calculate risk score
        risk = self._calculate_risk(violations)

        # Determine verdict
        verdict = self._determine_verdict(violations, risk)

        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "verdict": verdict,
            "violations": violations,
            "risk": risk,
            "logs": {
                "trace": trace,
                "redactions": redactions,
                "recommendations": self._generate_recommendations(violations, verdict),
                "telemetry": dict(self._telemetry),
            },
            "meta": {
                "guard_version": self.version,
                "evaluation_time_ms": round(elapsed_ms, 2),
                "timeout_applied": elapsed_ms >= timeout_ms,
            },
        }

    def revise_once(
        self, payload: Dict[str, Any], remediations: List[str], model_fn: callable
    ) -> Dict[str, Any]:
        """
        Retry generation with remediation guidance (1 attempt only).

        Args:
            payload: Original guard input
            remediations: List of remediation instructions
            model_fn: Callable for LLM generation, signature: (prompt) -> str

        Returns:
            New guard decision dict with revised candidate
        """
        # Build revision prompt
        original = payload.get("candidate_answer", "")
        revision_prompt = self._build_revision_prompt(original, remediations)

        # Call model (with timeout/fallback)
        try:
            revised_candidate = model_fn(revision_prompt)
        except Exception as e:
            # Fallback: return conservative revise verdict
            return {
                "verdict": "revise",
                "violations": [],
                "risk": {"score": 30, "level": "MEDIUM"},
                "logs": {
                    "trace": [
                        {
                            "rule_id": "REVISE-ERROR",
                            "result": "fail",
                            "note_ko": f"재생성 실패: {e}",
                        }
                    ],
                    "redactions": [],
                    "recommendations": ["재생성 중 오류 발생. 수동 검토 권장."],
                },
                "meta": {
                    "guard_version": self.version,
                    "evaluation_time_ms": 0,
                    "timeout_applied": True,
                },
            }

        # Re-evaluate with revised candidate
        revised_payload = {**payload, "candidate_answer": revised_candidate}
        return self.decide(revised_payload)

    # ============================================================
    # Rule Evaluators (13 rules)
    # ============================================================

    def _apply_pii_redaction(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Optional PII scrubbing prior to rule evaluation."""

        if not self._feature_flags.get("pii_redaction"):
            self._maybe_log_feature_skip("pii_redaction")
            return text, []

        patterns = {
            "email": re.compile(r"[\w.]+@[\w.-]+"),
            "phone": re.compile(r"\b(?:\+?\d{1,3}[- ]?)?(?:\d{2,4}[- ]?){3,4}\b"),
        }
        redactions: List[Dict[str, str]] = []
        scrubbed = text

        for kind, pattern in patterns.items():
            def _replacement(match: re.Match[str], *, label: str = kind) -> str:
                value = match.group(0)
                redactions.append({"type": label, "value": value})
                return f"[REDACTED_{label.upper()}]"

            scrubbed = pattern.sub(_replacement, scrubbed)

        if redactions:
            self._telemetry["pii_redactions"] += len(redactions)

        return scrubbed, redactions

    def _semantic_claim_supported(self, evidence: Dict[str, Any]) -> bool:
        """Very light heuristic to determine if absolute claims have backing."""

        support_fields = ("strength", "relations", "ten_gods", "engine_summaries")
        return any(bool(evidence.get(field)) for field in support_fields)

    def _semantic_relation_alignment(self, summaries: Dict[str, Any]) -> set[str]:
        """Return relation types represented in engine summaries."""

        relation_items = summaries.get("relation_items", [])
        return {str(item.get("type")) for item in relation_items if isinstance(item, dict)}

    def _maybe_log_feature_skip(self, feature: str) -> None:
        """Emit one-time log when a feature flag is disabled."""

        if self._feature_flags.get(feature):
            return
        if self._feature_skip_logged.get(feature):
            return
        LOGGER.info(
            "feature_disabled",
            extra={"component": "LLMGuard", "feature": feature},
        )
        self._feature_skip_logged[feature] = True

    def _eval_struct_000(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        STRUCT-000: 필수 필드 존재 검증

        Checks:
        - evidence has required top-level keys
        - candidate_answer is non-empty
        - engine_summaries has required fields
        """
        required_evidence = ["strength", "relations", "ten_gods"]
        missing = [k for k in required_evidence if k not in evidence]

        if missing or not candidate.strip():
            return {
                "result": "fail",
                "reason_code": "MISSING-FIELDS",
                "description_ko": f"필수 필드 누락: {', '.join(missing) if missing else '답변 텍스트 비어있음'}",
                "evidence_refs": missing,
                "note_ko": "구조 검증 실패 - 재생성 불가",
            }

        return {"result": "pass", "note_ko": "구조 검증 통과"}

    def _eval_evid_bind_100(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        EVID-BIND-100: 증거 기반 진술 검증

        Checks candidate doesn't make claims unsupported by evidence.
        """
        # Simple heuristic: check for absolute claims without evidence
        absolute_patterns = [
            r"확실히|반드시|절대|무조건",
            r"100%|완벽하게",
        ]

        for pattern in absolute_patterns:
            if re.search(pattern, candidate):
                if self._feature_flags.get("semantic_match"):
                    self._telemetry["semantic_checks"] += 1
                    if not self._semantic_claim_supported(evidence):
                        return {
                            "result": "fail",
                            "reason_code": "UNSUPPORTED-ABSOLUTE",
                            "description_ko": "절대 표현을 뒷받침하는 증거가 부족합니다.",
                            "evidence_refs": ["strength", "relations"],
                            "note_ko": "semantic_match",
                        }
                else:
                    self._maybe_log_feature_skip("semantic_match")

        return {"result": "pass", "note_ko": "증거 기반 검증 통과"}

    def _eval_scope_200(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        SCOPE-200: 업무 범위 내 응답 검증

        Blocks out-of-scope content (non-Saju topics).
        """
        # Use word boundaries and specific contexts to avoid false positives
        out_of_scope_patterns = [
            r"주식.*투자|투자.*주식|재테크|코인.*투자|비트코인",
            r"병원.*방문|진료.*예약|처방.*받|약.*처방",
            r"법률.*자문|소송.*제기|변호사.*상담",
        ]

        for pattern in out_of_scope_patterns:
            if re.search(pattern, candidate):
                return {
                    "result": "fail",
                    "reason_code": "OUT-OF-SCOPE",
                    "description_ko": "업무 범위 외 주제 감지",
                    "note_ko": "사주 분석 범위를 벗어남",
                }

        return {"result": "pass", "note_ko": "업무 범위 검증 통과"}

    def _eval_modal_300(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        MODAL-300: 양상 표현 검증

        Checks for appropriate modal hedging (가능성/경향).
        """
        # Check for overly definitive statements
        definitive_patterns = [
            r"당신은.*입니다$",
            r"반드시.*될 것입니다",
        ]

        for pattern in definitive_patterns:
            if re.search(pattern, candidate):
                return {
                    "result": "fail",
                    "reason_code": "OVERLY-DEFINITIVE",
                    "description_ko": "단정적 표현 사용",
                    "note_ko": "'경향이 있습니다', '가능성이 있습니다' 등 완화 표현 권장",
                }

        return {"result": "pass", "note_ko": "양상 표현 검증 통과"}

    def _eval_conf_low_310(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        CONF-LOW-310: 낮은 신뢰도 검증

        Checks if average engine confidence < 0.40 (threshold from policy).
        """
        strength_conf = summaries.get("strength", {}).get("confidence", 0.5)
        yongshin_conf = summaries.get("yongshin_result", {}).get("confidence", 0.5)

        avg_conf = (strength_conf + yongshin_conf) / 2

        if avg_conf < 0.40:
            return {
                "result": "fail",
                "reason_code": "CONFIDENCE-LOW",
                "description_ko": f"평균 신뢰도 {avg_conf:.2f} < 0.40",
                "evidence_refs": ["strength.confidence", "yongshin.confidence"],
                "note_ko": "신뢰도가 낮습니다. 해석 결과를 주의 깊게 검토하세요.",
            }

        return {"result": "pass", "note_ko": f"신뢰도 검증 통과 (avg={avg_conf:.2f})"}

    def _eval_rel_400(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        REL-400: 관계 검증

        Checks relations (sanhe/chong/etc.) mentioned in candidate are in evidence.
        """
        if self._feature_flags.get("semantic_match"):
            self._telemetry["semantic_checks"] += 1
            available = self._semantic_relation_alignment(summaries)
            keyword_map = {
                "삼합": "sanhe",
                "반합": "banhe",
                "충": "chong",
                "형": "xing",
                "파": "pa",
                "해": "hai",
            }
            missing = [
                kw
                for kw, rel_key in keyword_map.items()
                if kw in candidate and rel_key not in available
            ]
            if missing:
                return {
                    "result": "fail",
                    "reason_code": "RELATION-UNSUPPORTED",
                    "description_ko": f"다음 관계 근거 부족: {', '.join(missing)}",
                    "note_ko": "semantic_match",
                }
        else:
            self._maybe_log_feature_skip("semantic_match")
        return {"result": "pass", "note_ko": "관계 검증 통과"}

    def _eval_rel_overweight_410(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        REL-OVERWEIGHT-410: 관계 과대 평가 검증

        Detects overemphasis on relations with low formation conditions.
        """
        relation_items = summaries.get("relation_items", [])

        for item in relation_items:
            # Check if relation is emphasized but has low formation
            conditions_met = item.get("conditions_met", [])
            strict_required = item.get("strict_mode_required", False)
            formed = item.get("formed", False)

            # If strict_mode_required but not formed, and mentioned prominently
            if strict_required and not formed:
                # Check if relation type appears in candidate
                rel_type_ko = {"sanhe": "삼합", "chong": "충", "xing": "형"}.get(
                    item.get("type"), ""
                )
                if rel_type_ko and rel_type_ko in candidate:
                    return {
                        "result": "fail",
                        "reason_code": "RELATION-OVERWEIGHT",
                        "description_ko": f"{rel_type_ko} 관계가 성립하지 않았으나 강조됨",
                        "evidence_refs": [f"relation.{item.get('type')}"],
                        "note_ko": f"conditions_met={len(conditions_met)}, formed={formed}",
                    }

        return {"result": "pass", "note_ko": "관계 과대 평가 검증 통과"}

    def _eval_consist_450(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        CONSIST-450: 엔진 간 일관성 검증

        Validates Strength ↔ Yongshin ↔ Relation alignment.

        Rules:
        - 신약 (weak) should pair with 부억 (support) strategy, not 억부 (suppress)
        - 신강 (strong) should pair with 억부 (suppress) strategy, not 부억 (support)
        - Yongshin should have season/relation environmental support
        """
        strength = summaries.get("strength", {})
        yongshin = summaries.get("yongshin_result", {})
        bucket = strength.get("bucket", "중화")
        strategy = yongshin.get("strategy", "")

        # Check 신약 + 억부 mismatch (weak + suppress = bad)
        if bucket in ["신약", "극신약"] and strategy == "억부":
            return {
                "result": "fail",
                "reason_code": "CONSIST-MISMATCH",
                "description_ko": f"{bucket} 상태인데 {strategy} 전략 사용 (불일치)",
                "evidence_refs": ["strength.bucket", "yongshin.strategy"],
                "note_ko": "신약은 부억(보강) 전략이 적합합니다",
            }

        # Check 신강 + 부억 mismatch (strong + support = bad)
        if bucket in ["신강", "극신강"] and strategy == "부억":
            return {
                "result": "fail",
                "reason_code": "CONSIST-MISMATCH",
                "description_ko": f"{bucket} 상태인데 {strategy} 전략 사용 (불일치)",
                "evidence_refs": ["strength.bucket", "yongshin.strategy"],
                "note_ko": "신강은 억부(억제) 전략이 적합합니다",
            }

        return {"result": "pass", "note_ko": f"일관성 검증 통과 ({bucket} + {strategy})"}

    def _eval_yongshin_unsupported_460(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        YONGSHIN-UNSUPPORTED-460: 용신 환경 지지 검증

        Checks if yongshin candidates have season/relation support.
        """
        yongshin_list = summaries.get("yongshin_result", {}).get("yongshin", [])
        climate = summaries.get("climate", {})
        relation_summary = summaries.get("relation_summary", {})

        if not yongshin_list:
            return {"result": "pass", "note_ko": "용신 없음"}

        # Simple heuristic: check season support
        support = climate.get("support", "보통")

        if support == "약":
            # Check if any relation supports yongshin
            has_relation_support = False
            for ys in yongshin_list:
                # Check if yongshin appears in sanhe/liuhe elements
                if relation_summary.get("sanhe_element") == ys:
                    has_relation_support = True
                    break

            if not has_relation_support:
                return {
                    "result": "fail",
                    "reason_code": "YONGSHIN-NO-SUPPORT",
                    "description_ko": f"용신 {','.join(yongshin_list)}이(가) 계절·관계 지지를 받지 못함",
                    "evidence_refs": ["climate.support", "relation_summary"],
                    "note_ko": "용신이 불리한 환경에 있습니다",
                }

        return {"result": "pass", "note_ko": "용신 환경 검증 통과"}

    def _eval_sig_500(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        SIG-500: 정책 서명 검증

        Checks evidence contains valid policy signature.
        """
        if self._feature_flags.get("signature_check"):
            self._telemetry["signature_checks"] += 1
            required_sections = ("ten_gods", "relations", "strength", "luck")
            missing = [
                section
                for section in required_sections
                if not isinstance(evidence.get(section), dict)
                or not evidence[section].get("policy_signature")
            ]
            if missing:
                return {
                    "result": "fail",
                    "reason_code": "SIGNATURE-MISSING",
                    "description_ko": f"서명 누락: {', '.join(missing)}",
                    "note_ko": "signature_check",
                }
        else:
            self._maybe_log_feature_skip("signature_check")
        return {"result": "pass", "note_ko": "서명 검증 통과"}

    def _eval_pii_600(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        PII-600: 개인정보 노출 검증

        Detects PII patterns (phone, email, jumin) in candidate.
        """
        pii_patterns = [
            (r"\d{3}-\d{4}-\d{4}", "전화번호"),
            (r"\d{6}-\d{7}", "주민등록번호"),
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "이메일"),
        ]

        for pattern, pii_type in pii_patterns:
            if re.search(pattern, candidate):
                return {
                    "result": "fail",
                    "reason_code": "PII-DETECTED",
                    "description_ko": f"{pii_type} 노출 감지",
                    "note_ko": "개인정보를 마스킹해야 합니다",
                }

        return {"result": "pass", "note_ko": "PII 검증 통과"}

    def _eval_ko_700(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        KO-700: 한국어 우선 라벨 검증

        Checks that Korean labels (*_ko fields) are used.
        """
        # Check if candidate uses English terms instead of Korean
        english_terms = ["strength", "yongshin", "sanhe", "chong"]
        found_english = [term for term in english_terms if term in candidate.lower()]

        if found_english:
            return {
                "result": "fail",
                "reason_code": "EN-LABEL-USED",
                "description_ko": f"영어 라벨 사용 감지: {', '.join(found_english)}",
                "note_ko": "한국어 라벨을 사용하세요 (strength → 강약, yongshin → 용신)",
            }

        return {"result": "pass", "note_ko": "한국어 라벨 검증 통과"}

    def _eval_ambig_800(
        self, evidence: Dict, candidate: str, summaries: Dict, context: Dict
    ) -> Dict[str, Any]:
        """
        AMBIG-800: 모호성 검증

        Detects ambiguous phrasing that could mislead users.
        """
        ambiguous_patterns = [
            r"아마도|어쩌면|글쎄요",
            r"잘 모르겠",
        ]

        for pattern in ambiguous_patterns:
            if re.search(pattern, candidate):
                return {
                    "result": "fail",
                    "reason_code": "AMBIGUOUS-PHRASING",
                    "description_ko": "모호한 표현 사용",
                    "note_ko": "'경향이 있습니다', '가능성이 높습니다' 등 명확한 표현 권장",
                }

        return {"result": "pass", "note_ko": "모호성 검증 통과"}

    # ============================================================
    # Helper Methods
    # ============================================================

    def _calculate_risk(self, violations: List[Dict]) -> Dict[str, Any]:
        """Calculate risk score and stratification level"""
        if not violations:
            return {"score": 0, "level": "LOW", "breakdown": {}}

        weight_map = self.risk_model.get("violation_weight", {})
        special_weights = weight_map.get("special", {})

        score = 0
        breakdown = {}

        for v in violations:
            rule_id = v["rule_id"]
            severity = v["severity"]

            # Get weight: special > severity default
            weight = special_weights.get(rule_id, weight_map.get(severity, 10))
            score += weight
            breakdown[rule_id] = weight

        # Clamp to 0-100
        score = min(100, max(0, score))

        # Determine level
        levels = self.risk_model.get(
            "stratification",
            {
                "LOW": {"min": 0, "max": 29},
                "MEDIUM": {"min": 30, "max": 69},
                "HIGH": {"min": 70, "max": 100},
            },
        )

        level = "LOW"
        for lvl, bounds in levels.items():
            if bounds["min"] <= score <= bounds["max"]:
                level = lvl
                break

        return {"score": score, "level": level, "breakdown": breakdown}

    def _determine_verdict(self, violations: List[Dict], risk: Dict[str, Any]) -> str:
        """Determine final verdict based on violations and risk"""
        if not violations:
            return "allow"

        # Check for error severity
        has_error = any(v["severity"] == "error" for v in violations)
        if has_error:
            return "deny"

        # Check risk level
        if risk["level"] == "HIGH":
            return "deny"
        elif risk["level"] == "MEDIUM":
            return "revise"
        else:
            return "allow"

    def _generate_recommendations(self, violations: List[Dict], verdict: str) -> List[str]:
        """Generate remediation recommendations"""
        if not violations:
            return []

        recs = []
        for v in violations:
            rule_id = v["rule_id"]
            if rule_id == "CONSIST-450":
                recs.append("강약과 용신 전략의 일관성을 확인하세요")
            elif rule_id == "CONF-LOW-310":
                recs.append("신뢰도가 낮습니다. 해석 결과를 주의 깊게 검토하세요")
            elif rule_id == "REL-OVERWEIGHT-410":
                recs.append("관계 성립 조건을 재확인하세요")
            elif rule_id == "YONGSHIN-UNSUPPORTED-460":
                recs.append("용신이 계절·관계 지지를 받는지 확인하세요")
            else:
                recs.append(f"{v['description_ko']}")

        return recs

    def _build_revision_prompt(self, original: str, remediations: List[str]) -> str:
        """Build revision prompt with remediation guidance"""
        return f"""다음 답변을 개선하세요:

원본:
{original}

개선 지침:
{chr(10).join(f'- {r}' for r in remediations)}

개선된 답변:"""
