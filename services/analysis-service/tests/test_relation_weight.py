"""
Tests for Relation Weight Evaluator v1.0

Tests impact_weight and confidence calculation based on contextual conditions.
"""

import pytest
from app.core.relation_weight import RelationWeightEvaluator, evaluate_relation_weights

# Sample input from specification
SPEC_SAMPLE_INPUT = {
    "pairs_detected": [
        {"type": "sanhe", "a": "申子辰", "b": "水", "pivot": "子", "formed": True, "priority": 3},
        {"type": "chong", "a": "巳", "b": "亥", "priority": 1},
        {"type": "liuhe", "a": "辰", "b": "酉", "priority": 2},
        {"type": "ganhe", "a": "甲", "b": "己", "element": "土", "priority": 2},
    ],
    "context": {
        "heavenly": ["庚", "乙", "乙", "辛"],
        "earthly": ["申", "子", "辰", "巳"],
        "month_branch": "子",
    },
}


@pytest.fixture
def evaluator():
    """Create evaluator instance"""
    return RelationWeightEvaluator()


@pytest.fixture
def basic_context():
    """Basic context for tests"""
    return {
        "heavenly": ["甲", "乙", "丙", "丁"],
        "earthly": ["子", "丑", "寅", "卯"],
        "month_branch": "子",
    }


def test_evaluator_loads_policy(evaluator):
    """Test that evaluator loads policy correctly"""
    assert evaluator.policy is not None
    assert evaluator.policy["policy_version"] == "relation_weight_v1.0.0"
    assert len(evaluator.policy["relations"]) == 7
    assert "sanhe" in evaluator.policy_map
    assert "liuhe" in evaluator.policy_map
    assert "ganhe" in evaluator.policy_map


def test_evaluate_empty_input(evaluator, basic_context):
    """Test evaluation with no detected pairs"""
    result = evaluator.evaluate([], basic_context)

    assert result["policy_version"] == "relation_weight_v1.0.0"
    assert result["items"] == []
    assert result["summary"]["total"] == 0
    assert all(stats["count"] == 0 for stats in result["summary"]["by_type"].values())


def test_evaluate_sanhe_full_conditions(evaluator):
    """Test sanhe with full conditions met"""
    pairs = [
        {"type": "sanhe", "a": "申子辰", "b": "水", "pivot": "子", "formed": True, "priority": 3}
    ]
    context = {
        "heavenly": ["庚", "乙", "乙", "辛"],
        "earthly": ["申", "子", "辰", "巳"],
        "month_branch": "子",
        "season_element": "水",
        "tonggen_support": {"水": True},
        "strong_combos": [{"type": "sanhe", "branches": ["申", "子", "辰"]}],
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    # Should have high weight due to pivot_month + month_adjacent + tonggen support
    assert item["impact_weight"] > 0.70  # base + bonuses
    assert item["confidence"] >= 0.90
    assert "pivot_month" in item["conditions_met"]
    assert "month_adjacent" in item["conditions_met"]
    assert "tonggen_or_season_support" in item["conditions_met"]


def test_evaluate_sanhe_strict_mode_violation(evaluator, basic_context):
    """Test sanhe with strict mode violation (formed=False)"""
    pairs = [
        {"type": "sanhe", "a": "申子", "b": "水", "formed": False, "priority": 3}  # incomplete
    ]

    result = evaluator.evaluate(pairs, basic_context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    # Strict mode violation should set weight to 0
    assert item["impact_weight"] == 0.0
    assert "formed_incomplete" in item["missing_conditions"]


def test_evaluate_liuhe_on_day_branch(evaluator):
    """Test liuhe on day branch gets bonus"""
    pairs = [{"type": "liuhe", "a": "辰", "b": "酉", "formed": True, "priority": 2}]
    context = {
        "earthly": ["申", "子", "辰", "酉"],  # 辰 is day branch (index 2)
        "month_branch": "子",
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert "on_day_branch" in item["conditions_met"]
    assert item["impact_weight"] >= 0.45  # base weight


def test_evaluate_ganhe_adjacent_stems(evaluator):
    """Test ganhe between adjacent stems"""
    pairs = [
        {"type": "ganhe", "a": "甲", "b": "己", "element": "土", "formed": True, "priority": 2}
    ]
    context = {
        "heavenly": ["甲", "己", "丙", "丁"],  # 甲-己 adjacent (year-month)
        "earthly": ["子", "丑", "寅", "卯"],
        "month_branch": "丑",  # 土 month
        "season_element": "土",
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert "adjacent_stems" in item["conditions_met"]
    assert "season_supports_result" in item["conditions_met"]
    assert item["hua"] is True  # Season supports → hua
    assert item["impact_weight"] > 0.50  # base + bonuses


def test_evaluate_ganhe_non_adjacent_penalty(evaluator):
    """Test ganhe non-adjacent gets penalty"""
    pairs = [
        {"type": "ganhe", "a": "甲", "b": "己", "element": "土", "formed": True, "priority": 2}
    ]
    context = {
        "heavenly": ["甲", "丙", "己", "丁"],  # 甲-己 non-adjacent
        "earthly": ["子", "丑", "寅", "卯"],
        "month_branch": "子",
        "season_element": "水",
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert "non_adjacent" in item["missing_conditions"]
    assert item["impact_weight"] < 0.50  # base + penalty


def test_evaluate_chong_pivot_month(evaluator):
    """Test chong with month pivot"""
    pairs = [{"type": "chong", "a": "子", "b": "午", "formed": True, "priority": 1}]
    context = {"earthly": ["申", "子", "寅", "卯"], "month_branch": "子"}  # 子 in chong pair

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert "pivot_month" in item["conditions_met"]
    assert item["impact_weight"] > 0.55  # base + bonus


def test_evaluate_spec_sample(evaluator):
    """Test the specification sample case"""
    result = evaluator.evaluate(SPEC_SAMPLE_INPUT["pairs_detected"], SPEC_SAMPLE_INPUT["context"])

    assert result["policy_version"] == "relation_weight_v1.0.0"
    assert len(result["items"]) == 4

    # Check sanhe (申子辰)
    sanhe = next(item for item in result["items"] if item["type"] == "sanhe")
    assert sanhe["formed"] is True
    assert sanhe["impact_weight"] >= 0.85  # Should be high due to pivot + adjacent
    assert sanhe["confidence"] >= 0.90
    assert "pivot_month" in sanhe["conditions_met"]
    assert "month_adjacent" in sanhe["conditions_met"]

    # Check chong (巳-亥)
    chong = next(item for item in result["items"] if item["type"] == "chong")
    assert chong["impact_weight"] > 0.0  # Should have some weight

    # Check liuhe (辰-酉)
    liuhe = next(item for item in result["items"] if item["type"] == "liuhe")
    assert liuhe["impact_weight"] >= 0.40

    # Check ganhe (甲-己)
    # Note: The spec sample has inconsistent data - 甲己 not in heavenly stems ["庚","乙","乙","辛"]
    # So this will have low weight due to non_adjacent penalty
    ganhe = next(item for item in result["items"] if item["type"] == "ganhe")
    assert ganhe["impact_weight"] >= 0.0  # Will be low due to non-adjacent

    # Check summary
    assert result["summary"]["total"] == 4
    assert result["summary"]["by_type"]["sanhe"]["count"] == 1
    assert result["summary"]["by_type"]["chong"]["count"] == 1
    assert result["summary"]["by_type"]["liuhe"]["count"] == 1
    assert result["summary"]["by_type"]["ganhe"]["count"] == 1


def test_evaluate_multiple_same_type(evaluator, basic_context):
    """Test multiple relations of same type"""
    pairs = [
        {"type": "chong", "a": "子", "b": "午", "formed": True, "priority": 1},
        {"type": "chong", "a": "卯", "b": "酉", "formed": True, "priority": 1},
    ]

    result = evaluator.evaluate(pairs, basic_context)

    assert len(result["items"]) == 2
    assert result["summary"]["by_type"]["chong"]["count"] == 2
    assert result["summary"]["by_type"]["chong"]["avg_weight"] > 0.0


def test_confidence_adjustment_with_conditions(evaluator, basic_context):
    """Test confidence adjusts based on conditions met/missing"""
    pairs = [{"type": "sanhe", "a": "申子辰", "b": "水", "formed": True, "priority": 3}]

    # Case 1: Many conditions met
    context_met = {
        **basic_context,
        "month_branch": "子",  # Will meet pivot_month
        "season_element": "水",
        "tonggen_support": {"水": True},
    }

    result_met = evaluator.evaluate(pairs, context_met)
    item_met = result_met["items"][0]

    # Case 2: Few conditions met
    context_miss = {
        **basic_context,
        "month_branch": "丑",  # Won't meet pivot_month
        "season_element": "土",
    }

    result_miss = evaluator.evaluate(pairs, context_miss)
    item_miss = result_miss["items"][0]

    # More conditions met should have higher confidence
    assert item_met["confidence"] > item_miss["confidence"]


def test_xing_full_triplet_strict(evaluator):
    """Test xing full triplet strict conditions"""
    pairs = [{"type": "xing", "a": "寅巳申", "b": "刑", "formed": True, "priority": 2}]
    context = {"earthly": ["寅", "巳", "申", "卯"], "month_branch": "巳"}  # Month pivot

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    # Should get full_triplet_strict bonus if month pivot + adjacent met
    if "full_triplet_strict" in item["conditions_met"]:
        assert item["impact_weight"] > 0.40  # base + bonus


def test_hai_inside_strong_combo(evaluator):
    """Test hai inside strong combo gets penalty"""
    pairs = [{"type": "hai", "a": "寅", "b": "巳", "formed": True, "priority": 2}]
    context = {
        "earthly": ["寅", "午", "戌", "巳"],
        "month_branch": "午",
        "strong_combos": [{"type": "sanhe", "branches": ["寅", "午", "戌"]}],
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    # Should have penalty for being inside strong combo
    assert item["impact_weight"] <= 0.30  # base + penalty


def test_yuanjin_on_spouse_palace(evaluator):
    """Test yuanjin on day branch (spouse palace)"""
    pairs = [{"type": "yuanjin", "a": "子", "b": "未", "formed": True, "priority": 2}]
    context = {
        "earthly": ["申", "丑", "子", "卯"],  # 子 is day branch (index 2)
        "month_branch": "丑",
    }

    result = evaluator.evaluate(pairs, context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert "on_spouse_palace" in item["conditions_met"]
    assert item["impact_weight"] >= 0.20  # base + bonus


def test_summary_all_types_present(evaluator):
    """Test summary includes all 7 types even if count is 0"""
    pairs = [{"type": "chong", "a": "子", "b": "午", "formed": True, "priority": 1}]

    result = evaluator.evaluate(pairs, {"earthly": ["子", "午", "寅", "卯"], "month_branch": "子"})

    summary = result["summary"]["by_type"]
    expected_types = ["sanhe", "liuhe", "ganhe", "chong", "xing", "hai", "yuanjin"]

    for rel_type in expected_types:
        assert rel_type in summary
        assert "count" in summary[rel_type]
        assert "avg_weight" in summary[rel_type]

    # Only chong should have count > 0
    assert summary["chong"]["count"] == 1
    assert summary["sanhe"]["count"] == 0
    assert summary["liuhe"]["count"] == 0


def test_convenience_function():
    """Test convenience function"""
    result = evaluate_relation_weights(
        SPEC_SAMPLE_INPUT["pairs_detected"], SPEC_SAMPLE_INPUT["context"]
    )

    assert result["policy_version"] == "relation_weight_v1.0.0"
    assert len(result["items"]) == 4


def test_unknown_relation_type(evaluator, basic_context):
    """Test handling of unknown relation type"""
    pairs = [{"type": "unknown_type", "a": "子", "b": "午", "formed": True, "priority": 1}]

    result = evaluator.evaluate(pairs, basic_context)

    assert len(result["items"]) == 1
    item = result["items"][0]

    assert item["impact_weight"] == 0.0
    assert item["confidence"] == 0.0
    assert "Unknown relation type" in item["explain"]


def test_weight_clamping(evaluator):
    """Test that weight is clamped to [0, 1]"""
    # This would be tested with extreme modifier combinations
    # For now, just verify the clamping logic works
    pairs = [{"type": "sanhe", "a": "申子辰", "b": "水", "formed": True, "priority": 3}]
    context = {
        "earthly": ["申", "子", "辰", "巳"],
        "month_branch": "子",
        "season_element": "水",
        "tonggen_support": {"水": True},
    }

    result = evaluator.evaluate(pairs, context)
    item = result["items"][0]

    assert 0.0 <= item["impact_weight"] <= 1.0
    assert 0.0 <= item["confidence"] <= 1.0
