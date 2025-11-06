"""
Test strength policy v2.0.1 schema validation and structure.

Validates the three key improvements in v2.0.1:
1. CI weight sum assertion (W_SUM_100)
2. Separated relation_policy apply switch
3. Common hidden_weights with JSON Pointer references
"""

import json
from pathlib import Path

from jsonschema import validate

BASE = Path(__file__).resolve().parents[3]
POLICY_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "strength_policy_v2.json"
SCHEMA_PATH = (
    BASE / "saju_codex_batch_all_v2_6_signed" / "schemas" / "strength_policy_v2.schema.json"
)


def load_policy() -> dict:
    """Load strength policy v2."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_schema() -> dict:
    """Load strength policy v2 schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_validation():
    """Policy should pass schema validation."""
    policy = load_policy()
    schema = load_schema()

    # Should not raise
    validate(instance=policy, schema=schema)


def test_version():
    """Policy version should be 2.0.1."""
    policy = load_policy()
    assert policy["version"] == "2.0.1"


def test_engine_name_ko():
    """Policy should have Korean engine name."""
    policy = load_policy()
    assert policy["engine_name_ko"] == "강약 평가기 v2"


def test_ci_checks_weight_sum():
    """CI checks should enforce weight sum = 100."""
    policy = load_policy()

    # Should have ci_checks
    assert "ci_checks" in policy
    assert policy["ci_checks"]["on_fail"] == "fail_build"

    # Should have W_SUM_100 assertion
    assertions = policy["ci_checks"]["assertions"]
    weight_sum_assertion = next((a for a in assertions if a["id"] == "W_SUM_100"), None)
    assert weight_sum_assertion is not None
    assert (
        "weights.deukryeong + weights.deukji + weights.deuksi + weights.deukse == 100"
        in weight_sum_assertion["expr"]
    )


def test_weights_sum_to_100():
    """Weights should actually sum to 100."""
    policy = load_policy()
    weights = policy["weights"]

    total = weights["deukryeong"] + weights["deukji"] + weights["deuksi"] + weights["deukse"]
    assert total == 100.0


def test_relation_policy_apply_separated():
    """relation_policy.apply should be in options, not dependencies."""
    policy = load_policy()

    # Dependencies should NOT have apply
    deps = policy["dependencies"]["relation_policy"]
    assert "apply" not in deps

    # Options should have apply
    assert "options" in policy
    assert "relation_policy" in policy["options"]
    assert "apply" in policy["options"]["relation_policy"]
    assert policy["options"]["relation_policy"]["apply"] is False


def test_common_hidden_weights_exists():
    """Policy should have common_hidden_weights at root level."""
    policy = load_policy()

    assert "common_hidden_weights" in policy
    common = policy["common_hidden_weights"]

    assert common["primary"] == 1.0
    assert common["secondary"] == 0.6
    assert common["tertiary"] == 0.3


def test_deukji_uses_hidden_weights_ref():
    """deukji should use hidden_weights_ref, not inline hidden_weights."""
    policy = load_policy()
    deukji = policy["deukji"]

    # Should have ref
    assert "hidden_weights_ref" in deukji
    assert deukji["hidden_weights_ref"] == "#/common_hidden_weights"

    # Should NOT have inline weights
    assert "hidden_weights" not in deukji


def test_deuksi_uses_hidden_weights_ref():
    """deuksi should use hidden_weights_ref."""
    policy = load_policy()
    deuksi = policy["deuksi"]

    # Should have ref
    assert "hidden_weights_ref" in deuksi
    assert deuksi["hidden_weights_ref"] == "#/common_hidden_weights"


def test_ci_assertion_hidden_ref_exists():
    """CI checks should validate JSON pointer exists."""
    policy = load_policy()

    assertions = policy["ci_checks"]["assertions"]
    hidden_ref_assertion = next((a for a in assertions if a["id"] == "HIDDEN_REF_EXISTS"), None)
    assert hidden_ref_assertion is not None
    assert "#/common_hidden_weights" in hidden_ref_assertion["expr"]


def test_bucket_order_assertion():
    """CI checks should enforce bucket threshold ordering."""
    policy = load_policy()

    assertions = policy["ci_checks"]["assertions"]
    bucket_order = next((a for a in assertions if a["id"] == "BUCKET_ORDER"), None)
    assert bucket_order is not None

    # Verify actual order
    t = policy["buckets"]["thresholds"]
    assert t["tae_gang"] > t["jung_gang"] > t["jung_hwa"] > t["jung_yak"] > t["tae_yak"]


def test_all_dependencies_have_signature():
    """All dependencies should have name, version, signature fields."""
    policy = load_policy()
    deps = policy["dependencies"]

    for dep_name, dep_config in deps.items():
        assert "name" in dep_config, f"{dep_name} missing 'name'"
        assert "version" in dep_config, f"{dep_name} missing 'version'"
        assert "signature" in dep_config, f"{dep_name} missing 'signature'"


def test_labels_multilingual():
    """Bucket labels should have ko, zh, en."""
    policy = load_policy()
    labels = policy["buckets"]["labels"]

    assert "ko" in labels
    assert "zh" in labels
    assert "en" in labels

    # All should have same keys
    for lang, lang_labels in labels.items():
        assert set(lang_labels.keys()) == {
            "tae_gang",
            "jung_gang",
            "jung_hwa",
            "jung_yak",
            "tae_yak",
        }
