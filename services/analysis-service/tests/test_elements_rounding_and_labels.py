"""
Test elements distribution rounding and labeling rules.

Validates that labels are assigned BEFORE rounding, preventing edge case errors.
"""

from .policy_guards import normalize_and_label


def test_labeling_before_rounding_developed_boundary():
    """24.995% should be 'appropriate' even though it rounds to 25.00%."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    # 24.995 rounds to 25.00, but is below 25.0 threshold
    pcts = {"木": 24.995}
    labels = normalize_and_label(pcts, thresholds)

    assert (
        labels["木"] == "appropriate"
    ), "24.995 should be 'appropriate' (below 25.0 threshold), not 'developed'"


def test_labeling_before_rounding_excessive_boundary():
    """34.999% should be 'developed' even though it rounds to 35.00%."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    # 34.999 rounds to 35.00, but is below 35.0 threshold
    pcts = {"火": 34.999}
    labels = normalize_and_label(pcts, thresholds)

    assert (
        labels["火"] == "developed"
    ), "34.999 should be 'developed' (below 35.0 threshold), not 'excessive'"


def test_labeling_before_rounding_appropriate_boundary():
    """14.999% should be 'deficient' even though it rounds to 15.00%."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    # 14.999 rounds to 15.00, but is below 15.0 threshold
    pcts = {"土": 14.999}
    labels = normalize_and_label(pcts, thresholds)

    assert (
        labels["土"] == "deficient"
    ), "14.999 should be 'deficient' (below 15.0 threshold), not 'appropriate'"


def test_labeling_exact_threshold_values():
    """Exact threshold values should be labeled correctly."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {
        "木": 15.0,  # Exactly 15.0
        "火": 25.0,  # Exactly 25.0
        "土": 35.0,  # Exactly 35.0
        "金": 14.999,  # Just below 15.0
        "水": 0.0,  # Exactly 0.0
    }

    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "appropriate", "15.0 should be 'appropriate' (>= 15.0)"
    assert labels["火"] == "developed", "25.0 should be 'developed' (>= 25.0)"
    assert labels["土"] == "excessive", "35.0 should be 'excessive' (>= 35.0)"
    assert labels["金"] == "deficient", "14.999 should be 'deficient' (< 15.0)"
    assert labels["水"] == "deficient", "0.0 should be 'deficient' (< 15.0)"


def test_labeling_all_five_elements():
    """Test labeling with all five elements."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {
        "木": 24.995,  # appropriate (24.995 < 25.0)
        "火": 35.0,  # excessive (35.0 >= 35.0)
        "土": 0.0,  # deficient (0.0 < 15.0)
        "金": 15.0,  # appropriate (15.0 >= 15.0)
        "水": 26.0,  # developed (26.0 >= 25.0)
    }

    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "appropriate"
    assert labels["火"] == "excessive"
    assert labels["土"] == "deficient"
    assert labels["金"] == "appropriate"
    assert labels["水"] == "developed"


def test_labeling_edge_case_very_small_values():
    """Very small percentages should be labeled deficient."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {"木": 0.001, "火": 0.1, "土": 1.0, "金": 10.0, "水": 14.9}

    labels = normalize_and_label(pcts, thresholds)

    for element in pcts.keys():
        assert (
            labels[element] == "deficient"
        ), f"{element} ({pcts[element]}%) should be 'deficient' (< 15.0)"


def test_labeling_edge_case_very_large_values():
    """Very large percentages should be labeled excessive."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {"木": 50.0, "火": 75.0, "土": 99.99, "金": 100.0, "水": 35.001}

    labels = normalize_and_label(pcts, thresholds)

    for element in pcts.keys():
        assert (
            labels[element] == "excessive"
        ), f"{element} ({pcts[element]}%) should be 'excessive' (>= 35.0)"


def test_labeling_realistic_distribution():
    """Test with realistic element distribution."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    # Realistic case: sum = 100.0
    pcts = {
        "木": 18.33,  # appropriate
        "火": 12.50,  # deficient
        "土": 30.00,  # developed
        "金": 25.00,  # developed
        "水": 14.17,  # deficient
    }

    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "appropriate"
    assert labels["火"] == "deficient"
    assert labels["土"] == "developed"
    assert labels["金"] == "developed"
    assert labels["水"] == "deficient"


def test_labeling_boundary_precision():
    """Test labeling precision at boundaries with float comparison."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    # Test cases right at boundaries
    test_cases = [
        (14.9999999, "deficient"),
        (15.0000000, "appropriate"),
        (15.0000001, "appropriate"),
        (24.9999999, "appropriate"),
        (25.0000000, "developed"),
        (25.0000001, "developed"),
        (34.9999999, "developed"),
        (35.0000000, "excessive"),
        (35.0000001, "excessive"),
    ]

    for pct, expected_label in test_cases:
        pcts = {"木": pct}
        labels = normalize_and_label(pcts, thresholds)
        assert (
            labels["木"] == expected_label
        ), f"{pct}% should be '{expected_label}', got '{labels['木']}'"


def test_labeling_with_custom_thresholds():
    """Test labeling with non-standard thresholds."""
    thresholds = {"deficient": 5.0, "appropriate": 20.0, "developed": 40.0, "excessive": 60.0}

    pcts = {
        "木": 4.99,  # deficient (< 5.0)
        "火": 5.0,  # deficient (5.0 < 20.0)
        "土": 19.99,  # deficient (< 20.0)
        "金": 20.0,  # appropriate (>= 20.0)
        "水": 60.0,  # excessive (>= 60.0)
    }

    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "deficient"
    assert labels["火"] == "deficient"
    assert labels["土"] == "deficient"
    assert labels["金"] == "appropriate"
    assert labels["水"] == "excessive"


def test_labeling_zero_percentage():
    """Zero percentage should be labeled deficient."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {"木": 0.0}
    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "deficient"


def test_labeling_handles_negative_zero():
    """Negative zero should be treated as deficient."""
    thresholds = {"deficient": 0.0, "appropriate": 15.0, "developed": 25.0, "excessive": 35.0}

    pcts = {"木": -0.0}  # Negative zero (equals 0.0 in Python)
    labels = normalize_and_label(pcts, thresholds)

    assert labels["木"] == "deficient"
