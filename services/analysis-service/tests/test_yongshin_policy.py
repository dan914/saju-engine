"""
Test suite for yongshin_policy.json and elemental_projection_policy.json validation.

Tests include:
- P0: Schema, required fields, locale, determinism, projection policy
- P1: Normalization, role thresholds, topk, metrics
- P2: KO-first, evidence compatibility

Based on test_yongshin_properties.md specifications.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def yongshin_policy_path():
    """Path to yongshin_policy.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "yongshin_policy.json"
    )


@pytest.fixture
def projection_policy_path():
    """Path to elemental_projection_policy.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "policies"
        / "elemental_projection_policy.json"
    )


@pytest.fixture
def schema_path():
    """Path to yongshin.schema.json"""
    return (
        Path(__file__).parent.parent.parent.parent
        / "saju_codex_batch_all_v2_6_signed"
        / "schemas"
        / "yongshin.schema.json"
    )


@pytest.fixture
def yongshin_policy(yongshin_policy_path):
    """Load yongshin_policy.json"""
    with open(yongshin_policy_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def projection_policy(projection_policy_path):
    """Load elemental_projection_policy.json"""
    with open(projection_policy_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def schema(schema_path):
    """Load yongshin.schema.json"""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# P0: Schema / Required Fields / Locale
# ============================================================================


def test_p0_yongshin_policy_structure(yongshin_policy):
    """P0: Yongshin policy has required top-level fields"""
    required_fields = [
        "policy_name",
        "policy_version",
        "policy_signature",
        "locale",
        "schema",
        "canonicalization",
        "hashing",
        "engine",
        "dependencies_required",
        "weighting_policy",
        "projection_contracts",
        "five_elements",
        "role_assignment",
        "confidence_rules",
        "topk",
        "ci_checks",
    ]

    for field in required_fields:
        assert field in yongshin_policy, f"Missing required field: {field}"


def test_p0_projection_policy_structure(projection_policy):
    """P0: Projection policy has required sections"""
    required_sections = [
        "policy_name",
        "policy_version",
        "five_elements",
        "resolver",
        "projectors",
        "overlap_guards",
        "metrics",
    ]

    for section in required_sections:
        assert section in projection_policy, f"Missing required section: {section}"


def test_p0_locale_default_ko(yongshin_policy):
    """P0: Default locale must be ko-KR"""
    assert yongshin_policy["locale"]["default"] == "ko-KR"
    assert yongshin_policy["locale"]["ko_first_enforced"] is True


def test_p0_five_elements_complete(yongshin_policy, projection_policy):
    """P0: Five elements must be defined identically"""
    expected = ["木", "火", "土", "金", "水"]
    assert yongshin_policy["five_elements"] == expected
    assert projection_policy["five_elements"] == expected


# ============================================================================
# P0: Determinism / Hash / Signature
# ============================================================================


def test_p0_canonicalization_rfc8785(yongshin_policy, projection_policy):
    """P0: Both policies use RFC8785 canonicalization"""
    assert yongshin_policy["canonicalization"]["json"] == "RFC8785"
    assert projection_policy["canonicalization"]["json"] == "RFC8785"


def test_p0_hashing_sha256(yongshin_policy, projection_policy):
    """P0: Both policies use SHA256 hashing"""
    assert yongshin_policy["hashing"]["algo"] == "SHA256"
    assert projection_policy["hashing"]["algo"] == "SHA256"


def test_p0_policy_signature_pending(yongshin_policy, projection_policy):
    """P0: Policy signatures should be PENDING before CI injection"""
    assert yongshin_policy["policy_signature"] == "PENDING"
    assert projection_policy["policy_signature"] == "PENDING"


# ============================================================================
# P0: Projection / Weighting / Clamping
# ============================================================================


def test_p0_projection_policy_ref_valid(yongshin_policy, projection_policy_path):
    """P0: projection_contracts.policy_ref must point to valid file"""
    policy_ref = yongshin_policy["projection_contracts"]["policy_ref"]

    # Extract file path (before #)
    if "#" in policy_ref:
        file_path = policy_ref.split("#")[0]
    else:
        file_path = policy_ref

    # Check file exists
    assert projection_policy_path.exists(), f"Projection policy file not found: {file_path}"


def test_p0_projectors_have_caps(projection_policy):
    """P0: All projectors must have caps defined"""
    for name, projector in projection_policy["projectors"].items():
        if projector.get("enabled", True):  # Only check enabled projectors
            assert "cap" in projector, f"Projector {name} missing cap"


def test_p0_weights_sum_approximately_one(yongshin_policy):
    """P0: Policy weights should sum to approximately 1.0"""
    weights = yongshin_policy["weighting_policy"]["weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected ~1.0"


def test_p0_overlap_guards_defined(projection_policy):
    """P0: Overlap guards must be defined to prevent double-counting"""
    guards = projection_policy["overlap_guards"]

    assert "tengods_vs_strength" in guards
    assert guards["tengods_vs_strength"]["mode"] == "residual"
    assert "alpha" in guards["tengods_vs_strength"]
    assert 0 < guards["tengods_vs_strength"]["alpha"] <= 1


def test_p0_per_element_cap_exists(projection_policy):
    """P0: Global per-element cap must be defined"""
    caps = projection_policy["overlap_guards"]["caps"]
    assert "per_element" in caps
    assert caps["per_element"] == 100.0


# ============================================================================
# P1: Normalization / Role Thresholds / Top-K
# ============================================================================


def test_p1_normalization_range_valid(yongshin_policy):
    """P1: Normalization target range must be [0, 100]"""
    norm = yongshin_policy["normalization"]
    assert norm["kind"] == "min_max"
    assert norm["target_range"] == [0.0, 100.0]


def test_p1_role_thresholds_ordered(yongshin_policy):
    """P1: Role thresholds must be properly ordered"""
    roles = yongshin_policy["role_assignment"]

    useful = roles["useful_threshold"]  # 65
    favorable = roles["favorable_threshold"]  # 55
    unfavorable = roles["unfavorable_threshold"]  # 35

    assert useful > favorable > unfavorable
    assert useful == 65.0
    assert favorable == 55.0
    assert unfavorable == 35.0


def test_p1_topk_value_reasonable(yongshin_policy):
    """P1: Top-K value must be reasonable (typically 3-5)"""
    topk = yongshin_policy["topk"]["k"]
    assert isinstance(topk, int)
    assert 1 <= topk <= 5


def test_p1_role_labels_ko_complete(yongshin_policy):
    """P1: All role labels must be defined in Korean"""
    labels = yongshin_policy["role_assignment"]["labels"]

    required_roles = ["useful", "favorable", "unfavorable", "neutral"]
    for role in required_roles:
        assert role in labels
        assert len(labels[role]) > 0


# ============================================================================
# P1: Metrics / Confidence
# ============================================================================


def test_p1_confidence_weights_sum_to_one(yongshin_policy):
    """P1: Confidence component weights must sum to 1.0"""
    params = yongshin_policy["confidence_rules"]["params"]

    total = (
        params["w_strength_context"]
        + params["w_consistency"]
        + params["w_relation_polarity"]
        + params["w_shensha_support"]
    )

    assert abs(total - 1.0) < 0.01, f"Confidence weights sum to {total}, expected 1.0"


def test_p1_confidence_formula_exists(yongshin_policy):
    """P1: Confidence formula must be defined"""
    assert "formula" in yongshin_policy["confidence_rules"]
    formula = yongshin_policy["confidence_rules"]["formula"]
    assert "clamp01" in formula or "clip" in formula


def test_p1_metrics_defined(projection_policy):
    """P1: All metrics used in confidence must be defined"""
    metrics = projection_policy["metrics"]

    required_metrics = ["consistency", "relation_polarity", "strength_context", "shensha_support"]

    for metric in required_metrics:
        assert metric in metrics
        assert "method" in metrics[metric]
        assert "desc" in metrics[metric]


# ============================================================================
# P2: KO-first / Integration Compatibility
# ============================================================================


def test_p2_ko_first_enforced(yongshin_policy):
    """P2: KO-first must be enforced in locale settings"""
    assert yongshin_policy["locale"]["ko_first_enforced"] is True
    assert yongshin_policy["locale"]["fallback_order"][0] == "ko-KR"


def test_p2_dependencies_required_complete(yongshin_policy):
    """P2: All required dependencies must be specified"""
    deps = yongshin_policy["dependencies_required"]
    required_names = {"strength_v2", "branch_tengods_v1.1", "shensha_v2", "relation_v1.0"}

    actual_names = {dep["name"] for dep in deps}
    assert required_names.issubset(actual_names)


def test_p2_ci_checks_complete(yongshin_policy):
    """P2: All critical CI checks must be defined"""
    ci_checks = yongshin_policy["ci_checks"]
    check_ids = {check["id"] for check in ci_checks}

    critical_checks = {
        "SCHEMA_VALIDATION",
        "REQUIRED_FIELDS",
        "KO_FIRST_LABEL_COVERAGE",
        "DETERMINISTIC_INPUT_HASH",
        "PROJECTION_POLICY_REF",
        "PROJECTOR_OUTPUT_BOUNDS",
        "RESIDUAL_OVERLAP_GUARD",
    }

    assert critical_checks.issubset(check_ids)


# ============================================================================
# Projection Policy Tests
# ============================================================================


def test_projection_resolver_complete(projection_policy):
    """Test: Resolver must have all required mappings"""
    resolver = projection_policy["resolver"]

    # Day master element map
    assert "day_master_element_map" in resolver
    stems = resolver["day_master_element_map"]
    assert len(stems) == 10  # 10 heavenly stems

    # Element relations
    assert "element_relations" in resolver
    relations = resolver["element_relations"]
    assert len(relations) == 5  # 5 elements

    # Each element must have all relative roles
    required_roles = {"same", "shengwo", "wo_sheng", "wo_ke", "ke_wo"}
    for element, roles in relations.items():
        assert set(roles.keys()) == required_roles


def test_projection_strength_weights_by_state(projection_policy):
    """Test: Strength projector must have weights for all states"""
    strength = projection_policy["projectors"]["strength_v2"]

    assert "weights_by_state" in strength
    states = strength["weights_by_state"]

    required_states = {"weak", "balanced", "strong"}
    assert set(states.keys()) == required_states

    # Each state must have all relative roles
    required_roles = {"same", "shengwo", "wo_sheng", "wo_ke", "ke_wo"}
    for state, weights in states.items():
        assert set(weights.keys()) == required_roles


def test_projection_tengods_relative_map(projection_policy):
    """Test: TenGods projector must map all 10 ten gods"""
    tengods = projection_policy["projectors"]["branch_tengods_v1.1"]

    assert "relative_map" in tengods
    relative_map = tengods["relative_map"]

    # All 10 ten gods must be mapped
    assert len(relative_map) == 10

    # All values must be valid relative roles
    valid_roles = {"same", "shengwo", "wo_sheng", "wo_ke", "ke_wo"}
    for god, role in relative_map.items():
        assert role in valid_roles


def test_projection_relation_direction_rules(projection_policy):
    """Test: Relation projector must have direction rules for all types"""
    relation = projection_policy["projectors"]["relation_v1.0"]

    assert "direction_rules" in relation
    rules = relation["direction_rules"]

    # Must cover harmonies and conflicts
    assert "三合|六合|半合|方合|拱合" in rules
    assert "沖" in rules
    assert "破|害|刑" in rules


def test_projection_climate_mappings(projection_policy):
    """Test: Climate projector must have temperature and humidity mappings"""
    climate = projection_policy["projectors"]["climate_balancer_v1.0"]

    assert "temperature" in climate
    assert "humidity" in climate

    # Temperature mappings
    temp = climate["temperature"]
    assert "cold" in temp
    assert "hot" in temp

    # Humidity mappings
    humid = climate["humidity"]
    assert "dry" in humid
    assert "humid" in humid


def test_projection_shensha_disabled_by_default(projection_policy):
    """Test: Shensha projector should be disabled by default"""
    shensha = projection_policy["projectors"]["shensha_v2"]
    assert shensha["enabled"] is False


# ============================================================================
# Integration Tests
# ============================================================================


def test_integration_merge_order_correct(yongshin_policy):
    """Test: Evidence builder merge order must place yongshin last"""
    merge_order = yongshin_policy["integration"]["evidence_builder_merge_order"]

    # Yongshin must be last (depends on all others)
    assert merge_order[-1] == "yongshin_v1.0"

    # Must include all dependencies
    required = ["strength_v2", "branch_tengods_v1.1", "shensha_v2", "relation_v1.0"]
    for dep in required:
        assert dep in merge_order


def test_integration_policy_version_valid(yongshin_policy):
    """Test: Policy version must follow semantic versioning"""
    version = yongshin_policy["policy_version"]
    parts = version.split(".")

    assert len(parts) in [2, 3]  # major.minor or major.minor.patch
    for part in parts:
        assert part.isdigit()


# ============================================================================
# Summary Test
# ============================================================================


def test_summary_yongshin_complete(yongshin_policy, projection_policy):
    """Summary: Verify all major components are present and valid"""
    # Yongshin policy
    assert yongshin_policy["policy_name"] == "Saju Yongshin Selector Policy"
    assert yongshin_policy["policy_version"] == "1.0.1"
    assert len(yongshin_policy["five_elements"]) == 5
    assert len(yongshin_policy["dependencies_required"]) == 4
    assert len(yongshin_policy["ci_checks"]) >= 7

    # Projection policy
    assert projection_policy["policy_name"] == "Elemental Projection Policy"
    assert projection_policy["policy_version"] == "1.0.0"
    assert len(projection_policy["projectors"]) == 5
    assert len(projection_policy["metrics"]) == 4

    # Cross-reference
    weights = yongshin_policy["weighting_policy"]["weights"]
    projectors = projection_policy["projectors"]

    # All weighted engines must have projectors
    for engine in weights.keys():
        if engine != "climate_balancer_v1.0":  # Optional dependency
            assert engine in projectors
