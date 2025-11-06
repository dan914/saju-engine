"""
Test suite for gyeokguk_policy.json validation.

Tests include:
- P0: Schema, required fields, locale, determinism
- P1: Normalization, priority, confidence
- P2: KO-first, integration compatibility
- Property-based tests (P1-P10)
- Concrete test cases (Case 01-14)

Based on test_gyeokguk_properties.md and test_gyeokguk_cases.md specifications.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def gyeokguk_policy_path():
    """Path to gyeokguk_policy.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "gyeokguk_policy.json"
    )


@pytest.fixture
def gyeokguk_schema_path():
    """Path to gyeokguk.schema.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "schemas"
        / "gyeokguk.schema.json"
    )


@pytest.fixture
def gyeokguk_policy(gyeokguk_policy_path):
    """Load gyeokguk_policy.json"""
    with open(gyeokguk_policy_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def gyeokguk_schema(gyeokguk_schema_path):
    """Load gyeokguk.schema.json"""
    with open(gyeokguk_schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# P0: Core Structure / Required Fields / Locale
# ============================================================================


def test_p0_gyeokguk_policy_structure(gyeokguk_policy):
    """P0: Gyeokguk policy has required top-level fields"""
    required_fields = [
        "module",
        "policy_version",
        "policy_signature",
        "locale_default",
        "labels",
        "dependencies",
        "scoring",
        "priority",
        "tie_breakers",
        "confidence",
        "selectors",
        "relation_codes",
        "patterns",
    ]

    for field in required_fields:
        assert field in gyeokguk_policy, f"Missing required field: {field}"


def test_p0_module_name(gyeokguk_policy):
    """P0: Module name must be gyeokguk_v1.0"""
    assert gyeokguk_policy["module"] == "gyeokguk_v1.0"


def test_p0_locale_default_ko(gyeokguk_policy):
    """P0: Default locale must be ko-KR"""
    assert gyeokguk_policy["locale_default"] == "ko-KR"


def test_p0_labels_ko_complete(gyeokguk_policy):
    """P0: All labels must include Korean"""
    labels = gyeokguk_policy["labels"]
    assert "ko" in labels
    assert len(labels["ko"]) > 0


def test_p0_patterns_count(gyeokguk_policy):
    """P0: Must have 14 patterns (8 CORE + 2 PEER + 4 CONG)"""
    patterns = gyeokguk_policy["patterns"]
    assert len(patterns) == 14

    # Count by family
    core_count = sum(1 for p in patterns if p["family"] == "CORE")
    peer_count = sum(1 for p in patterns if p["family"] == "PEER")
    cong_count = sum(1 for p in patterns if p["family"] == "CONG")

    assert core_count == 8, "Should have 8 CORE patterns"
    assert peer_count == 2, "Should have 2 PEER patterns"
    assert cong_count == 4, "Should have 4 CONG patterns"


def test_p0_pattern_codes_unique(gyeokguk_policy):
    """P0: All pattern codes must be unique"""
    patterns = gyeokguk_policy["patterns"]
    codes = [p["code"] for p in patterns]
    assert len(codes) == len(set(codes)), "Pattern codes must be unique"


# ============================================================================
# P0: Pattern Structure
# ============================================================================


def test_p0_core_patterns_complete(gyeokguk_policy):
    """P0: All 8 CORE patterns must be present"""
    patterns = gyeokguk_policy["patterns"]
    core_codes = {p["code"] for p in patterns if p["family"] == "CORE"}

    required_core = {
        "ZHENGGUAN",
        "QISHA",
        "ZHENGCAI",
        "PIANCAI",
        "SHISHEN",
        "SHANGGUAN",
        "YINSHOU",
        "PIANYIN",
    }

    assert required_core.issubset(
        core_codes
    ), f"Missing CORE patterns: {required_core - core_codes}"


def test_p0_cong_patterns_have_gating(gyeokguk_policy):
    """P0: All CONG patterns must have gating conditions"""
    patterns = gyeokguk_policy["patterns"]
    cong_patterns = [p for p in patterns if p["family"] == "CONG"]

    for pattern in cong_patterns:
        assert "gating" in pattern, f"CONG pattern {pattern['code']} missing gating"
        assert "conditions" in pattern["gating"]
        assert len(pattern["gating"]["conditions"]) > 0


def test_p0_pattern_label_ko_complete(gyeokguk_policy):
    """P0: All patterns must have label_ko"""
    patterns = gyeokguk_policy["patterns"]

    for pattern in patterns:
        assert "label_ko" in pattern, f"Pattern {pattern['code']} missing label_ko"
        assert len(pattern["label_ko"]) > 0


# ============================================================================
# P0: Scoring / Normalization
# ============================================================================


def test_p0_scoring_normalization_valid(gyeokguk_policy):
    """P0: Normalization must use min_max with bounds [0, 100]"""
    scoring = gyeokguk_policy["scoring"]
    norm = scoring["normalization"]

    assert norm["kind"] == "min_max"
    assert norm["bounds"] == [0, 100]
    assert "params" in norm
    assert "min_raw" in norm["params"]
    assert "max_raw" in norm["params"]


def test_p0_status_thresholds_ordered(gyeokguk_policy):
    """P0: Status thresholds must be properly ordered"""
    thresholds = gyeokguk_policy["scoring"]["status_thresholds"]

    assert "成格" in thresholds
    assert "假格" in thresholds
    assert "破格" in thresholds

    # 成格 requires higher score than 假格
    assert thresholds["成格"]["min_score"] > thresholds["假格"]["min_score"]


# ============================================================================
# P0: Priority / Tie-breakers
# ============================================================================


def test_p0_priority_families_defined(gyeokguk_policy):
    """P0: Priority families must be defined"""
    priority = gyeokguk_policy["priority"]

    assert "families" in priority
    assert len(priority["families"]) > 0

    # CONG should have highest priority
    assert priority["families"][0] == "CONG"


def test_p0_tie_breakers_complete(gyeokguk_policy):
    """P0: All 5 tie-breakers must be defined"""
    tie_breakers = gyeokguk_policy["tie_breakers"]

    assert len(tie_breakers) == 5

    # Check all required fields
    for tb in tie_breakers:
        assert "id" in tb
        assert "label_ko" in tb
        assert "key" in tb
        assert "direction" in tb


# ============================================================================
# P0: Confidence / Relation Codes
# ============================================================================


def test_p0_confidence_formula_exists(gyeokguk_policy):
    """P0: Confidence formula must be defined"""
    confidence = gyeokguk_policy["confidence"]

    assert "formula" in confidence
    assert "metrics" in confidence
    assert len(confidence["metrics"]) == 4

    # Required metrics
    required_metrics = ["condition_coverage", "strength_fit", "month_command_fit", "consistency"]
    for metric in required_metrics:
        assert metric in confidence["metrics"]


def test_p0_relation_codes_complete(gyeokguk_policy):
    """P0: Relation codes must have supportive/penalty/breaker"""
    rel_codes = gyeokguk_policy["relation_codes"]

    assert "supportive" in rel_codes
    assert "penalty" in rel_codes
    assert "breaker" in rel_codes

    assert len(rel_codes["supportive"]) >= 6
    assert len(rel_codes["penalty"]) >= 5
    assert len(rel_codes["breaker"]) >= 3


# ============================================================================
# P1: Normalization Bounds
# ============================================================================


def test_p1_normalization_bounds_valid():
    """P1: Test normalization bounds property"""
    # Given raw scores from -30 to +30
    # Then normalized scores should be in [0, 100]

    min_raw = -30.0
    max_raw = 30.0

    def normalize(raw):
        return ((raw - min_raw) / (max_raw - min_raw)) * 100.0

    # Test boundary values
    assert normalize(-30.0) == 0.0
    assert normalize(0.0) == 50.0
    assert normalize(30.0) == 100.0

    # Test range
    for raw in [-30, -15, 0, 15, 30]:
        norm = normalize(raw)
        assert 0.0 <= norm <= 100.0


# ============================================================================
# P1: Pattern Rule Weights
# ============================================================================


def test_p1_core_condition_weights_reasonable(gyeokguk_policy):
    """P1: Core condition weights should be reasonable"""
    patterns = gyeokguk_policy["patterns"]

    for pattern in patterns:
        core = pattern["core"]
        if "conditions" in core:
            for cond in core["conditions"]:
                if "weight" in cond:
                    # Weights should be positive and reasonable (typically 1-20)
                    assert 0 < cond["weight"] <= 20.0


def test_p1_bonus_penalty_scores_reasonable(gyeokguk_policy):
    """P1: Bonus/penalty scores should be reasonable"""
    patterns = gyeokguk_policy["patterns"]

    for pattern in patterns:
        # Check bonuses
        if "bonuses" in pattern:
            for bonus in pattern["bonuses"]:
                if "score" in bonus:
                    assert (
                        0 < bonus["score"] <= 10.0
                    ), f"Bonus score out of range in {pattern['code']}"

        # Check penalties
        if "penalties" in pattern:
            for penalty in pattern["penalties"]:
                if "score" in penalty:
                    assert (
                        -15.0 <= penalty["score"] < 0
                    ), f"Penalty score out of range in {pattern['code']}"


# ============================================================================
# P2: KO-first / Integration
# ============================================================================


def test_p2_ko_first_enforced(gyeokguk_policy):
    """P2: KO-first must be enforced throughout"""
    # Check top-level labels
    assert "ko" in gyeokguk_policy["labels"]

    # Check all patterns
    patterns = gyeokguk_policy["patterns"]
    for pattern in patterns:
        assert "label_ko" in pattern

        # Check core notes
        if "notes_ko" in pattern["core"]:
            assert len(pattern["core"]["notes_ko"]) > 0

        # Check bonuses
        if "bonuses" in pattern:
            for bonus in pattern["bonuses"]:
                if "notes_ko" in bonus:
                    assert len(bonus["notes_ko"]) > 0


def test_p2_dependencies_required_complete(gyeokguk_policy):
    """P2: All required dependencies must be specified"""
    deps = gyeokguk_policy["dependencies"]["modules"]
    required_names = {
        "strength_v2",
        "branch_tengods_v1.1",
        "relation_v1.0",
        "elemental_projection_policy",
    }

    actual_names = {dep["name"] for dep in deps}
    assert required_names.issubset(actual_names)


def test_p2_ci_checks_complete(gyeokguk_policy):
    """P2: All critical CI checks must be defined"""
    ci_checks = gyeokguk_policy["ci_checks"]
    check_ids = {check["id"] for check in ci_checks}

    critical_checks = {
        "CI-KO-FIRST",
        "CI-NORM-BOUNDS",
        "CI-PRIORITY-CONSISTENCY",
        "CI-CONG-GATING",
        "CI-DET-HASH",
    }

    assert critical_checks.issubset(check_ids)


# ============================================================================
# Property-based Tests (from test_gyeokguk_properties.md)
# ============================================================================


def test_property_p3_priority_ladder_determinism(gyeokguk_policy):
    """P3: Priority → Tie-breaker ladder must be deterministic"""
    tie_breakers = gyeokguk_policy["tie_breakers"]

    # Check order is maintained
    assert tie_breakers[0]["id"] == "TB-1"  # family_priority
    assert tie_breakers[1]["id"] == "TB-2"  # score_normalized
    assert tie_breakers[2]["id"] == "TB-3"  # month_command_fit
    assert tie_breakers[3]["id"] == "TB-4"  # yongshin_alignment
    assert tie_breakers[4]["id"] == "TB-5"  # deterministic_hash

    # All must have clear direction
    for tb in tie_breakers:
        assert tb["direction"] in ["asc", "desc"]


def test_property_p4_cong_gating_invariants(gyeokguk_policy):
    """P4: CONG gating invariants must be enforced"""
    patterns = gyeokguk_policy["patterns"]
    cong_patterns = [p for p in patterns if p["family"] == "CONG"]

    for pattern in cong_patterns:
        gating = pattern["gating"]
        conditions = gating["conditions"]

        # All CONG patterns must have strength_score condition
        has_strength = any(c["kind"] == "strength_score" for c in conditions)
        assert has_strength, f"CONG pattern {pattern['code']} missing strength_score gating"

        # Check strength thresholds
        for cond in conditions:
            if cond["kind"] == "strength_score":
                # Should have op and value
                assert "op" in cond
                assert "value" in cond

                # Value should be reasonable (0..1 range)
                assert 0.0 <= cond["value"] <= 1.0


def test_property_p5_cong_wang_gating(gyeokguk_policy):
    """P5: CONG_WANG requires strength >= 0.72"""
    patterns = gyeokguk_policy["patterns"]
    cong_wang = next(p for p in patterns if p["code"] == "CONG_WANG")

    # Find strength_score condition
    strength_cond = next(
        c for c in cong_wang["gating"]["conditions"] if c["kind"] == "strength_score"
    )

    assert strength_cond["op"] == ">="
    assert strength_cond["value"] == 0.72


def test_property_p7_family_priority_order(gyeokguk_policy):
    """P7: Family priority must follow CONG > CORE > PEER"""
    families = gyeokguk_policy["priority"]["families"]

    cong_idx = families.index("CONG")
    core_idx = families.index("CORE")
    peer_idx = families.index("PEER")

    # CONG must come before CORE, CORE before PEER
    assert cong_idx < core_idx < peer_idx


def test_property_p9_ko_first_label_coverage(gyeokguk_policy):
    """P9: KO-first label coverage must be complete"""
    patterns = gyeokguk_policy["patterns"]

    for pattern in patterns:
        # Pattern must have label_ko
        assert "label_ko" in pattern
        assert len(pattern["label_ko"]) > 0

        # Core must have notes_ko
        assert "notes_ko" in pattern["core"]

        # All bonuses should have notes_ko
        if "bonuses" in pattern:
            for bonus in pattern["bonuses"]:
                assert "notes_ko" in bonus

        # All penalties should have notes_ko
        if "penalties" in pattern:
            for penalty in pattern["penalties"]:
                assert "notes_ko" in penalty


def test_property_p10_boundary_values(gyeokguk_policy):
    """P10: Boundary value normalization must be exact"""
    scoring = gyeokguk_policy["scoring"]
    norm_params = scoring["normalization"]["params"]

    min_raw = norm_params["min_raw"]
    max_raw = norm_params["max_raw"]

    def normalize(raw):
        return ((raw - min_raw) / (max_raw - min_raw)) * 100.0

    # Test exact boundary values
    assert abs(normalize(min_raw) - 0.0) < 0.01
    assert abs(normalize(0.0) - 50.0) < 0.01
    assert abs(normalize(max_raw) - 100.0) < 0.01


# ============================================================================
# Trace Components
# ============================================================================


def test_trace_components_complete(gyeokguk_policy):
    """Test: Trace components must include all 7 types"""
    trace_templates = gyeokguk_policy["trace_templates"]
    components = trace_templates["components"]

    required_components = ["格局判定", "成格條件", "破格條件", "扶抑", "關係", "조후", "십신"]

    for comp in required_components:
        assert comp in components


# ============================================================================
# Concrete Test Cases (from test_gyeokguk_cases.md)
# Note: These are specification tests, not runtime tests
# They validate the policy structure supports the test cases
# ============================================================================


def test_case_support_zhengguan(gyeokguk_policy):
    """Case 01: Policy supports ZHENGGUAN pattern"""
    patterns = gyeokguk_policy["patterns"]
    zhengguan = next(p for p in patterns if p["code"] == "ZHENGGUAN")

    assert zhengguan["family"] == "CORE"
    assert zhengguan["label_ko"] == "정관격"

    # Should have REL-OFF-SEAL bonus
    bonus_codes = [b["code"] for b in zhengguan["bonuses"]]
    assert "REL-OFF-SEAL" in bonus_codes

    # Should have PEN-MIX-OFF-KILL penalty
    penalty_codes = [p["code"] for p in zhengguan["penalties"]]
    assert "PEN-MIX-OFF-KILL" in penalty_codes


def test_case_support_shangguan_peiyin(gyeokguk_policy):
    """Case 02: Policy supports SHANGGUAN with 상관패인"""
    patterns = gyeokguk_policy["patterns"]
    shangguan = next(p for p in patterns if p["code"] == "SHANGGUAN")

    # Should have REL-SG-PEIYIN bonus
    bonus_codes = [b["code"] for b in shangguan["bonuses"]]
    assert "REL-SG-PEIYIN" in bonus_codes

    # Should have BRK-SG-OFF-DIRECT breaker
    breaker_codes = [b["code"] for b in shangguan["breakers"]]
    assert "BRK-SG-OFF-DIRECT" in breaker_codes


def test_case_support_cong_cai(gyeokguk_policy):
    """Case 08: Policy supports CONG_CAI with gating"""
    patterns = gyeokguk_policy["patterns"]
    cong_cai = next(p for p in patterns if p["code"] == "CONG_CAI")

    assert cong_cai["family"] == "CONG"
    assert "gating" in cong_cai

    # Check gating conditions
    gating_conditions = cong_cai["gating"]["conditions"]

    # Should have strength_score <= 0.28
    strength_cond = next(c for c in gating_conditions if c["kind"] == "strength_score")
    assert strength_cond["op"] == "<="
    assert strength_cond["value"] == 0.28

    # Should require 財 focus
    focus_cond = next(c for c in gating_conditions if c["kind"] == "projection_focus")
    assert focus_cond["focus"] == "財"


def test_case_support_cong_wang(gyeokguk_policy):
    """Case 13: Policy supports CONG_WANG with strength >= 0.72"""
    patterns = gyeokguk_policy["patterns"]
    cong_wang = next(p for p in patterns if p["code"] == "CONG_WANG")

    assert cong_wang["family"] == "CONG"

    # Check gating
    gating_conditions = cong_wang["gating"]["conditions"]
    strength_cond = next(c for c in gating_conditions if c["kind"] == "strength_score")

    assert strength_cond["op"] == ">="
    assert strength_cond["value"] == 0.72


def test_case_support_bijian(gyeokguk_policy):
    """Case 10: Policy supports BIJIAN pattern"""
    patterns = gyeokguk_policy["patterns"]
    bijian = next(p for p in patterns if p["code"] == "BIJIAN")

    assert bijian["family"] == "PEER"
    assert bijian["label_ko"] == "비견격"

    # Should require strong strength_state
    core_conditions = bijian["core"]["conditions"]
    strength_fit = next(c for c in core_conditions if c["kind"] == "strength_fit")
    assert "strong" in strength_fit["allowed"]


# ============================================================================
# Summary Test
# ============================================================================


def test_summary_gyeokguk_complete(gyeokguk_policy):
    """Summary: Verify all major components are present and valid"""
    # Policy metadata
    assert gyeokguk_policy["module"] == "gyeokguk_v1.0"
    assert gyeokguk_policy["policy_version"] == "1.0.0"
    assert gyeokguk_policy["locale_default"] == "ko-KR"

    # Patterns
    assert len(gyeokguk_policy["patterns"]) == 14

    # Dependencies
    assert len(gyeokguk_policy["dependencies"]["modules"]) >= 4

    # Scoring
    assert "normalization" in gyeokguk_policy["scoring"]
    assert "status_thresholds" in gyeokguk_policy["scoring"]

    # Priority
    assert len(gyeokguk_policy["priority"]["families"]) >= 5

    # Tie-breakers
    assert len(gyeokguk_policy["tie_breakers"]) == 5

    # Confidence
    assert len(gyeokguk_policy["confidence"]["metrics"]) == 4

    # Relation codes
    rel_codes = gyeokguk_policy["relation_codes"]
    assert len(rel_codes["supportive"]) >= 6
    assert len(rel_codes["penalty"]) >= 5
    assert len(rel_codes["breaker"]) >= 3

    # CI checks
    assert len(gyeokguk_policy["ci_checks"]) == 5
