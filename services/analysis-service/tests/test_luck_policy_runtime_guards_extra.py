"""
Test luck pillars policy runtime guards.

Validates runtime checks beyond schema validation:
- Start age reference type validation (jie/qi)
- Labels key presence validation
- Direction matrix validation
- Age series bounds validation
"""

import json
from pathlib import Path

import pytest
from app.core.policy_guards_luck import (
    LuckPolicyError,
    validate_age_series,
    validate_direction_matrix,
    validate_labels,
    validate_start_age_reference,
)

BASE = Path(__file__).resolve().parents[3]
POL = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "luck_pillars_policy.json"


def load_policy() -> dict:
    """Load luck pillars policy."""
    return json.loads(POL.read_text(encoding="utf-8"))


def test_reference_and_labels_guards():
    """Valid policy should pass all guards."""
    pol = load_policy()
    validate_start_age_reference(pol["start_age"]["reference"])
    validate_labels(pol["labels"])


def test_reference_type_jie_valid():
    """Reference type 'jie' should be valid."""
    ref = {"type": "jie", "forward": "next", "backward": "prev"}
    validate_start_age_reference(ref)  # Should not raise


def test_reference_type_qi_valid():
    """Reference type 'qi' should be valid."""
    ref = {"type": "qi", "forward": "next", "backward": "prev"}
    validate_start_age_reference(ref)  # Should not raise


def test_reference_type_invalid():
    """Invalid reference type should fail."""
    pol = load_policy()
    pol["start_age"]["reference"]["type"] = "foo"

    with pytest.raises(LuckPolicyError, match="must be 'jie' or 'qi'"):
        validate_start_age_reference(pol["start_age"]["reference"])


def test_reference_forward_invalid():
    """Invalid forward value should fail."""
    ref = {"type": "jie", "forward": "previous", "backward": "prev"}

    with pytest.raises(LuckPolicyError, match="must be 'next'/'prev'"):
        validate_start_age_reference(ref)


def test_reference_backward_invalid():
    """Invalid backward value should fail."""
    ref = {"type": "jie", "forward": "next", "backward": "previous"}

    with pytest.raises(LuckPolicyError, match="must be 'next'/'prev'"):
        validate_start_age_reference(ref)


def test_labels_valid():
    """Valid labels should pass."""
    labels = {
        "ko": {"luck_pillar": "대운", "age": "시작나이", "ten_god": "십신", "lifecycle": "12운성"},
        "en": {
            "luck_pillar": "Decade Luck",
            "age": "StartAge",
            "ten_god": "TenGod",
            "lifecycle": "Lifecycle",
        },
    }
    validate_labels(labels)  # Should not raise


def test_labels_missing_ko():
    """Missing Korean labels should fail."""
    labels = {
        "en": {
            "luck_pillar": "Decade Luck",
            "age": "StartAge",
            "ten_god": "TenGod",
            "lifecycle": "Lifecycle",
        }
    }

    with pytest.raises(LuckPolicyError, match="missing keys for ko"):
        validate_labels(labels)


def test_labels_missing_en():
    """Missing English labels should fail."""
    labels = {
        "ko": {"luck_pillar": "대운", "age": "시작나이", "ten_god": "십신", "lifecycle": "12운성"}
    }

    with pytest.raises(LuckPolicyError, match="missing keys for en"):
        validate_labels(labels)


def test_labels_missing_ko_key():
    """Missing Korean label key should fail."""
    labels = {
        "ko": {
            "luck_pillar": "대운",
            "age": "시작나이",
            "ten_god": "십신",
            # Missing: lifecycle
        },
        "en": {
            "luck_pillar": "Decade Luck",
            "age": "StartAge",
            "ten_god": "TenGod",
            "lifecycle": "Lifecycle",
        },
    }

    with pytest.raises(LuckPolicyError, match="missing keys for ko"):
        validate_labels(labels)


def test_labels_missing_en_key():
    """Missing English label key should fail."""
    labels = {
        "ko": {"luck_pillar": "대운", "age": "시작나이", "ten_god": "십신", "lifecycle": "12운성"},
        "en": {
            "luck_pillar": "Decade Luck",
            "age": "StartAge",
            "ten_god": "TenGod",
            # Missing: lifecycle
        },
    }

    with pytest.raises(LuckPolicyError, match="missing keys for en"):
        validate_labels(labels)


def test_direction_matrix_valid():
    """Valid direction matrix should pass."""
    pol = load_policy()
    validate_direction_matrix(pol["direction"]["matrix"])


def test_direction_matrix_missing_gender():
    """Missing gender in matrix should fail."""
    matrix = {
        "male": {"yang": "forward", "yin": "backward"}
        # Missing: female
    }

    with pytest.raises(LuckPolicyError, match="missing entries for female"):
        validate_direction_matrix(matrix)


def test_direction_matrix_missing_polarity():
    """Missing polarity in matrix should fail."""
    matrix = {
        "male": {"yang": "forward"},  # Missing: yin
        "female": {"yang": "backward", "yin": "forward"},
    }

    with pytest.raises(LuckPolicyError, match="missing entries for male"):
        validate_direction_matrix(matrix)


def test_direction_matrix_invalid_value():
    """Invalid direction value should fail."""
    matrix = {
        "male": {"yang": "forwards", "yin": "backward"},  # Invalid: forwards
        "female": {"yang": "backward", "yin": "forward"},
    }

    with pytest.raises(LuckPolicyError, match="must be 'forward' or 'backward'"):
        validate_direction_matrix(matrix)


def test_age_series_valid():
    """Valid age series should pass."""
    pol = load_policy()
    validate_age_series(pol["generation"]["age_series"])


def test_age_series_step_out_of_bounds_low():
    """Step years below 1 should fail."""
    series = {"step_years": 0, "count": 10}

    with pytest.raises(LuckPolicyError, match="out of bounds"):
        validate_age_series(series)


def test_age_series_step_out_of_bounds_high():
    """Step years above 20 should fail."""
    series = {"step_years": 21, "count": 10}

    with pytest.raises(LuckPolicyError, match="out of bounds"):
        validate_age_series(series)


def test_age_series_count_out_of_bounds_low():
    """Count below 1 should fail."""
    series = {"step_years": 10, "count": 0}

    with pytest.raises(LuckPolicyError, match="out of bounds"):
        validate_age_series(series)


def test_age_series_count_out_of_bounds_high():
    """Count above 12 should fail."""
    series = {"step_years": 10, "count": 13}

    with pytest.raises(LuckPolicyError, match="out of bounds"):
        validate_age_series(series)


def test_all_guards_pass_on_valid_policy():
    """All guards should pass on valid policy."""
    pol = load_policy()

    # Should not raise
    validate_start_age_reference(pol["start_age"]["reference"])
    validate_labels(pol["labels"])
    validate_direction_matrix(pol["direction"]["matrix"])
    validate_age_series(pol["generation"]["age_series"])
