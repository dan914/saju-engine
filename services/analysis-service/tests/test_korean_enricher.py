"""
Tests for Korean Label Enricher
================================

Test suite for KoreanLabelEnricher class covering all 141 mappings.
"""

from pathlib import Path

import pytest
from .korean_enricher import KoreanLabelEnricher

# Test data paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
POLICY_DIR = REPO_ROOT / "saju_codex_batch_all_v2_6_signed" / "policies"


class TestKoreanLabelEnricherLoading:
    """Test loading of all Korean mappings from policy files."""

    def test_from_files_loads_successfully(self):
        """Test that from_files() loads all mappings without error."""
        enricher = KoreanLabelEnricher.from_files()

        # Verify all mapping dictionaries are populated
        assert len(enricher.ten_gods_ko) == 10
        assert len(enricher.strength_ko) == 5
        assert len(enricher.luck_direction_ko) == 2
        assert len(enricher.confidence_ko) == 4
        assert len(enricher.validity_ko) == 4
        assert len(enricher.pillar_ko) == 4
        assert len(enricher.month_state_ko) == 5
        assert len(enricher.relation_types_ko) == 9

        # Gyeokguk should have 14 items
        assert len(enricher.gyeokguk_ko) >= 14

        # Shensha should have 20 items
        assert len(enricher.shensha_ko) >= 20

        # Jiazi should have 60 items
        assert len(enricher.jiazi_ko) >= 60

    def test_localization_ko_mappings(self):
        """Test specific mappings from localization_ko_v1.json."""
        enricher = KoreanLabelEnricher.from_files()

        # Ten Gods
        assert enricher.ten_gods_ko["BI"] == "비견"
        assert enricher.ten_gods_ko["JG"] == "정관"

        # Strength (전문가 검증 완료)
        assert enricher.strength_ko["very_weak"] == "극신약"
        assert enricher.strength_ko["weak"] == "신약"
        assert enricher.strength_ko["balanced"] == "중화"
        assert enricher.strength_ko["strong"] == "신강"
        assert enricher.strength_ko["very_strong"] == "극신강"

        # Luck Direction
        assert enricher.luck_direction_ko["forward"] == "순행"
        assert enricher.luck_direction_ko["reverse"] == "역행"

        # Confidence (UI probability)
        assert enricher.confidence_ko["high"] == "높음"
        assert enricher.confidence_ko["mid"] == "보통"
        assert enricher.confidence_ko["low"] == "낮음"
        assert enricher.confidence_ko["none"] == "없음"

        # Structure Validity (격국 성립 상태)
        assert enricher.validity_ko["established"] == "성격"
        assert enricher.validity_ko["pseudo"] == "가격"
        assert enricher.validity_ko["broken"] == "파격"
        assert enricher.validity_ko["none"] == "불성립"

        # Pillar (연주 vs 년주)
        assert enricher.pillar_ko["year"] == "연주"
        assert enricher.pillar_ko["month"] == "월주"
        assert enricher.pillar_ko["day"] == "일주"
        assert enricher.pillar_ko["hour"] == "시주"

        # Month State
        assert enricher.month_state_ko["旺"] == "왕"
        assert enricher.month_state_ko["相"] == "상"
        assert enricher.month_state_ko["休"] == "휴"
        assert enricher.month_state_ko["囚"] == "수"
        assert enricher.month_state_ko["死"] == "사"

        # Relation Types (반합 vs 방합 구분)
        assert enricher.relation_types_ko["he6"] == "육합"
        assert enricher.relation_types_ko["sanhe"] == "삼합"
        assert enricher.relation_types_ko["banhe"] == "반합"
        assert enricher.relation_types_ko["fanghe"] == "방합"
        assert enricher.relation_types_ko["chong"] == "충"

        # Recommendation
        assert enricher.recommendation_ko["allow"] == "표시"
        assert enricher.recommendation_ko["suppress"] == "숨김"

    def test_gyeokguk_mappings(self):
        """Test gyeokguk Korean labels from gyeokguk_policy.json."""
        enricher = KoreanLabelEnricher.from_files()

        # Sample gyeokguk mappings
        assert enricher.gyeokguk_ko.get("ZHENGGUAN") == "정관격"
        assert enricher.gyeokguk_ko.get("PIANYIN") == "편인격"

    def test_shensha_mappings(self):
        """Test shensha Korean labels from shensha_v2_policy.json."""
        enricher = KoreanLabelEnricher.from_files()

        # Sample shensha mappings
        assert enricher.shensha_ko.get("TIAN_E_GUIREN") == "천을귀인"

    def test_jiazi_mappings(self):
        """Test sixty jiazi Korean labels from sixty_jiazi.json."""
        enricher = KoreanLabelEnricher.from_files()

        # Sample jiazi mappings
        assert enricher.jiazi_ko.get("JIAZI") == "갑자"
        assert enricher.jiazi_ko.get("YICHOU") == "을축"


class TestKoreanLabelEnricherEnrichment:
    """Test enrichment of various payload sections."""

    @pytest.fixture
    def enricher(self):
        """Fixture to provide enricher instance."""
        return KoreanLabelEnricher.from_files()

    def test_enrich_strength(self, enricher):
        """Test strength enrichment with all 5 levels."""
        payloads = [
            {"strength": {"level": "very_weak"}},
            {"strength": {"level": "weak"}},
            {"strength": {"level": "balanced"}},
            {"strength": {"level": "strong"}},
            {"strength": {"level": "very_strong"}},
        ]

        expected = ["극신약", "신약", "중화", "신강", "극신강"]

        for payload, expected_ko in zip(payloads, expected):
            enriched = enricher.enrich(payload)
            assert enriched["strength"]["level_ko"] == expected_ko
            # Original value preserved
            assert enriched["strength"]["level"] == payload["strength"]["level"]

    def test_enrich_luck_direction(self, enricher):
        """Test luck direction enrichment."""
        payload = {"luck_direction": {"direction": "forward"}}
        enriched = enricher.enrich(payload)

        assert enriched["luck_direction"]["direction"] == "forward"
        assert enriched["luck_direction"]["direction_ko"] == "순행"

        payload = {"luck_direction": {"direction": "reverse"}}
        enriched = enricher.enrich(payload)

        assert enriched["luck_direction"]["direction"] == "reverse"
        assert enriched["luck_direction"]["direction_ko"] == "역행"

    def test_enrich_confidence_and_validity_separate(self, enricher):
        """Test that confidence and validity are separate fields (expert warning)."""
        payload = {
            "structure": {
                "primary": "ZHENGGUAN",
                "confidence": "high",
                "validity": "established",
            }
        }

        enriched = enricher.enrich(payload)

        # Confidence (UI probability)
        assert enriched["structure"]["confidence"] == "high"
        assert enriched["structure"]["confidence_ko"] == "높음"

        # Validity (격국 성립 상태)
        assert enriched["structure"]["validity"] == "established"
        assert enriched["structure"]["validity_ko"] == "성격"

        # Primary structure
        assert enriched["structure"]["primary"] == "ZHENGGUAN"
        assert enriched["structure"]["primary_ko"] == "정관격"

    def test_enrich_shensha_with_pillar(self, enricher):
        """Test shensha enrichment with pillar labels."""
        payload = {
            "shensha": {
                "list": [
                    {"key": "TIAN_E_GUIREN", "pillar": "year"},
                    {"key": "TIAN_E_GUIREN", "pillar": "month"},
                ]
            }
        }

        enriched = enricher.enrich(payload)

        assert len(enriched["shensha"]["list"]) == 2

        # First entry
        assert enriched["shensha"]["list"][0]["key"] == "TIAN_E_GUIREN"
        assert enriched["shensha"]["list"][0]["label_ko"] == "천을귀인"
        assert enriched["shensha"]["list"][0]["pillar"] == "year"
        assert enriched["shensha"]["list"][0]["pillar_ko"] == "연주"

        # Second entry
        assert enriched["shensha"]["list"][1]["pillar"] == "month"
        assert enriched["shensha"]["list"][1]["pillar_ko"] == "월주"

    def test_enrich_relations_with_type_and_pillars(self, enricher):
        """Test relations enrichment (반합 vs 방합 구분)."""
        payload = {
            "relations": {
                "list": [
                    {"type": "banhe", "pillars": ["year", "month"]},
                    {"type": "fanghe", "pillars": ["day", "hour"]},
                ]
            }
        }

        enriched = enricher.enrich(payload)

        # First relation: 반합 (半合) not 방합!
        assert enriched["relations"]["list"][0]["type"] == "banhe"
        assert enriched["relations"]["list"][0]["type_ko"] == "반합"
        assert enriched["relations"]["list"][0]["pillars_ko"] == ["연주", "월주"]

        # Second relation: 방합 (方合)
        assert enriched["relations"]["list"][1]["type"] == "fanghe"
        assert enriched["relations"]["list"][1]["type_ko"] == "방합"
        assert enriched["relations"]["list"][1]["pillars_ko"] == ["일주", "시주"]

    def test_enrich_ten_gods_in_branch_tengods(self, enricher):
        """Test ten gods enrichment in branch_tengods section."""
        payload = {
            "branch_tengods": {
                "year": {
                    "roles": [
                        {"tengod": "BI", "role": "primary"},
                        {"tengod": "JG", "role": "secondary"},
                    ]
                }
            }
        }

        enriched = enricher.enrich(payload)

        roles = enriched["branch_tengods"]["year"]["roles"]
        assert roles[0]["tengod"] == "BI"
        assert roles[0]["tengod_ko"] == "비견"
        assert roles[0]["role"] == "primary"
        assert roles[0]["role_ko"] == "본기"

        assert roles[1]["tengod"] == "JG"
        assert roles[1]["tengod_ko"] == "정관"
        assert roles[1]["role"] == "secondary"
        assert roles[1]["role_ko"] == "중기"

    def test_enrich_pillars_with_jiazi(self, enricher):
        """Test pillar enrichment with jiazi labels."""
        payload = {
            "pillars": {
                "year": {"jiazi": "JIAZI", "stem": "JIA", "branch": "ZI"},
                "month": {"jiazi": "YICHOU", "stem": "YI", "branch": "CHOU"},
            }
        }

        enriched = enricher.enrich(payload)

        # Year pillar
        assert enriched["pillars"]["year"]["pillar_ko"] == "연주"
        assert enriched["pillars"]["year"]["jiazi"] == "JIAZI"
        assert enriched["pillars"]["year"]["jiazi_ko"] == "갑자"

        # Month pillar
        assert enriched["pillars"]["month"]["pillar_ko"] == "월주"
        assert enriched["pillars"]["month"]["jiazi"] == "YICHOU"
        assert enriched["pillars"]["month"]["jiazi_ko"] == "을축"

    def test_enrich_recommendation(self, enricher):
        """Test recommendation enrichment."""
        payload = {"recommendation": {"action": "allow"}}
        enriched = enricher.enrich(payload)

        assert enriched["recommendation"]["action"] == "allow"
        assert enriched["recommendation"]["action_ko"] == "표시"

        payload = {"recommendation": {"action": "suppress"}}
        enriched = enricher.enrich(payload)

        assert enriched["recommendation"]["action"] == "suppress"
        assert enriched["recommendation"]["action_ko"] == "숨김"

    def test_enrich_missing_mapping_preserves_original(self, enricher):
        """Test that missing mappings preserve original values (graceful degradation)."""
        payload = {
            "strength": {"level": "UNKNOWN_LEVEL"},
            "shensha": {"list": [{"key": "UNKNOWN_SHENSHA", "pillar": "year"}]},
        }

        enriched = enricher.enrich(payload)

        # Missing strength mapping
        assert enriched["strength"]["level"] == "UNKNOWN_LEVEL"
        assert enriched["strength"]["level_ko"] == "UNKNOWN_LEVEL"

        # Missing shensha mapping
        assert enriched["shensha"]["list"][0]["key"] == "UNKNOWN_SHENSHA"
        assert enriched["shensha"]["list"][0]["label_ko"] == "UNKNOWN_SHENSHA"

    def test_enrich_adds_metadata(self, enricher):
        """Test that enrichment adds metadata."""
        payload = {"strength": {"level": "weak"}}
        enriched = enricher.enrich(payload)

        assert "_enrichment" in enriched
        assert enriched["_enrichment"]["korean_labels_added"] is True
        assert enriched["_enrichment"]["locale"] == "ko-KR"
        assert enriched["_enrichment"]["enricher_version"] == "1.0.0"
        assert enriched["_enrichment"]["mappings_count"] == 141

    def test_enrich_does_not_modify_original(self, enricher):
        """Test that enrichment does not modify original payload."""
        original = {"strength": {"level": "weak"}}
        enriched = enricher.enrich(original)

        # Original should not have *_ko fields
        assert "level_ko" not in original["strength"]
        assert "_enrichment" not in original

        # Enriched should have *_ko fields
        assert enriched["strength"]["level_ko"] == "신약"
        assert "_enrichment" in enriched


class TestKoreanLabelEnricherEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def enricher(self):
        """Fixture to provide enricher instance."""
        return KoreanLabelEnricher.from_files()

    def test_enrich_empty_payload(self, enricher):
        """Test enrichment of empty payload."""
        payload = {}
        enriched = enricher.enrich(payload)

        # Should only add metadata
        assert "_enrichment" in enriched
        assert len(enriched) == 1

    def test_enrich_nested_structures(self, enricher):
        """Test enrichment preserves nested structures."""
        payload = {
            "structure": {
                "primary": "ZHENGGUAN",
                "nested": {"deep": {"value": "test"}},
            }
        }

        enriched = enricher.enrich(payload)

        # Nested structure preserved
        assert enriched["structure"]["nested"]["deep"]["value"] == "test"

    def test_enrich_list_types(self, enricher):
        """Test enrichment handles list types correctly."""
        payload = {
            "shensha": {
                "list": [
                    {"key": "TIAN_E_GUIREN", "pillar": "year"},
                    {"key": "TIAN_E_GUIREN", "pillar": "month"},
                    {"key": "TIAN_E_GUIREN", "pillar": "day"},
                ]
            }
        }

        enriched = enricher.enrich(payload)

        assert len(enriched["shensha"]["list"]) == 3
        for entry in enriched["shensha"]["list"]:
            assert "label_ko" in entry
            assert "pillar_ko" in entry


class TestLLMGuardIntegration:
    """Test integration with LLMGuard."""

    def test_llm_guard_default_loads_enricher(self):
        """Test that LLMGuard.default() loads KoreanLabelEnricher."""
        from app.core.llm_guard import LLMGuard

        guard = LLMGuard.default()
        assert guard.korean_enricher is not None
        assert isinstance(guard.korean_enricher, KoreanLabelEnricher)

    def test_llm_guard_prepare_payload_enriches(self):
        """Test that LLMGuard.prepare_payload() enriches with Korean labels."""
        from app.core.engine import AnalysisEngine
        from app.core.llm_guard import LLMGuard

        from .helpers import build_sample_request

        # Use real engine to create a valid AnalysisResponse
        engine = AnalysisEngine()
        request = build_sample_request()
        response = engine.analyze(request)

        guard = LLMGuard.default()
        payload = guard.prepare_payload(response)

        # Should have enrichment metadata
        assert "_enrichment" in payload
        assert payload["_enrichment"]["korean_labels_added"] is True
        assert payload["_enrichment"]["locale"] == "ko-KR"
        assert payload["_enrichment"]["mappings_count"] == 141

        # Should have Korean labels in strength if present
        if "level" in payload.get("strength", {}):
            assert "level_ko" in payload["strength"]
