"""
Integration Tests for LLM Guard v1.1 - New Rules (CONF-LOW-310, REL-OVERWEIGHT-410, CONSIST-450, YONGSHIN-UNSUPPORTED-460)

Tests verify:
1. Cross-engine consistency validation (CONSIST-450)
2. Low confidence detection (CONF-LOW-310)
3. Relation overweight detection (REL-OVERWEIGHT-410)
4. Yongshin environmental support (YONGSHIN-UNSUPPORTED-460)
5. Risk scoring and verdict determination
"""

import pytest
from app.guard.llm_guard_v1_1 import LLMGuardV11


@pytest.fixture
def guard():
    """Create LLMGuardV11 instance with v1.1 policy"""
    return LLMGuardV11("policy/llm_guard_policy_v1.1.json")


class TestLLMGuardV11NewRules:
    """Test suite for 4 new v1.1 rules"""

    def test_conf_low_310_triggers_on_low_confidence(self, guard):
        """CONF-LOW-310: Should trigger when avg confidence < 0.40"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.3},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {"yongshin": [], "confidence": 0.35},
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should trigger CONF-LOW-310 (avg = (0.3 + 0.35) / 2 = 0.325 < 0.40)
        violations = [v for v in result["violations"] if v["rule_id"] == "CONF-LOW-310"]
        assert len(violations) == 1
        assert violations[0]["severity"] == "warn"
        assert violations[0]["reason_code"] == "CONFIDENCE-LOW"

        # With only warn severity and weight=10, risk should be LOW, verdict=allow
        assert result["risk"]["level"] == "LOW"
        assert result["risk"]["score"] == 10

    def test_conf_low_310_passes_on_high_confidence(self, guard):
        """CONF-LOW-310: Should pass when avg confidence >= 0.40"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {"yongshin": [], "confidence": 0.75},
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should NOT trigger CONF-LOW-310 (avg = (0.8 + 0.75) / 2 = 0.775 >= 0.40)
        assert not any(v["rule_id"] == "CONF-LOW-310" for v in result["violations"])

    def test_consist_450_신약_with_억부_fails(self, guard):
        """CONSIST-450: 신약 + 억부 should fail (mismatch)"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.25, "bucket": "신약", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {
                    "yongshin": ["金"],
                    "confidence": 0.75,
                    "strategy": "억부",  # Suppress strategy - wrong for weak
                },
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should trigger CONSIST-450
        violations = [v for v in result["violations"] if v["rule_id"] == "CONSIST-450"]
        assert len(violations) == 1
        assert violations[0]["reason_code"] == "CONSIST-MISMATCH"
        assert "신약" in violations[0]["description_ko"]
        assert "억부" in violations[0]["description_ko"]

    def test_consist_450_신약_with_부억_passes(self, guard):
        """CONSIST-450: 신약 + 부억 should pass (consistent)"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.25, "bucket": "신약", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {
                    "yongshin": ["木", "水"],
                    "confidence": 0.75,
                    "strategy": "부억",  # Support strategy - correct for weak
                },
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should NOT trigger CONSIST-450
        assert not any(v["rule_id"] == "CONSIST-450" for v in result["violations"])
        assert result["verdict"] == "allow"

    def test_consist_450_신강_with_부억_fails(self, guard):
        """CONSIST-450: 신강 + 부억 should fail (mismatch)"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.75, "bucket": "신강", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {
                    "yongshin": ["木"],
                    "confidence": 0.70,
                    "strategy": "부억",  # Support strategy - wrong for strong
                },
                "climate": {"season_element": "水", "support": "강"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should trigger CONSIST-450
        violations = [v for v in result["violations"] if v["rule_id"] == "CONSIST-450"]
        assert len(violations) == 1
        assert "신강" in violations[0]["description_ko"]
        assert "부억" in violations[0]["description_ko"]

    def test_consist_450_신강_with_억부_passes(self, guard):
        """CONSIST-450: 신강 + 억부 should pass (consistent)"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.75, "bucket": "신강", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {
                    "yongshin": ["金", "水"],
                    "confidence": 0.70,
                    "strategy": "억부",  # Suppress strategy - correct for strong
                },
                "climate": {"season_element": "水", "support": "강"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should NOT trigger CONSIST-450
        assert not any(v["rule_id"] == "CONSIST-450" for v in result["violations"])
        assert result["verdict"] == "allow"

    def test_rel_overweight_410_triggers_on_unformed_relation(self, guard):
        """REL-OVERWEIGHT-410: Should fail when emphasizing unformed relation"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "삼합 관계가 강하게 작용합니다",  # Emphasizes sanhe
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {"sanhe": 0.5},
                "relation_items": [
                    {
                        "type": "sanhe",
                        "impact_weight": 0.5,
                        "conditions_met": ["지지위치"],  # Only 1 condition
                        "strict_mode_required": True,
                        "formed": False,  # Not formed!
                    }
                ],
                "yongshin_result": {"yongshin": [], "confidence": 0.75},
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should trigger REL-OVERWEIGHT-410
        violations = [v for v in result["violations"] if v["rule_id"] == "REL-OVERWEIGHT-410"]
        assert len(violations) == 1
        assert violations[0]["reason_code"] == "RELATION-OVERWEIGHT"

    def test_rel_overweight_410_passes_on_formed_relation(self, guard):
        """REL-OVERWEIGHT-410: Should pass when relation is formed"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "삼합 관계가 강하게 작용합니다",
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {"sanhe": 0.7},
                "relation_items": [
                    {
                        "type": "sanhe",
                        "impact_weight": 0.7,
                        "conditions_met": ["지지위치", "천간투출", "월령"],
                        "strict_mode_required": True,
                        "formed": True,  # Formed!
                    }
                ],
                "yongshin_result": {"yongshin": [], "confidence": 0.75},
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should NOT trigger REL-OVERWEIGHT-410
        assert not any(v["rule_id"] == "REL-OVERWEIGHT-410" for v in result["violations"])

    def test_yongshin_unsupported_460_triggers_on_weak_support(self, guard):
        """YONGSHIN-UNSUPPORTED-460: Should fail when yongshin lacks environmental support"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {"sanhe_element": "金"},  # Different from yongshin
                "relation_items": [],
                "yongshin_result": {"yongshin": ["木"], "confidence": 0.70},  # No relation support
                "climate": {"season_element": "火", "support": "약"},  # Weak support!
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should trigger YONGSHIN-UNSUPPORTED-460
        violations = [v for v in result["violations"] if v["rule_id"] == "YONGSHIN-UNSUPPORTED-460"]
        assert len(violations) == 1
        assert violations[0]["reason_code"] == "YONGSHIN-NO-SUPPORT"

    def test_yongshin_unsupported_460_passes_with_relation_support(self, guard):
        """YONGSHIN-UNSUPPORTED-460: Should pass when yongshin has relation support"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.5, "bucket": "중화", "confidence": 0.8},
                "relation_summary": {"sanhe_element": "木"},  # Matches yongshin!
                "relation_items": [],
                "yongshin_result": {"yongshin": ["木"], "confidence": 0.70},
                "climate": {
                    "season_element": "火",
                    "support": "약",  # Weak climate, but has relation support
                },
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Should NOT trigger YONGSHIN-UNSUPPORTED-460
        assert not any(v["rule_id"] == "YONGSHIN-UNSUPPORTED-460" for v in result["violations"])

    def test_risk_scoring_and_verdict(self, guard):
        """Test risk scoring calculates correctly and determines verdict"""
        payload = {
            "evidence": {"strength": {}, "relations": {}, "ten_gods": {}},
            "candidate_answer": "테스트 답변",
            "engine_summaries": {
                "strength": {"score": 0.25, "bucket": "신약", "confidence": 0.8},
                "relation_summary": {},
                "relation_items": [],
                "yongshin_result": {
                    "yongshin": ["金"],
                    "confidence": 0.75,
                    "strategy": "억부",  # Triggers CONSIST-450
                },
                "climate": {"season_element": "火", "support": "보통"},
            },
            "policy_context": {"locale": "ko-KR"},
        }

        result = guard.decide(payload)

        # Verify risk structure
        assert "risk" in result
        assert "score" in result["risk"]
        assert "level" in result["risk"]
        assert "breakdown" in result["risk"]

        # CONSIST-450 has special weight of 28 (per policy v1.1)
        assert result["risk"]["score"] > 0
        assert result["risk"]["level"] in ["LOW", "MEDIUM", "HIGH"]

        # Should have recommendations
        assert len(result["logs"]["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
