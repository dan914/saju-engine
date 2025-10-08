"""
Test elements distribution policy runtime guards.

Validates threshold ordering and dependency signature verification.
"""

import json
from pathlib import Path

import pytest
from app.core.policy_guards import (
    DependencySignature,
    PolicyValidationError,
    validate_dependencies,
    validate_threshold_order,
)

BASE = Path(__file__).resolve().parents[3]
POL = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "elements_distribution_criteria.json"


def load_policy() -> dict:
    """Load elements distribution policy."""
    return json.loads(POL.read_text(encoding="utf-8"))


def test_threshold_order_ok():
    """Valid threshold ordering should pass."""
    pol = load_policy()
    validate_threshold_order(pol)  # Should not raise


def test_threshold_order_violation_excessive_too_low():
    """Excessive threshold below developed should fail."""
    pol = load_policy()
    pol["thresholds"]["excessive"] = 20.0  # Below developed (25.0)

    with pytest.raises(PolicyValidationError, match="Threshold order"):
        validate_threshold_order(pol)


def test_threshold_order_violation_developed_below_appropriate():
    """Developed threshold below appropriate should fail."""
    pol = load_policy()
    pol["thresholds"]["developed"] = 10.0  # Below appropriate (15.0)

    with pytest.raises(PolicyValidationError, match="Threshold order"):
        validate_threshold_order(pol)


def test_threshold_order_violation_out_of_range():
    """Threshold values outside [0,100] should fail."""
    pol = load_policy()
    pol["thresholds"]["excessive"] = 150.0  # Out of range

    with pytest.raises(PolicyValidationError, match="within \\[0,100\\]"):
        validate_threshold_order(pol)


def test_threshold_order_violation_negative():
    """Negative threshold values should fail."""
    pol = load_policy()
    pol["thresholds"]["deficient"] = -5.0  # Negative

    with pytest.raises(PolicyValidationError, match="within \\[0,100\\]"):
        validate_threshold_order(pol)


def test_threshold_order_violation_equal():
    """Equal adjacent thresholds should fail."""
    pol = load_policy()
    pol["thresholds"]["developed"] = 25.0
    pol["thresholds"]["appropriate"] = 25.0  # Equal to developed

    with pytest.raises(PolicyValidationError, match="Threshold order"):
        validate_threshold_order(pol)


def test_threshold_order_violation_missing_key():
    """Missing threshold key should fail."""
    pol = load_policy()
    del pol["thresholds"]["excessive"]

    with pytest.raises(PolicyValidationError, match="Missing thresholds keys"):
        validate_threshold_order(pol)


def test_threshold_order_violation_non_numeric():
    """Non-numeric threshold values should fail."""
    pol = load_policy()
    pol["thresholds"]["excessive"] = "not_a_number"

    with pytest.raises(PolicyValidationError, match="must be numeric"):
        validate_threshold_order(pol)


def test_dependency_signature_match():
    """Matching dependency signature should pass."""
    pol = load_policy()
    declared = pol["dependencies"]["zanggan_policy"]

    actual = {
        declared["name"]: DependencySignature(
            declared["name"], declared["version"], declared["signature"]
        )
    }

    validate_dependencies(pol, actual)  # Should not raise


def test_dependency_signature_mismatch_version():
    """Mismatched version should fail."""
    pol = load_policy()
    declared = pol["dependencies"]["zanggan_policy"]

    actual = {
        declared["name"]: DependencySignature(
            declared["name"], "99.99", declared["signature"]  # Wrong version
        )
    }

    with pytest.raises(PolicyValidationError, match="Dependency mismatch"):
        validate_dependencies(pol, actual)


def test_dependency_signature_mismatch_signature():
    """Mismatched signature should fail."""
    pol = load_policy()
    declared = pol["dependencies"]["zanggan_policy"]

    actual = {
        declared["name"]: DependencySignature(
            declared["name"], declared["version"], "WRONG_SIGNATURE_123"  # Wrong signature
        )
    }

    with pytest.raises(PolicyValidationError, match="Dependency mismatch"):
        validate_dependencies(pol, actual)


def test_dependency_signature_missing_actual():
    """Missing actual dependency should fail."""
    pol = load_policy()

    actual = {}  # Empty, no zanggan_table

    with pytest.raises(PolicyValidationError, match="not provided"):
        validate_dependencies(pol, actual)


def test_dependency_signature_missing_in_policy():
    """Missing dependency declaration in policy should fail."""
    pol = load_policy()
    del pol["dependencies"]["zanggan_policy"]

    actual = {"zanggan_table": DependencySignature("zanggan_table", "2.6", "abc123")}

    with pytest.raises(PolicyValidationError, match="Missing zanggan_policy"):
        validate_dependencies(pol, actual)


def test_actual_zanggan_signature_calculation():
    """Verify actual zanggan signature matches policy declaration."""
    import hashlib

    # Load actual zanggan table
    zanggan_path = BASE / "rulesets" / "zanggan_table.json"
    zanggan_data = json.loads(zanggan_path.read_text(encoding="utf-8"))

    # Calculate signature (same method as policy creation)
    content = json.dumps(zanggan_data["data"], sort_keys=True, ensure_ascii=False)
    calculated_signature = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

    # Load policy
    pol = load_policy()
    declared_signature = pol["dependencies"]["zanggan_policy"]["signature"]

    # They should match
    assert (
        calculated_signature == declared_signature
    ), f"Zanggan signature mismatch: calculated={calculated_signature}, declared={declared_signature}"


def test_threshold_order_edge_case_minimum_spacing():
    """Minimum valid spacing (0.1 apart) should pass."""
    pol = load_policy()
    pol["thresholds"] = {"deficient": 0.0, "appropriate": 0.1, "developed": 0.2, "excessive": 0.3}

    validate_threshold_order(pol)  # Should pass


def test_threshold_order_edge_case_maximum_values():
    """Maximum valid values should pass."""
    pol = load_policy()
    pol["thresholds"] = {
        "deficient": 0.0,
        "appropriate": 33.3,
        "developed": 66.6,
        "excessive": 99.9,
    }

    validate_threshold_order(pol)  # Should pass
