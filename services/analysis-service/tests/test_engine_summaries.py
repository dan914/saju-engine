"""
Tests for EngineSummariesBuilder - LLM Guard v1.1 Engine Summaries Pipeline

Tests verify:
1. Correct structure generation from individual engine outputs
2. Relation summary aggregation (max weights per type)
3. Element extraction (sanhe_element, ganhe_result)
4. Score normalization (0-100 → 0-1)
5. Schema compliance with llm_guard_input_v1.1.json
"""

import pytest
from .engine_summaries import EngineSummariesBuilder


class TestEngineSummariesBuilder:
    """Test suite for EngineSummariesBuilder"""

    def test_build_basic_structure(self):
        """Test basic structure generation with minimal inputs"""
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={"score": 0.65, "bucket": "중화", "confidence": 0.8},
            relation_items=[],
            yongshin={"yongshin": ["木"], "bojosin": ["水"], "confidence": 0.75},
            climate={"season_element": "火", "support": "강"},
        )

        # Verify top-level structure
        assert "strength" in result
        assert "relation_summary" in result
        assert "relation_items" in result
        assert "yongshin_result" in result
        assert "climate" in result

        # Verify strength
        assert result["strength"]["score"] == 0.65
        assert result["strength"]["bucket"] == "중화"
        assert result["strength"]["confidence"] == 0.8

        # Verify yongshin
        assert result["yongshin_result"]["yongshin"] == ["木"]
        assert result["yongshin_result"]["bojosin"] == ["水"]
        assert result["yongshin_result"]["confidence"] == 0.75

        # Verify climate
        assert result["climate"]["season_element"] == "火"
        assert result["climate"]["support"] == "강"

    def test_relation_summary_aggregation(self):
        """Test relation summary correctly aggregates max weights per type"""
        builder = EngineSummariesBuilder()

        relation_items = [
            {"type": "sanhe", "impact_weight": 0.70, "element": "金"},
            {"type": "sanhe", "impact_weight": 0.50, "element": "水"},  # Lower, should be ignored
            {"type": "chong", "impact_weight": 0.60},
            {"type": "xing", "impact_weight": 0.40},
        ]

        result = builder.build(
            strength={"score": 0.5},
            relation_items=relation_items,
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        summary = result["relation_summary"]
        assert summary["sanhe"] == 0.70  # Max of 0.70 and 0.50
        assert summary["chong"] == 0.60
        assert summary["xing"] == 0.40
        assert summary["liuhe"] == 0.0  # Not present
        assert summary["ganhe"] == 0.0  # Not present

    def test_sanhe_element_extraction(self):
        """Test sanhe_element extracted from first sanhe relation"""
        builder = EngineSummariesBuilder()

        relation_items = [
            {"type": "sanhe", "impact_weight": 0.70, "element": "金"},
            {"type": "sanhe", "impact_weight": 0.80, "element": "水"},  # Higher weight but second
        ]

        result = builder.build(
            strength={"score": 0.5},
            relation_items=relation_items,
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        # Should take first sanhe, not highest weight
        assert result["relation_summary"]["sanhe_element"] == "金"

    def test_ganhe_hua_result_extraction(self):
        """Test ganhe_result extracted only when hua=True"""
        builder = EngineSummariesBuilder()

        relation_items = [
            {"type": "ganhe", "impact_weight": 0.50, "hua": False, "element": "木"},  # Should skip
            {"type": "ganhe", "impact_weight": 0.70, "hua": True, "element": "金"},  # Should use
        ]

        result = builder.build(
            strength={"score": 0.5},
            relation_items=relation_items,
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        assert result["relation_summary"]["ganhe_result"] == "金"

    def test_score_normalization_0_to_100(self):
        """Test strength score normalized from 0-100 to 0-1"""
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={"score": 65},  # 0-100 scale
            relation_items=[],
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        assert result["strength"]["score"] == 0.65

    def test_score_already_normalized(self):
        """Test strength score unchanged if already 0-1"""
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={"score": 0.65},  # Already 0-1 scale
            relation_items=[],
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        assert result["strength"]["score"] == 0.65

    def test_default_values(self):
        """Test default values applied for missing fields"""
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={},  # Missing all fields
            relation_items=[],
            yongshin={},  # Missing all fields
            climate={},  # Missing all fields
        )

        # Verify defaults
        assert result["strength"]["score"] == 0.5
        assert result["strength"]["bucket"] == "중화"
        assert result["strength"]["confidence"] == 0.5

        assert result["yongshin_result"]["yongshin"] == []
        assert result["yongshin_result"]["bojosin"] == []
        assert result["yongshin_result"]["confidence"] == 0.5
        assert result["yongshin_result"]["strategy"] == ""

        assert result["climate"]["season_element"] == ""
        assert result["climate"]["support"] == "보통"

    def test_relation_items_passthrough(self):
        """Test relation_items passed through unchanged for detailed validation"""
        builder = EngineSummariesBuilder()

        relation_items = [
            {"type": "sanhe", "impact_weight": 0.70, "positions": [0, 4, 8], "extra_field": "test"}
        ]

        result = builder.build(
            strength={"score": 0.5},
            relation_items=relation_items,
            yongshin={"yongshin": []},
            climate={"season_element": ""},
        )

        # Should preserve all original fields
        assert result["relation_items"] == relation_items
        assert result["relation_items"][0]["extra_field"] == "test"

    def test_신약_consistency_scenario(self):
        """
        Test 신약 (weak day master) scenario for CONSIST-450 validation.

        Expected: 신약 should pair with 부억 (support) strategy, not 억부 (suppress).
        """
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={"score": 25, "bucket": "신약", "confidence": 0.8},
            relation_items=[{"type": "sanhe", "impact_weight": 0.70, "element": "木"}],
            yongshin={
                "yongshin": ["木", "水"],
                "bojosin": [],
                "confidence": 0.75,
                "strategy": "부억",
            },
            climate={"season_element": "火", "support": "약"},
        )

        # This scenario should PASS CONSIST-450 (신약 + 부억 = consistent)
        assert result["strength"]["score"] == 0.25
        assert result["strength"]["bucket"] == "신약"
        assert result["yongshin_result"]["strategy"] == "부억"

    def test_신강_consistency_scenario(self):
        """
        Test 신강 (strong day master) scenario for CONSIST-450 validation.

        Expected: 신강 should pair with 억부 (suppress) strategy, not 부억 (support).
        """
        builder = EngineSummariesBuilder()

        result = builder.build(
            strength={"score": 75, "bucket": "신강", "confidence": 0.8},
            relation_items=[{"type": "chong", "impact_weight": 0.60}],
            yongshin={
                "yongshin": ["金"],
                "bojosin": ["水"],
                "confidence": 0.70,
                "strategy": "억부",
            },
            climate={"season_element": "木", "support": "강"},
        )

        # This scenario should PASS CONSIST-450 (신강 + 억부 = consistent)
        assert result["strength"]["score"] == 0.75
        assert result["strength"]["bucket"] == "신강"
        assert result["yongshin_result"]["strategy"] == "억부"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
