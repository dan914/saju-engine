"""
Test luck pillars policy schema validation with focus on labels and reference structure.

Validates that luck_pillars_policy.json conforms to its schema, especially:
- Label keys (ko/en with required fields)
- Reference structure (type: jie/qi, forward/backward)
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError, validate

BASE = Path(__file__).resolve().parents[3]
POL = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "luck_pillars_policy.json"
SCH = BASE / "saju_codex_batch_all_v2_6_signed" / "schemas" / "luck_pillars_policy.schema.json"


@pytest.fixture
def policy() -> dict:
    """Load luck pillars policy."""
    return json.loads(POL.read_text(encoding="utf-8"))


@pytest.fixture
def schema() -> dict:
    """Load luck pillars schema."""
    return json.loads(SCH.read_text(encoding="utf-8"))


def test_policy_file_exists():
    """Policy file must exist."""
    assert POL.exists(), f"Policy not found: {POL}"


def test_schema_file_exists():
    """Schema file must exist."""
    assert SCH.exists(), f"Schema not found: {SCH}"


def test_luck_policy_schema_valid(policy: dict, schema: dict):
    """Policy must validate against schema."""
    validate(policy, schema)


def test_policy_has_required_top_level_fields(policy: dict):
    """Policy must have all required top-level fields."""
    required = [
        "version",
        "generated_on",
        "source_refs",
        "disclaimer",
        "dependencies",
        "direction",
        "start_age",
        "generation",
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


def test_policy_dependencies_structure(policy: dict):
    """Dependencies must have all three required policies."""
    deps = policy["dependencies"]

    assert "sixty_jiazi" in deps
    assert "lifecycle_stages" in deps
    assert "tengods_logic" in deps

    for dep_name in ["sixty_jiazi", "lifecycle_stages", "tengods_logic"]:
        dep = deps[dep_name]
        assert "name" in dep
        assert "version" in dep
        assert "signature" in dep


def test_policy_start_age_reference_structure(policy: dict):
    """Start age reference must have type (jie/qi) and forward/backward."""
    ref = policy["start_age"]["reference"]

    assert "type" in ref
    assert ref["type"] in ["jie", "qi"], f"Invalid type: {ref['type']}"

    assert "forward" in ref
    assert ref["forward"] == "next"

    assert "backward" in ref
    assert ref["backward"] == "prev"


def test_policy_labels_has_required_languages(policy: dict):
    """Labels must have ko and en."""
    labels = policy["labels"]

    assert "ko" in labels, "Missing Korean labels"
    assert "en" in labels, "Missing English labels"


def test_policy_labels_ko_has_required_keys(policy: dict):
    """Korean labels must have all required keys."""
    ko = policy["labels"]["ko"]

    required = ["luck_pillar", "age", "ten_god", "lifecycle"]
    for key in required:
        assert key in ko, f"Missing Korean label key: {key}"
        assert isinstance(ko[key], str), f"Korean label {key} must be string"


def test_policy_labels_en_has_required_keys(policy: dict):
    """English labels must have all required keys."""
    en = policy["labels"]["en"]

    required = ["luck_pillar", "age", "ten_god", "lifecycle"]
    for key in required:
        assert key in en, f"Missing English label key: {key}"
        assert isinstance(en[key], str), f"English label {key} must be string"


def test_policy_direction_matrix_structure(policy: dict):
    """Direction matrix must have male/female with yang/yin."""
    matrix = policy["direction"]["matrix"]

    assert "male" in matrix
    assert "female" in matrix

    for gender in ["male", "female"]:
        assert "yang" in matrix[gender]
        assert "yin" in matrix[gender]
        assert matrix[gender]["yang"] in ["forward", "backward"]
        assert matrix[gender]["yin"] in ["forward", "backward"]


def test_policy_generation_emit_structure(policy: dict):
    """Generation emit must have ten_god_for_stem and lifecycle_for_branch."""
    emit = policy["generation"]["emit"]

    assert "ten_god_for_stem" in emit
    assert "lifecycle_for_branch" in emit
    assert isinstance(emit["ten_god_for_stem"], bool)
    assert isinstance(emit["lifecycle_for_branch"], bool)


def test_invalid_policy_missing_label_key(schema: dict):
    """Schema should reject policy with missing label key."""
    validator = Draft202012Validator(schema)

    pol = json.loads(POL.read_text(encoding="utf-8"))
    del pol["labels"]["ko"]["lifecycle"]  # Remove required key

    with pytest.raises(ValidationError):
        validator.validate(pol)


def test_invalid_policy_wrong_reference_type(schema: dict):
    """Schema should reject invalid reference type."""
    validator = Draft202012Validator(schema)

    pol = json.loads(POL.read_text(encoding="utf-8"))
    pol["start_age"]["reference"]["type"] = "invalid_type"

    with pytest.raises(ValidationError):
        validator.validate(pol)


def test_invalid_policy_missing_dependency(schema: dict):
    """Schema should reject policy with missing dependency."""
    validator = Draft202012Validator(schema)

    pol = json.loads(POL.read_text(encoding="utf-8"))
    del pol["dependencies"]["lifecycle_stages"]

    with pytest.raises(ValidationError):
        validator.validate(pol)
