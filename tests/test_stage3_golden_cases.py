# -*- coding: utf-8 -*-
"""
Stage-3 Golden Cases Parametric Test

Tests 4 MVP runtime engines (Climate Advice, Luck Flow, Gyeokguk, Pattern Profiler)
against 20 golden test cases covering various scenarios.

Usage:
    export POLICY_DIR=$(pwd)/policy
    pytest tests/test_stage3_golden_cases.py -v
"""
import json
from pathlib import Path

import pytest

from tests._analysis_loader import get_core_attr


ClimateAdvice = get_core_attr("climate_advice", "ClimateAdvice")
LuckFlow = get_core_attr("luck_flow", "LuckFlow")
GyeokgukClassifier = get_core_attr("gyeokguk_classifier", "GyeokgukClassifier")
PatternProfiler = get_core_attr("pattern_profiler", "PatternProfiler")

# Load all golden cases
GOLDEN_CASES_DIR = Path(__file__).parent / "golden_cases"
GOLDEN_CASES = []

for case_file in sorted(GOLDEN_CASES_DIR.glob("case_*.json")):
    with open(case_file, encoding="utf-8") as f:
        case = json.load(f)
        case["_file"] = case_file.name
        GOLDEN_CASES.append(case)


@pytest.fixture(scope="module")
def engines():
    """Initialize all Stage-3 engines once."""
    return {
        "climate_advice": ClimateAdvice(),
        "luck_flow": LuckFlow(),
        "gyeokguk": GyeokgukClassifier(),
        "pattern": PatternProfiler(),
    }


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["_file"] for c in GOLDEN_CASES])
def test_climate_advice_match(case, engines):
    """Test ClimateAdvice engine against golden case expectations."""
    if "climate_policy_id" not in case.get("expect", {}):
        pytest.skip("No climate_policy_id expectation")

    result = engines["climate_advice"].run(case)
    expected_id = case["expect"]["climate_policy_id"]

    assert (
        result["matched_policy_id"] == expected_id
    ), f"Expected climate_policy_id={expected_id}, got {result['matched_policy_id']}"
    assert result["engine"] == "climate_advice"
    assert "evidence_ref" in result


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["_file"] for c in GOLDEN_CASES])
def test_luck_flow_trend(case, engines):
    """Test LuckFlow engine against golden case expectations."""
    if "luck_flow_trend" not in case.get("expect", {}):
        pytest.skip("No luck_flow_trend expectation")

    result = engines["luck_flow"].run(case)
    expected_trend = case["expect"]["luck_flow_trend"]

    assert (
        result["trend"] == expected_trend
    ), f"Expected trend={expected_trend}, got {result['trend']}"
    assert result["engine"] == "luck_flow"
    assert "evidence_ref" in result
    assert "drivers" in result
    assert "detractors" in result


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["_file"] for c in GOLDEN_CASES])
def test_gyeokguk_type(case, engines):
    """Test GyeokgukClassifier engine against golden case expectations."""
    if "gyeokguk_type" not in case.get("expect", {}):
        pytest.skip("No gyeokguk_type expectation")

    result = engines["gyeokguk"].run(case)
    expected_type = case["expect"]["gyeokguk_type"]

    assert result["type"] == expected_type, f"Expected type={expected_type}, got {result['type']}"
    assert result["engine"] == "gyeokguk_classifier"
    assert "evidence_ref" in result
    assert "basis" in result


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["_file"] for c in GOLDEN_CASES])
def test_pattern_profiler_patterns(case, engines):
    """Test PatternProfiler engine against golden case expectations."""
    if "patterns_include" not in case.get("expect", {}):
        pytest.skip("No patterns_include expectation")

    result = engines["pattern"].run(case)
    expected_patterns = set(case["expect"]["patterns_include"])
    actual_patterns = set(result.get("patterns", []))

    assert expected_patterns.issubset(
        actual_patterns
    ), f"Expected patterns {expected_patterns} not found in {actual_patterns}"
    assert result["engine"] == "pattern_profiler"
    assert "evidence_ref" in result


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["_file"] for c in GOLDEN_CASES])
def test_e2e_pipeline(case, engines):
    """Test complete Stage-3 pipeline: luck_flow → gyeokguk → climate → pattern."""
    # Run in sequence
    lf_result = engines["luck_flow"].run(case)

    # Enrich context with luck_flow result
    ctx_with_lf = {**case, "luck_flow": lf_result}
    gk_result = engines["gyeokguk"].run(ctx_with_lf)

    ca_result = engines["climate_advice"].run(case)

    # Enrich context with all results
    ctx_full = {**ctx_with_lf, "gyeokguk": gk_result}
    pp_result = engines["pattern"].run(ctx_full)

    # Verify all engines produced output
    assert lf_result is not None
    assert gk_result is not None
    assert ca_result is not None
    assert pp_result is not None

    # Verify evidence_ref present in all
    for result in [lf_result, gk_result, ca_result, pp_result]:
        assert (
            "evidence_ref" in result
        ), f"Missing evidence_ref in {result.get('engine', 'unknown')}"


def test_golden_cases_loaded():
    """Verify all 20 golden cases are loaded."""
    assert len(GOLDEN_CASES) == 20, f"Expected 20 golden cases, found {len(GOLDEN_CASES)}"

    # Verify each case has required fields
    for case in GOLDEN_CASES:
        assert "id" in case, "Case missing 'id' field"
        assert "context" in case, "Case missing 'context' field"
        assert "strength" in case, "Case missing 'strength' field"
        assert "expect" in case, "Case missing 'expect' field"


def test_policy_loader_fallback():
    """Test that policy loader can find files in fallback directories."""
    from services.common.policy_loader import resolve_policy_path

    # Should find in ./policy/ or legacy directories
    climate_policy = resolve_policy_path("climate_advice_policy_v1.json")
    assert climate_policy.exists(), "Climate policy not found by loader"

    luck_policy = resolve_policy_path("luck_flow_policy_v1.json")
    assert luck_policy.exists(), "Luck flow policy not found by loader"

    gyeokguk_policy = resolve_policy_path("gyeokguk_policy_v1.json")
    assert gyeokguk_policy.exists(), "Gyeokguk policy not found by loader"

    pattern_policy = resolve_policy_path("pattern_profiler_policy_v1.json")
    assert pattern_policy.exists(), "Pattern profiler policy not found by loader"
