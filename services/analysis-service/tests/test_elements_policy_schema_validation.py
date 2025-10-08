"""
Test elements distribution policy against JSON schema.

Validates that elements_distribution_criteria.json conforms to its schema.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError, validate

BASE = Path(__file__).resolve().parents[3]
POL = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "elements_distribution_criteria.json"
SCH = (
    BASE
    / "saju_codex_batch_all_v2_6_signed"
    / "schemas"
    / "elements_distribution_criteria.schema.json"
)


@pytest.fixture
def policy() -> dict:
    """Load elements distribution policy."""
    return json.loads(POL.read_text(encoding="utf-8"))


@pytest.fixture
def schema() -> dict:
    """Load elements distribution schema."""
    return json.loads(SCH.read_text(encoding="utf-8"))


def test_policy_file_exists():
    """Policy file must exist."""
    assert POL.exists(), f"Policy not found: {POL}"


def test_schema_file_exists():
    """Schema file must exist."""
    assert SCH.exists(), f"Schema not found: {SCH}"


def test_elements_policy_schema_valid(policy: dict, schema: dict):
    """Policy must validate against schema."""
    validate(policy, schema)


def test_policy_has_required_fields(policy: dict):
    """Policy must have all required top-level fields."""
    required = [
        "version",
        "generated_on",
        "source_refs",
        "disclaimer",
        "dependencies",
        "counting_method",
        "thresholds",
        "labels",
    ]

    for field in required:
        assert field in policy, f"Missing required field: {field}"


def test_policy_version_format(policy: dict):
    """Version must be semantic (e.g., '1.0', '1.1')."""
    version = policy["version"]
    assert isinstance(version, str)
    assert len(version.split(".")) == 2, f"Version must be X.Y format, got: {version}"

    major, minor = version.split(".")
    assert major.isdigit(), f"Major version must be numeric: {major}"
    assert minor.isdigit(), f"Minor version must be numeric: {minor}"


def test_policy_generated_on_iso8601(policy: dict):
    """generated_on must be ISO-8601 date-time."""
    from datetime import datetime

    generated_on = policy["generated_on"]
    assert isinstance(generated_on, str)

    # Parse as ISO-8601
    try:
        datetime.fromisoformat(generated_on.replace("Z", "+00:00"))
    except ValueError as e:
        pytest.fail(f"Invalid ISO-8601 date-time: {generated_on} - {e}")


def test_policy_has_disclaimer(policy: dict):
    """Policy must have disclaimer field."""
    assert "disclaimer" in policy
    assert isinstance(policy["disclaimer"], str)
    assert len(policy["disclaimer"]) > 0


def test_policy_dependencies_structure(policy: dict):
    """Dependencies must have zanggan_policy with name/version/signature."""
    deps = policy["dependencies"]
    assert "zanggan_policy" in deps

    zanggan = deps["zanggan_policy"]
    assert zanggan["name"] == "zanggan_table"
    assert isinstance(zanggan["version"], str)
    assert isinstance(zanggan["signature"], str)
    assert len(zanggan["signature"]) >= 6


def test_policy_counting_method_structure(policy: dict):
    """Counting method must have all required fields."""
    cm = policy["counting_method"]

    assert "mode" in cm
    assert cm["mode"] in ["hidden_only", "branch_plus_hidden"]

    assert "stems" in cm
    assert "weight" in cm["stems"]

    assert "branches" in cm
    assert "weight" in cm["branches"]

    assert "hidden_stems" in cm
    assert "primary" in cm["hidden_stems"]
    assert "secondary" in cm["hidden_stems"]
    assert "tertiary" in cm["hidden_stems"]

    assert "relation_transform" in cm
    assert "apply" in cm["relation_transform"]

    assert "rounding" in cm
    assert "decimals" in cm["rounding"]


def test_policy_thresholds_structure(policy: dict):
    """Thresholds must have all four levels."""
    th = policy["thresholds"]

    required = ["excessive", "developed", "appropriate", "deficient"]
    for field in required:
        assert field in th, f"Missing threshold: {field}"
        assert isinstance(th[field], (int, float))
        assert 0 <= th[field] <= 100


def test_policy_labels_structure(policy: dict):
    """Labels must have zh/ko/en with all four levels."""
    labels = policy["labels"]

    languages = ["zh", "ko", "en"]
    levels = ["excessive", "developed", "appropriate", "deficient"]

    for lang in languages:
        assert lang in labels, f"Missing language: {lang}"
        for level in levels:
            assert level in labels[lang], f"Missing {lang} label for {level}"
            assert isinstance(labels[lang][level], str)


def test_invalid_policy_missing_disclaimer(schema: dict):
    """Schema should reject policy without disclaimer."""
    validator = Draft202012Validator(schema)

    invalid_policy = {
        "version": "1.0",
        "generated_on": "2025-10-04T00:00:00+09:00",
        "source_refs": ["test"],
        "dependencies": {
            "zanggan_policy": {"name": "zanggan_table", "version": "2.6", "signature": "abc123"}
        },
        "counting_method": {
            "mode": "branch_plus_hidden",
            "stems": {"weight": 1.0},
            "branches": {"weight": 1.0},
            "hidden_stems": {
                "primary": {"weight": 1.0},
                "secondary": {"weight": 0.5},
                "tertiary": {"weight": 0.3},
            },
            "relation_transform": {"apply": False},
            "rounding": {"decimals": 2},
        },
        "thresholds": {"excessive": 35.0, "developed": 25.0, "appropriate": 15.0, "deficient": 0.0},
        "labels": {
            "zh": {
                "excessive": "過旺",
                "developed": "發達",
                "appropriate": "平衡",
                "deficient": "不足",
            },
            "ko": {
                "excessive": "과다",
                "developed": "발달",
                "appropriate": "적정",
                "deficient": "부족",
            },
            "en": {
                "excessive": "Excessive",
                "developed": "Developed",
                "appropriate": "Balanced",
                "deficient": "Deficient",
            },
        },
        # Missing: "disclaimer"
    }

    with pytest.raises(ValidationError):
        validator.validate(invalid_policy)


def test_invalid_policy_wrong_mode(schema: dict):
    """Schema should reject invalid counting mode."""
    validator = Draft202012Validator(schema)

    policy = json.loads(POL.read_text(encoding="utf-8"))
    policy["counting_method"]["mode"] = "invalid_mode"

    with pytest.raises(ValidationError):
        validator.validate(policy)


def test_invalid_policy_missing_dependency_field(schema: dict):
    """Schema should reject dependency without required fields."""
    validator = Draft202012Validator(schema)

    policy = json.loads(POL.read_text(encoding="utf-8"))
    del policy["dependencies"]["zanggan_policy"]["signature"]

    with pytest.raises(ValidationError):
        validator.validate(policy)
