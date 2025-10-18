#!/usr/bin/env python3
"""
Yongshin Selector v1.0 - Test Runner

Runs all test cases from yongshin_cases_v1.jsonl and validates:
1. Output schema compliance
2. Expected yongshin elements present
3. Confidence threshold met
4. Gisin elements present (if specified)
"""

import json
import sys
from pathlib import Path

# Add parent directory to import yongshin_selector directly
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# Import directly to avoid triggering full app imports
import importlib.util

spec = importlib.util.spec_from_file_location(
    "yongshin_selector",
    str(Path(__file__).resolve().parents[1] / "app" / "core" / "yongshin_selector.py"),
)
yongshin_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yongshin_module)
YongshinSelector = yongshin_module.YongshinSelector


def load_test_cases(jsonl_path: str):
    """Load JSONL test cases."""
    cases = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def validate_output_schema(output: dict, case_name: str) -> None:
    """Validate output has required fields."""
    required = [
        "policy_version",
        "yongshin",
        "gisin",
        "confidence",
        "rationale",
        "scores",
        "rules_fired",
    ]

    for field in required:
        assert field in output, f"[{case_name}] Missing field: {field}"

    # Validate types
    assert isinstance(output["yongshin"], list), f"[{case_name}] yongshin must be list"
    assert isinstance(output["gisin"], list), f"[{case_name}] gisin must be list"
    assert isinstance(
        output["confidence"], (int, float)
    ), f"[{case_name}] confidence must be number"
    assert isinstance(output["scores"], dict), f"[{case_name}] scores must be dict"
    assert isinstance(output["rules_fired"], list), f"[{case_name}] rules_fired must be list"

    # Validate ranges
    assert 0.0 <= output["confidence"] <= 1.0, f"[{case_name}] confidence out of range"
    assert len(output["yongshin"]) >= 1, f"[{case_name}] yongshin must have at least 1 element"
    assert len(output["gisin"]) >= 1, f"[{case_name}] gisin must have at least 1 element"


def validate_expectations(output: dict, expected: dict, case_name: str) -> None:
    """Validate output meets test expectations."""
    # Check yongshin contains expected elements
    expected_yongshin = expected.get("yongshin", [])
    for elem in expected_yongshin:
        assert elem in output["yongshin"] or elem in output.get(
            "bojosin", []
        ), f"[{case_name}] Expected yongshin/bojosin element '{elem}' not found in output"

    # Check gisin contains expected elements
    expected_gisin = expected.get("gisin", [])
    for elem in expected_gisin:
        assert (
            elem in output["gisin"]
        ), f"[{case_name}] Expected gisin element '{elem}' not found in output"

    # Check confidence threshold
    min_confidence = expected.get("confidence_min", 0.0)
    assert (
        output["confidence"] >= min_confidence
    ), f"[{case_name}] Confidence {output['confidence']} below minimum {min_confidence}"

    # Check bojosin if specified
    expected_bojosin = expected.get("bojosin", [])
    if expected_bojosin:
        for elem in expected_bojosin:
            assert elem in output.get(
                "bojosin", []
            ), f"[{case_name}] Expected bojosin element '{elem}' not found in output"


def run_test_case(selector: YongshinSelector, case: dict) -> tuple:
    """
    Run a single test case.

    Returns:
        (passed: bool, error_msg: str)
    """
    case_name = case["name"]
    input_data = case["input"]
    expected = case["expected"]

    try:
        # Run selector
        output = selector.select(input_data)

        # Validate schema
        validate_output_schema(output, case_name)

        # Validate expectations
        validate_expectations(output, expected, case_name)

        return True, None

    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"[{case_name}] Unexpected error: {e}"


def main():
    """Run all test cases."""
    print("=" * 70)
    print("Yongshin Selector v1.0 - Test Runner")
    print("=" * 70)

    # Load policy
    # From tests/ → analysis-service → services → 사주
    repo_root = Path(__file__).resolve().parents[3]
    policy_path = str(repo_root / "policy" / "yongshin_selector_policy_v1.json")
    selector = YongshinSelector(policy_path=policy_path)

    # Load test cases
    jsonl_path = str(repo_root / "tests" / "yongshin_cases_v1.jsonl")
    cases = load_test_cases(jsonl_path)

    print(f"\nLoaded {len(cases)} test cases from {Path(jsonl_path).name}")
    print()

    # Run tests
    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        case_name = case["name"]
        success, error = run_test_case(selector, case)

        if success:
            passed += 1
            print(f"✅ [{i}/{len(cases)}] {case_name}")
        else:
            failed += 1
            print(f"❌ [{i}/{len(cases)}] {case_name}")
            print(f"   {error}")
            errors.append((case_name, error))

    # Summary
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed (total {len(cases)})")
    print("=" * 70)

    if failed > 0:
        print("\n⚠️  Failed cases:")
        for case_name, error in errors:
            print(f"  - {case_name}")
            print(f"    {error}")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
