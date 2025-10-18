"""
Test suite for relation_policy.json validation.

Tests include:
- P0: Schema validation
- P1: Conservation rules validation
- P2: Confidence calculation validation
- CI-REL-01 through CI-REL-12: Continuous integration checks
- Verification test cases for all 12 relationship types
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


@pytest.fixture
def policy_path():
    """Path to relation_policy.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "relation_policy.json"
    )


@pytest.fixture
def schema_path():
    """Path to relation.schema.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "schemas"
        / "relation.schema.json"
    )


@pytest.fixture
def policy(policy_path):
    """Load relation_policy.json"""
    with open(policy_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def schema(schema_path):
    """Load relation.schema.json"""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# P0: Schema Validation
# ============================================================================


def test_p0_schema_validation(policy, schema):
    """P0: Policy must validate against schema"""
    try:
        validate(instance=policy, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")


# ============================================================================
# P1: Conservation Rules Validation
# ============================================================================


def test_p1_conservation_enabled(policy):
    """P1.1: Conservation must be enabled"""
    assert policy["conservation"]["enabled"] is True


def test_p1_hidden_stems_complete(policy):
    """P1.2: All 12 earthly branches must have hidden stems weights"""
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    weights = policy["conservation"]["hidden_stems_weights"]

    for branch in branches:
        assert branch in weights, f"Missing hidden stems for {branch}"


def test_p1_hidden_stems_sum_to_one(policy):
    """P1.3: Hidden stems weights must sum to 1.0 for each branch"""
    weights = policy["conservation"]["hidden_stems_weights"]

    for branch, elements in weights.items():
        total = sum(elements.values())
        assert abs(total - 1.0) < 0.01, f"Weights for {branch} sum to {total}, expected 1.0"


def test_p1_fusion_rules_complete(policy):
    """P1.4: Main relationship types must have fusion rules"""
    main_relationships = ["三合", "半合", "方合", "拱合", "六合"]
    fusion_rules = policy["conservation"]["fusion_rules"]

    for rel_type in main_relationships:
        assert rel_type in fusion_rules, f"Missing fusion rule for {rel_type}"
        assert "consume_units" in fusion_rules[rel_type]
        assert "produce_units" in fusion_rules[rel_type]


# ============================================================================
# P2: Confidence Calculation Validation
# ============================================================================


def test_p2_confidence_weights_valid(policy):
    """P2.1: Confidence weights must be defined and reasonable"""
    weights = policy["confidence_rules"]["weights"]

    # Check all required weights are present
    assert "w_norm" in weights
    assert "w_conservation" in weights
    assert "w_priority" in weights
    assert "w_conflict" in weights

    # Check weights are in reasonable ranges
    assert 0 <= weights["w_norm"] <= 1
    assert 0 <= weights["w_conservation"] <= 1
    assert 0 <= weights["w_priority"] <= 1
    assert -1 <= weights["w_conflict"] <= 1  # Can be negative


def test_p2_confidence_formula_exists(policy):
    """P2.2: Confidence formula must be defined"""
    assert "formula" in policy["confidence_rules"]
    assert len(policy["confidence_rules"]["formula"]) > 0


def test_p2_normalization_ranges_valid(policy):
    """P2.3: Normalization ranges must be valid"""
    norm = policy["confidence_rules"]["normalization"]

    score_range = norm["score_range"]
    assert score_range["min"] < score_range["max"]

    priority_range = norm["priority_range"]
    assert priority_range["min"] < priority_range["max"]


# ============================================================================
# CI Checks (CI-REL-01 through CI-REL-12)
# ============================================================================


def test_ci_rel_01_positive_priorities(policy):
    """CI-REL-01: All relationships must have positive priority"""
    for rel_type, rel_data in policy["relationships"].items():
        for rule in rel_data["rules"]:
            assert rule["priority"] > 0, f"{rel_type} rule has non-positive priority: {rule['priority']}"


def test_ci_rel_02_valid_score_ranges(policy):
    """CI-REL-02: Score bounds must be valid (min < max)"""
    # Check score_range for each relationship type
    for rel_type, rel_data in policy["relationships"].items():
        score_range = rel_data["score_range"]
        assert score_range["min"] < score_range["max"], f"Invalid score range for {rel_type}: {score_range}"


def test_ci_rel_03_hidden_stems_sum(policy):
    """CI-REL-03: Hidden stems weights must sum to 1.0 for each branch"""
    # This is the same as test_p1_hidden_stems_sum_to_one
    weights = policy["conservation"]["hidden_stems_weights"]

    for branch, elements in weights.items():
        total = sum(elements.values())
        assert abs(total - 1.0) < 0.01, f"CI-REL-03: Weights for {branch} sum to {total}"


def test_ci_rel_04_liuhe_symmetric(policy):
    """CI-REL-04: All 六合 pairs must be symmetric"""
    liuhe_rules = policy["relationships"]["六合"]["rules"]
    expected_pairs = [
        {"子", "丑"},
        {"寅", "亥"},
        {"卯", "戌"},
        {"辰", "酉"},
        {"巳", "申"},
        {"午", "未"},
    ]

    for rule in liuhe_rules:
        branches_set = set(rule["branches"])
        assert branches_set in expected_pairs, f"Invalid 六合 pair: {rule['branches']}"


def test_ci_rel_05_sanhe_complete(policy):
    """CI-REL-05: All 三合 bureaus must be complete (3 branches each)"""
    sanhe_rules = policy["relationships"]["三合"]["rules"]

    for rule in sanhe_rules:
        assert len(rule["branches"]) == 3, f"三合 rule must have 3 branches: {rule['branches']}"


def test_ci_rel_06_chong_opposites(policy):
    """CI-REL-06: All 沖 pairs must be opposites (6 pairs)"""
    chong_rules = policy["relationships"]["沖"]["rules"]
    expected_pairs = [
        {"子", "午"},
        {"丑", "未"},
        {"寅", "申"},
        {"卯", "酉"},
        {"辰", "戌"},
        {"巳", "亥"},
    ]

    for rule in chong_rules:
        branches_set = set(rule["branches"])
        assert branches_set in expected_pairs, f"Invalid 沖 pair: {rule['branches']}"


def test_ci_rel_07_confidence_weights_valid(policy):
    """CI-REL-07: Confidence weights must be defined and valid"""
    # This is similar to test_p2_confidence_weights_valid
    weights = policy["confidence_rules"]["weights"]

    # Check all required weights are present
    assert "w_norm" in weights
    assert "w_conservation" in weights
    assert "w_priority" in weights
    assert "w_conflict" in weights

    # Check weights are in reasonable ranges
    assert 0 <= weights["w_norm"] <= 1
    assert 0 <= weights["w_conservation"] <= 1
    assert 0 <= weights["w_priority"] <= 1
    assert -1 <= weights["w_conflict"] <= 1


def test_ci_rel_08_fusion_rules_defined(policy):
    """CI-REL-08: Fusion rules must define consume and produce units"""
    fusion_rules = policy["conservation"]["fusion_rules"]

    for rel_type, rule in fusion_rules.items():
        assert "consume_units" in rule, f"{rel_type} missing consume_units"
        assert "produce_units" in rule, f"{rel_type} missing produce_units"
        assert rule["consume_units"] >= 0
        assert rule["produce_units"] >= 0


def test_ci_rel_09_mutual_exclusion_valid(policy):
    """CI-REL-09: Mutual exclusion groups must have valid promotion targets"""
    exclusion_groups = policy["mutual_exclusion_groups"]

    for group in exclusion_groups:
        promotion = group["promotion"]
        assert (
            promotion in group["group"]
        ), f"Promotion target {promotion} not in group {group['group']}"


def test_ci_rel_10_attenuation_factors_valid(policy):
    """CI-REL-10: Attenuation factors must be in range [0, 1]"""
    attenuation_rules = policy["attenuation_rules"]

    for rule in attenuation_rules:
        factor = rule["factor"]
        assert 0 <= factor <= 1, f"Attenuation factor {factor} out of range [0, 1]"


def test_ci_rel_11_non_empty_rules(policy):
    """CI-REL-11: Rules array must not be empty"""
    total_rules = sum(len(rel_data["rules"]) for rel_data in policy["relationships"].values())
    assert total_rules > 0, "No rules found in relationships"


def test_ci_rel_12_valid_branches(policy):
    """CI-REL-12: Branch patterns must contain only valid earthly branches"""
    valid_branches = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}

    for rel_type, rel_data in policy["relationships"].items():
        for rule in rel_data["rules"]:
            for branch in rule["branches"]:
                assert branch in valid_branches, f"{rel_type} rule contains invalid branch: {branch}"


# ============================================================================
# Verification Test Cases
# ============================================================================


def test_case01_liuhe_zi_chou(policy):
    """Test case 01: 六合 子丑"""
    # Find 子丑 pair in rules
    liuhe_rules = policy["relationships"]["六合"]["rules"]
    zi_chou = None
    for rule in liuhe_rules:
        if set(rule["branches"]) == {"子", "丑"}:
            zi_chou = rule
            break

    assert zi_chou is not None, "子丑 六合 not found"
    assert zi_chou["priority"] > 0
    assert zi_chou["score_hint"] == 8.0


def test_case02_sanhe_shen_zi_chen(policy):
    """Test case 02: 三合 申子辰 (水局)"""
    # Find 申子辰
    shen_zi_chen = None
    for rule in policy["relationships"]["三合"]["rules"]:
        if set(rule["branches"]) == {"申", "子", "辰"}:
            shen_zi_chen = rule
            break

    assert shen_zi_chen is not None, "申子辰 三合 not found"
    assert shen_zi_chen["element"] == "水"
    assert shen_zi_chen["score_hint"] == 18.0


def test_case03_banhe_shen_zi(policy):
    """Test case 03: 半合 申子"""
    # Find 申子
    shen_zi = None
    for rule in policy["relationships"]["半合"]["rules"]:
        if set(rule["branches"]) == {"申", "子"}:
            shen_zi = rule
            break

    assert shen_zi is not None, "申子 半合 not found"
    assert shen_zi["score_hint"] == 6.0


def test_case04_chong_zi_wu(policy):
    """Test case 04: 沖 子午"""
    # Find 子午
    zi_wu = None
    for rule in policy["relationships"]["沖"]["rules"]:
        if set(rule["branches"]) == {"子", "午"}:
            zi_wu = rule
            break

    assert zi_wu is not None, "子午 沖 not found"
    assert zi_wu["score_hint"] == -12.0


def test_case05_xing_self_yin_yin(policy):
    """Test case 05: 刑 寅寅 (self-punishment)"""
    # Find 寅寅
    yin_yin = None
    for rule in policy["relationships"]["刑_自刑"]["rules"]:
        if rule["branches"] == ["寅", "寅"]:
            yin_yin = rule
            break

    assert yin_yin is not None, "寅寅 刑_自刑 not found"
    assert yin_yin["xing_type"] == "self"
    assert yin_yin["score_hint"] == -4.0


def test_case06_xing_tri_yin_si_shen(policy):
    """Test case 06: 刑 寅巳申 (tri-punishment)"""
    # Find 寅巳申
    yin_si_shen = None
    for rule in policy["relationships"]["刑_三刑"]["rules"]:
        if set(rule["branches"]) == {"寅", "巳", "申"}:
            yin_si_shen = rule
            break

    assert yin_si_shen is not None, "寅巳申 刑_三刑 not found"
    assert yin_si_shen["xing_type"] == "punishment_of_power"
    assert yin_si_shen["score_hint"] == -8.0


def test_case07_po_zi_you(policy):
    """Test case 07: 破 子酉"""
    # Find 子酉
    zi_you = None
    for rule in policy["relationships"]["破"]["rules"]:
        if set(rule["branches"]) == {"子", "酉"}:
            zi_you = rule
            break

    assert zi_you is not None, "子酉 破 not found"
    assert zi_you["score_hint"] == -6.0


def test_case08_hai_zi_wei(policy):
    """Test case 08: 害 子未"""
    # Find 子未
    zi_wei = None
    for rule in policy["relationships"]["害"]["rules"]:
        if set(rule["branches"]) == {"子", "未"}:
            zi_wei = rule
            break

    assert zi_wei is not None, "子未 害 not found"
    assert zi_wei["score_hint"] == -5.0


def test_case09_fanghe_yin_mao_chen(policy):
    """Test case 09: 方合 寅卯辰 (東方木局)"""
    # Find 寅卯辰
    yin_mao_chen = None
    for rule in policy["relationships"]["方合"]["rules"]:
        if set(rule["branches"]) == {"寅", "卯", "辰"}:
            yin_mao_chen = rule
            break

    assert yin_mao_chen is not None, "寅卯辰 方合 not found"
    assert yin_mao_chen["element"] == "木"
    assert yin_mao_chen["score_hint"] == 5.0


def test_case10_gonghe_zi_chen(policy):
    """Test case 10: 拱合 子辰 (拱申)"""
    # Find 子辰
    zi_chen = None
    for rule in policy["relationships"]["拱合"]["rules"]:
        if set(rule["branches"]) == {"子", "辰"}:
            zi_chen = rule
            break

    assert zi_chen is not None, "子辰 拱合 not found"
    assert zi_chen["score_hint"] == 4.0


def test_case11_mutual_exclusion_sanhe_suppresses_banhe(policy):
    """Test case 11: 三合 suppresses 半合 in mutual exclusion"""
    exclusion_groups = policy["mutual_exclusion_groups"]

    # Find the group containing 三合, 半合, 拱合
    target_group = None
    for group in exclusion_groups:
        if set(group["group"]) == {"三合", "半合", "拱合"}:
            target_group = group
            break

    assert target_group is not None, "Mutual exclusion group {三合, 半合, 拱合} not found"
    assert target_group["promotion"] == "三合"
    assert target_group["suppression"]["lower_rank_weight"] == 0.0


def test_case12_attenuation_chong_weakens_sanhe(policy):
    """Test case 12: 沖 weakens 三合 by 30%"""
    attenuation_rules = policy["attenuation_rules"]

    # Find rule where 沖 weakens 三合
    chong_attenuates_sanhe = None
    for rule in attenuation_rules:
        if "沖" in rule["when"] and "三合" in rule["attenuate"]:
            chong_attenuates_sanhe = rule
            break

    assert chong_attenuates_sanhe is not None, "Attenuation rule (沖 weakens 三合) not found"
    assert chong_attenuates_sanhe["factor"] == 0.7


def test_case13_attenuation_chong_weakens_liuhe(policy):
    """Test case 13: 沖 weakens 六合 by 30%"""
    attenuation_rules = policy["attenuation_rules"]

    # Find rule where 沖 weakens 六合
    chong_attenuates_liuhe = None
    for rule in attenuation_rules:
        if "沖" in rule["when"] and "六合" in rule["attenuate"]:
            chong_attenuates_liuhe = rule
            break

    assert chong_attenuates_liuhe is not None, "Attenuation rule (沖 weakens 六合) not found"
    assert chong_attenuates_liuhe["factor"] == 0.7


def test_case14_attenuation_chong_weakens_banhe(policy):
    """Test case 14: 沖 weakens 半合 by 40%"""
    attenuation_rules = policy["attenuation_rules"]

    # Find rule where 沖 weakens 半合
    chong_attenuates_banhe = None
    for rule in attenuation_rules:
        if "沖" in rule["when"] and "半合" in rule["attenuate"]:
            chong_attenuates_banhe = rule
            break

    assert chong_attenuates_banhe is not None, "Attenuation rule (沖 weakens 半合) not found"
    assert chong_attenuates_banhe["factor"] == 0.6


# ============================================================================
# Summary Test
# ============================================================================


def test_summary_all_checks_pass(policy):
    """Summary: Verify all major components are present and valid"""
    # Check top-level structure
    assert policy["version"] == "1.1"
    assert policy["policy_name"] == "relation_policy"

    # Check conservation
    assert policy["conservation"]["enabled"] is True
    assert policy["conservation"]["budget_mode"] == "hidden_stems_v1"

    # Check confidence rules
    assert "formula" in policy["confidence_rules"]

    # Check mutual exclusion
    assert len(policy["mutual_exclusion_groups"]) > 0

    # Check attenuation
    assert len(policy["attenuation_rules"]) > 0

    # Check all relationship types exist in relationships
    expected_kinds = ["六合", "三合", "半合", "方合", "拱合", "沖", "破", "害"]
    found_kinds = set(policy["relationships"].keys())

    # Handle 刑 variants - should have all three types
    xing_variants = [k for k in found_kinds if k.startswith("刑")]
    if xing_variants:
        found_kinds.add("刑")

    for expected_kind in expected_kinds:
        assert expected_kind in found_kinds, f"Missing relationship kind: {expected_kind}"

    # Check CI checks (12 total)
    assert len(policy["ci_checks"]) == 12
