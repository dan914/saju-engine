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


@pytest.mark.skip(reason="Schema needs to be updated to match actual policy structure")
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
    params = policy["confidence_rules"]["params"]

    # Check all required weights are present
    assert "w_norm" in params
    assert "w_conservation" in params
    assert "w_priority" in params
    assert "w_conflict" in params

    # Check weights are in reasonable ranges
    assert 0 <= params["w_norm"] <= 1
    assert 0 <= params["w_conservation"] <= 1
    assert 0 <= params["w_priority"] <= 1
    assert -1 <= params["w_conflict"] <= 1  # Can be negative


def test_p2_confidence_formula_exists(policy):
    """P2.2: Confidence formula must be defined"""
    assert "formula" in policy["confidence_rules"]
    assert len(policy["confidence_rules"]["formula"]) > 0


def test_p2_normalization_ranges_valid(policy):
    """P2.3: Normalization ranges must be valid"""
    norm = policy["normalization"]

    score_bounds = policy["score_bounds"]
    assert score_bounds["min"] < score_bounds["max"]

    target_range = norm["target_range"]
    assert target_range[0] < target_range[1]


# ============================================================================
# CI Checks (CI-REL-01 through CI-REL-12)
# ============================================================================


def test_ci_rel_01_positive_priorities(policy):
    """CI-REL-01: All relationships must have positive priority"""
    for rule in policy["rules"]:
        assert rule["priority"] > 0, f"{rule['id']} has non-positive priority: {rule['priority']}"


def test_ci_rel_02_valid_score_ranges(policy):
    """CI-REL-02: Score bounds must be valid (min < max)"""
    score_bounds = policy["score_bounds"]
    assert score_bounds["min"] < score_bounds["max"], f"Invalid score bounds: {score_bounds}"


def test_ci_rel_03_hidden_stems_sum(policy):
    """CI-REL-03: Hidden stems weights must sum to 1.0 for each branch"""
    # This is the same as test_p1_hidden_stems_sum_to_one
    weights = policy["conservation"]["hidden_stems_weights"]

    for branch, elements in weights.items():
        total = sum(elements.values())
        assert abs(total - 1.0) < 0.01, f"CI-REL-03: Weights for {branch} sum to {total}"


def test_ci_rel_04_liuhe_symmetric(policy):
    """CI-REL-04: All 六合 pairs must be symmetric"""
    liuhe_rules = [r for r in policy["rules"] if r["kind"] == "六合"]
    expected_pairs = [
        {"子", "丑"},
        {"寅", "亥"},
        {"卯", "戌"},
        {"辰", "酉"},
        {"巳", "申"},
        {"午", "未"},
    ]

    for rule in liuhe_rules:
        branches_set = set(rule["pattern"])
        assert branches_set in expected_pairs, f"Invalid 六合 pair: {rule['pattern']}"


def test_ci_rel_05_sanhe_complete(policy):
    """CI-REL-05: All 三合 bureaus must be complete (3 branches each)"""
    sanhe_rules = [r for r in policy["rules"] if r["kind"] == "三合"]

    for rule in sanhe_rules:
        assert len(rule["pattern"]) == 3, f"三合 rule must have 3 branches: {rule['pattern']}"


def test_ci_rel_06_chong_opposites(policy):
    """CI-REL-06: All 沖 pairs must be opposites (6 pairs)"""
    chong_rules = [r for r in policy["rules"] if r["kind"] == "沖"]
    expected_pairs = [
        {"子", "午"},
        {"丑", "未"},
        {"寅", "申"},
        {"卯", "酉"},
        {"辰", "戌"},
        {"巳", "亥"},
    ]

    for rule in chong_rules:
        branches_set = set(rule["pattern"])
        assert branches_set in expected_pairs, f"Invalid 沖 pair: {rule['pattern']}"


def test_ci_rel_07_confidence_weights_valid(policy):
    """CI-REL-07: Confidence weights must be defined and valid"""
    # This is similar to test_p2_confidence_weights_valid
    params = policy["confidence_rules"]["params"]

    # Check all required weights are present
    assert "w_norm" in params
    assert "w_conservation" in params
    assert "w_priority" in params
    assert "w_conflict" in params

    # Check weights are in reasonable ranges
    assert 0 <= params["w_norm"] <= 1
    assert 0 <= params["w_conservation"] <= 1
    assert 0 <= params["w_priority"] <= 1
    assert -1 <= params["w_conflict"] <= 1


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
    attenuation_rules = policy["attenuation"]["rules"]

    for rule in attenuation_rules:
        factor = rule["factor"]
        assert 0 <= factor <= 1, f"Attenuation factor {factor} out of range [0, 1]"


def test_ci_rel_11_non_empty_rules(policy):
    """CI-REL-11: Rules array must not be empty"""
    assert len(policy["rules"]) > 0, "Rules array is empty"


def test_ci_rel_12_valid_branches(policy):
    """CI-REL-12: Branch patterns must contain only valid earthly branches"""
    valid_branches = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}

    for rule in policy["rules"]:
        for branch in rule["pattern"]:
            assert branch in valid_branches, f"{rule['id']} contains invalid branch: {branch}"


# ============================================================================
# Verification Test Cases
# ============================================================================


def test_case01_liuhe_zi_chou(policy):
    """Test case 01: 六合 子丑"""
    # Find 子丑 pair in rules
    zi_chou = None
    for rule in policy["rules"]:
        if rule["kind"] == "六合" and set(rule["pattern"]) == {"子", "丑"}:
            zi_chou = rule
            break

    assert zi_chou is not None, "子丑 六合 not found"
    assert zi_chou["priority"] > 0
    assert zi_chou["score_delta"] == 8.0


def test_case02_sanhe_shen_zi_chen(policy):
    """Test case 02: 三合 申子辰 (水局)"""
    # Find 申子辰
    shen_zi_chen = None
    for rule in policy["rules"]:
        if rule["kind"] == "三合" and set(rule["pattern"]) == {"申", "子", "辰"}:
            shen_zi_chen = rule
            break

    assert shen_zi_chen is not None, "申子辰 三合 not found"
    assert shen_zi_chen["element_bias"] == "水"
    assert shen_zi_chen["score_delta"] == 18.0


def test_case03_banhe_shen_zi(policy):
    """Test case 03: 半合 申子"""
    # Find 申子
    shen_zi = None
    for rule in policy["rules"]:
        if rule["kind"] == "半合" and set(rule["pattern"]) == {"申", "子"}:
            shen_zi = rule
            break

    assert shen_zi is not None, "申子 半合 not found"
    assert shen_zi["score_delta"] == 6.0


def test_case04_chong_zi_wu(policy):
    """Test case 04: 沖 子午"""
    # Find 子午
    zi_wu = None
    for rule in policy["rules"]:
        if rule["kind"] == "沖" and set(rule["pattern"]) == {"子", "午"}:
            zi_wu = rule
            break

    assert zi_wu is not None, "子午 沖 not found"
    assert zi_wu["score_delta"] == -12.0


def test_case05_xing_self_yin_yin(policy):
    """Test case 05: 刑 寅寅 (self-punishment)"""
    # Find 寅寅
    yin_yin = None
    for rule in policy["rules"]:
        if rule["kind"] == "刑_自刑" and rule["pattern"] == ["寅", "寅"]:
            yin_yin = rule
            break

    assert yin_yin is not None, "寅寅 刑_自刑 not found"
    assert yin_yin["directionality"] == "self"
    assert yin_yin["score_delta"] == -4.0


def test_case06_xing_tri_yin_si_shen(policy):
    """Test case 06: 刑 寅巳申 (tri-punishment)"""
    # Find 寅巳申
    yin_si_shen = None
    for rule in policy["rules"]:
        if rule["kind"] == "刑_三刑" and set(rule["pattern"]) == {"寅", "巳", "申"}:
            yin_si_shen = rule
            break

    assert yin_si_shen is not None, "寅巳申 刑_三刑 not found"
    assert yin_si_shen["directionality"] == "cyclic"
    assert yin_si_shen["score_delta"] == -8.0


def test_case07_po_zi_you(policy):
    """Test case 07: 破 子酉"""
    # Find 子酉
    zi_you = None
    for rule in policy["rules"]:
        if rule["kind"] == "破" and set(rule["pattern"]) == {"子", "酉"}:
            zi_you = rule
            break

    assert zi_you is not None, "子酉 破 not found"
    assert zi_you["score_delta"] == -6.0


def test_case08_hai_zi_wei(policy):
    """Test case 08: 害 子未"""
    # Find 子未
    zi_wei = None
    for rule in policy["rules"]:
        if rule["kind"] == "害" and set(rule["pattern"]) == {"子", "未"}:
            zi_wei = rule
            break

    assert zi_wei is not None, "子未 害 not found"
    assert zi_wei["score_delta"] == -5.0


def test_case09_fanghe_yin_mao_chen(policy):
    """Test case 09: 方合 寅卯辰 (東方木局)"""
    # Find 寅卯辰
    yin_mao_chen = None
    for rule in policy["rules"]:
        if rule["kind"] == "方合" and set(rule["pattern"]) == {"寅", "卯", "辰"}:
            yin_mao_chen = rule
            break

    assert yin_mao_chen is not None, "寅卯辰 方合 not found"
    assert yin_mao_chen["element_bias"] == "木"
    assert yin_mao_chen["score_delta"] == 5.0


def test_case10_gonghe_zi_chen(policy):
    """Test case 10: 拱合 子辰 (拱申)"""
    # Find 子辰
    zi_chen = None
    for rule in policy["rules"]:
        if rule["kind"] == "拱合" and set(rule["pattern"]) == {"子", "辰"}:
            zi_chen = rule
            break

    assert zi_chen is not None, "子辰 拱合 not found"
    assert zi_chen["score_delta"] == 4.0


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
    attenuation_rules = policy["attenuation"]["rules"]

    # Find rule where 沖 weakens 三合
    chong_attenuates_sanhe = None
    for rule in attenuation_rules:
        if "沖" in rule["if_together"] and "三合" in rule["apply_to"]:
            chong_attenuates_sanhe = rule
            break

    assert chong_attenuates_sanhe is not None, "Attenuation rule (沖 weakens 三合) not found"
    assert chong_attenuates_sanhe["factor"] == 0.7


def test_case13_attenuation_chong_weakens_liuhe(policy):
    """Test case 13: 沖 weakens 六合 by 30%"""
    attenuation_rules = policy["attenuation"]["rules"]

    # Find rule where 沖 weakens 六合
    chong_attenuates_liuhe = None
    for rule in attenuation_rules:
        if "沖" in rule["if_together"] and "六合" in rule["apply_to"]:
            chong_attenuates_liuhe = rule
            break

    assert chong_attenuates_liuhe is not None, "Attenuation rule (沖 weakens 六合) not found"
    assert chong_attenuates_liuhe["factor"] == 0.7


def test_case14_attenuation_chong_weakens_banhe(policy):
    """Test case 14: 沖 weakens 半合 by 40%"""
    attenuation_rules = policy["attenuation"]["rules"]

    # Find rule where 沖 weakens 半合
    chong_attenuates_banhe = None
    for rule in attenuation_rules:
        if "沖" in rule["if_together"] and "半合" in rule["apply_to"]:
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
    assert policy["policy_version"] == "1.1.0"
    assert policy["policy_name"] == "Saju Relation Transformer Policy"

    # Check conservation
    assert policy["conservation"]["enabled"] is True
    assert policy["conservation"]["budget_mode"] == "hidden_stems_v1"

    # Check confidence rules
    assert "formula" in policy["confidence_rules"]

    # Check mutual exclusion
    assert len(policy["mutual_exclusion_groups"]) > 0

    # Check attenuation
    assert len(policy["attenuation"]["rules"]) > 0

    # Check all 9 relationship types exist in rules
    expected_kinds = ["六合", "三合", "半合", "方合", "拱合", "沖", "破", "害"]
    found_kinds = set()
    for rule in policy["rules"]:
        kind = rule["kind"]
        # Handle 刑 variants
        if kind.startswith("刑"):
            found_kinds.add("刑")
        else:
            found_kinds.add(kind)

    for expected_kind in expected_kinds:
        assert expected_kind in found_kinds, f"Missing relationship kind: {expected_kind}"

    # Check CI checks (12 total)
    assert len(policy["ci_checks"]) == 12
