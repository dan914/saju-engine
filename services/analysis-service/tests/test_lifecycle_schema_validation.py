"""
Test lifecycle stages policy against JSON schema.

Validates that lifecycle_stages.json conforms to lifecycle_stages.schema.json.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


@pytest.fixture
def schema_path() -> Path:
    """Path to lifecycle stages schema."""
    return (
        Path(__file__).parents[3]
        / "saju_codex_batch_all_v2_6_signed/schemas/lifecycle_stages.schema.json"
    )


@pytest.fixture
def policy_path() -> Path:
    """Path to lifecycle stages policy."""
    return (
        Path(__file__).parents[3]
        / "saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json"
    )


@pytest.fixture
def lifecycle_schema(schema_path: Path) -> dict:
    """Load lifecycle stages schema."""
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def lifecycle_policy(policy_path: Path) -> dict:
    """Load lifecycle stages policy."""
    with policy_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_file_exists(schema_path: Path):
    """Schema file must exist."""
    assert schema_path.exists(), f"Schema not found: {schema_path}"


def test_policy_file_exists(policy_path: Path):
    """Policy file must exist."""
    assert policy_path.exists(), f"Policy not found: {policy_path}"


def test_schema_is_valid_json(lifecycle_schema: dict):
    """Schema must be valid JSON."""
    assert isinstance(lifecycle_schema, dict)
    assert "$schema" in lifecycle_schema
    assert lifecycle_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_policy_is_valid_json(lifecycle_policy: dict):
    """Policy must be valid JSON."""
    assert isinstance(lifecycle_policy, dict)


def test_policy_validates_against_schema(lifecycle_schema: dict, lifecycle_policy: dict):
    """Policy must pass schema validation."""
    validator = Draft202012Validator(lifecycle_schema)

    # Raises ValidationError if invalid
    validator.validate(lifecycle_policy)


def test_policy_has_required_fields(lifecycle_policy: dict):
    """Policy must have all required top-level fields."""
    required = ["version", "generated_on", "source_refs", "mappings", "labels"]

    for field in required:
        assert field in lifecycle_policy, f"Missing required field: {field}"


def test_policy_version_format(lifecycle_policy: dict):
    """Version must be semantic (e.g., '1.0', '1.1')."""
    version = lifecycle_policy["version"]
    assert isinstance(version, str)
    assert len(version.split(".")) == 2, f"Version must be X.Y format, got: {version}"

    major, minor = version.split(".")
    assert major.isdigit(), f"Major version must be numeric: {major}"
    assert minor.isdigit(), f"Minor version must be numeric: {minor}"


def test_policy_generated_on_iso8601(lifecycle_policy: dict):
    """generated_on must be ISO-8601 date-time."""
    from datetime import datetime

    generated_on = lifecycle_policy["generated_on"]
    assert isinstance(generated_on, str)

    # Parse as ISO-8601
    try:
        datetime.fromisoformat(generated_on.replace("Z", "+00:00"))
    except ValueError as e:
        pytest.fail(f"Invalid ISO-8601 date-time: {generated_on} - {e}")


def test_policy_source_refs_not_empty(lifecycle_policy: dict):
    """source_refs must have at least one reference."""
    source_refs = lifecycle_policy["source_refs"]
    assert isinstance(source_refs, list)
    assert len(source_refs) >= 1, "Must cite at least one classical source"


def test_policy_has_all_10_stems(lifecycle_policy: dict):
    """Mappings must include all 10 heavenly stems."""
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    mappings = lifecycle_policy["mappings"]

    for stem in stems:
        assert stem in mappings, f"Missing stem: {stem}"


def test_policy_has_all_12_branches_per_stem(lifecycle_policy: dict):
    """Each stem must have all 12 branches."""
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        for branch in branches:
            assert branch in branch_map, f"Stem {stem} missing branch: {branch}"


def test_policy_stage_values_valid(lifecycle_policy: dict):
    """All stage values must be valid lifecycle stages."""
    valid_stages = [
        "長生",
        "沐浴",
        "冠帶",
        "臨官",
        "帝旺",
        "衰",
        "病",
        "死",
        "墓",
        "絕",
        "胎",
        "養",
    ]
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        for branch, stage in branch_map.items():
            assert stage in valid_stages, f"Invalid stage for {stem}-{branch}: {stage}"


def test_policy_each_stem_uses_all_stages(lifecycle_policy: dict):
    """Each stem must use all 12 stages exactly once."""
    all_stages = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"]
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        stages_used = list(branch_map.values())
        assert len(stages_used) == 12, f"Stem {stem} has {len(stages_used)} stages, expected 12"

        # Check uniqueness
        assert len(set(stages_used)) == 12, f"Stem {stem} has duplicate stages"

        # Check completeness
        for stage in all_stages:
            assert stage in stages_used, f"Stem {stem} missing stage: {stage}"


def test_policy_labels_have_all_languages(lifecycle_policy: dict):
    """Labels must include zh, ko, en."""
    labels = lifecycle_policy["labels"]

    assert "zh" in labels, "Missing Chinese labels"
    assert "ko" in labels, "Missing Korean labels"
    assert "en" in labels, "Missing English labels"


def test_policy_labels_have_12_items(lifecycle_policy: dict):
    """Each language must have exactly 12 stage labels."""
    labels = lifecycle_policy["labels"]

    for lang in ["zh", "ko", "en"]:
        lang_labels = labels[lang]
        assert len(lang_labels) == 12, f"{lang} has {len(lang_labels)} labels, expected 12"


def test_policy_zh_labels_match_mappings(lifecycle_policy: dict):
    """Chinese labels must match stages used in mappings."""
    zh_labels = set(lifecycle_policy["labels"]["zh"])
    mappings = lifecycle_policy["mappings"]

    # Collect all unique stages from mappings
    stages_in_mappings = set()
    for branch_map in mappings.values():
        stages_in_mappings.update(branch_map.values())

    assert zh_labels == stages_in_mappings, "Chinese labels don't match mapping stages"


def test_invalid_policy_rejected():
    """Schema should reject invalid policy."""
    from jsonschema import Draft202012Validator

    schema_path = (
        Path(__file__).parents[3]
        / "saju_codex_batch_all_v2_6_signed/schemas/lifecycle_stages.schema.json"
    )

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)

    # Test 1: Missing required field
    invalid_policy_1 = {
        "version": "1.0",
        "generated_on": "2025-10-05T00:00:00+09:00",
        # Missing: source_refs, mappings, labels
    }

    with pytest.raises(ValidationError):
        validator.validate(invalid_policy_1)

    # Test 2: Invalid version format
    invalid_policy_2 = {
        "version": "1",  # Should be "1.0"
        "generated_on": "2025-10-05T00:00:00+09:00",
        "source_refs": ["test"],
        "mappings": {},
        "labels": {"zh": [], "ko": [], "en": []},
    }

    with pytest.raises(ValidationError):
        validator.validate(invalid_policy_2)

    # Test 3: Missing English labels (should fail in v1.1)
    invalid_policy_3 = {
        "version": "1.0",
        "generated_on": "2025-10-05T00:00:00+09:00",
        "source_refs": ["test"],
        "mappings": {
            "甲": {
                "子": "沐浴",
                "丑": "冠帶",
                "寅": "臨官",
                "卯": "帝旺",
                "辰": "衰",
                "巳": "病",
                "午": "死",
                "未": "墓",
                "申": "絕",
                "酉": "胎",
                "戌": "養",
                "亥": "長生",
            }
        },
        "labels": {
            "zh": [
                "長生",
                "沐浴",
                "冠帶",
                "臨官",
                "帝旺",
                "衰",
                "病",
                "死",
                "墓",
                "絕",
                "胎",
                "養",
            ],
            "ko": [
                "장생",
                "목욕",
                "관대",
                "임관",
                "제왕",
                "쇠",
                "병",
                "사",
                "묘",
                "절",
                "태",
                "양",
            ],
            # Missing: "en"
        },
    }

    with pytest.raises(ValidationError):
        validator.validate(invalid_policy_3)
