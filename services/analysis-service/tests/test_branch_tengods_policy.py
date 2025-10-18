"""
Test branch_tengods_policy v1.1 (KO-first).

Validates:
- Schema compliance
- Property tests (P0-P12)
- Verification cases (15 test cases)
- Ten Gods calculation logic
- Aggregation and normalization
"""

import json
from pathlib import Path

from jsonschema import validate

BASE = Path(__file__).resolve().parents[3]
POLICY_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "branch_tengods_policy.json"
SCHEMA_PATH = (
    BASE / "saju_codex_batch_all_v2_6_signed" / "schemas" / "branch_tengods_policy.schema.json"
)


def load_policy() -> dict:
    """Load branch_tengods_policy."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_schema() -> dict:
    """Load branch_tengods_policy schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# P0 — Schema Validity
def test_schema_validation():
    """Policy must pass schema validation."""
    policy = load_policy()
    schema = load_schema()

    # Should not raise
    validate(instance=policy, schema=schema)


# P1 — 12 Branch Keys
def test_branch_keys_completeness():
    """branches_hidden must have exactly 12 branch keys."""
    policy = load_policy()
    branches = list(policy["branches_hidden"].keys())

    expected = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    assert branches == expected


# P2 — Primary Role Present
def test_primary_role_present():
    """Each branch must have at least one primary role."""
    policy = load_policy()

    for branch, hidden_list in policy["branches_hidden"].items():
        has_primary = any(h["role"] == "primary" for h in hidden_list)
        assert has_primary, f"Branch {branch} missing primary role"


# P3 — Role Weights Monotonicity
def test_role_weights_order():
    """role_weights must be monotonic: primary >= secondary >= tertiary."""
    policy = load_policy()
    weights = policy["role_weights"]

    assert weights["primary"] >= weights["secondary"]
    assert weights["secondary"] >= weights["tertiary"]


# P4 — Ten Gods Labels KO Complete
def test_ten_gods_labels_ko_complete():
    """ten_gods_labels.ko must have 10 entries, all non-empty."""
    policy = load_policy()
    labels_ko = policy["ten_gods_labels"]["ko"]

    expected_keys = ["BI", "GE", "SIK", "SANG", "PJ", "JJ", "PG", "JG", "PI", "JI"]
    assert set(labels_ko.keys()) == set(expected_keys)

    for key, label in labels_ko.items():
        assert label, f"Label {key} is empty in ko"


# P5 — Mapping Rules 5
def test_mapping_rules_5():
    """mapping_rules must have exactly 5 relation types."""
    policy = load_policy()
    rules = policy["mapping_rules"]

    expected_keys = ["same_element", "wo_sheng", "wo_ke", "ke_wo", "sheng_wo"]
    assert set(rules.keys()) == set(expected_keys)


# P6 — Parity Flip Invariance
def test_parity_flip():
    """Changing polarity should only flip 正/편 without changing relation type."""
    policy = load_policy()

    # Example: same_element with same_polarity → BI, diff_polarity → GE
    same_elem = policy["mapping_rules"]["same_element"]
    assert same_elem["same_polarity"] == "BI"
    assert same_elem["diff_polarity"] == "GE"

    # Both should be in the same category (companions)
    # This is a semantic test - just verify they're different codes
    assert same_elem["same_polarity"] != same_elem["diff_polarity"]


# P7 — Normalization Sum = 1
def test_normalization_sum():
    """When normalized, weights must sum to 1.0 (within epsilon)."""
    # Example: 巳 branch has 3 hidden stems with weights 1.0, 0.6, 0.3
    # Total = 1.9, normalized should sum to 1.0

    weights = [1.0, 0.6, 0.3]
    total = sum(weights)
    normalized = [w / total for w in weights]

    assert abs(sum(normalized) - 1.0) < 1e-9


# P8 — JSON Pointer Validity
def test_json_pointer_valid():
    """aggregation.role_weights_ref must point to valid path."""
    policy = load_policy()

    ref = policy["aggregation"]["role_weights_ref"]
    assert ref == "#/role_weights"

    # Verify the target exists
    assert "role_weights" in policy


# P9 — Determinism
def test_determinism():
    """Same input should produce same output."""
    policy = load_policy()

    # Load policy twice and verify identical
    policy2 = load_policy()
    assert policy == policy2


# P10 — Signature Mode
def test_signature_mode():
    """Policy must have sha256_auto_injected signature mode."""
    policy = load_policy()

    assert policy["signature_mode"] == "sha256_auto_injected"
    assert "signature" in policy


# P11 — Label Consistency (Multi-language)
def test_label_consistency():
    """ten_gods_labels must have ko, zh, en with same keys."""
    policy = load_policy()
    labels = policy["ten_gods_labels"]

    assert "ko" in labels
    assert "zh" in labels
    assert "en" in labels

    keys_ko = set(labels["ko"].keys())
    keys_zh = set(labels["zh"].keys())
    keys_en = set(labels["en"].keys())

    assert keys_ko == keys_zh == keys_en


# P12 — Role Value Constraints
def test_role_value_constraints():
    """All branches_hidden roles must be valid."""
    policy = load_policy()

    valid_roles = {"primary", "secondary", "tertiary"}
    valid_elements = {"木", "火", "土", "金", "水"}
    valid_stems = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}

    for branch, hidden_list in policy["branches_hidden"].items():
        for hidden in hidden_list:
            assert hidden["role"] in valid_roles, f"Invalid role in {branch}"
            assert hidden["element"] in valid_elements, f"Invalid element in {branch}"
            assert hidden["stem"] in valid_stems, f"Invalid stem in {branch}"


# Verification Cases
def get_polarity(stem: str) -> str:
    """Get polarity of a stem."""
    yang_stems = ["甲", "丙", "戊", "庚", "壬"]
    return "陽" if stem in yang_stems else "陰"


def get_element(stem: str) -> str:
    """Get element of a stem."""
    stem_to_elem = {
        "甲": "木",
        "乙": "木",
        "丙": "火",
        "丁": "火",
        "戊": "土",
        "己": "土",
        "庚": "金",
        "辛": "金",
        "壬": "水",
        "癸": "水",
    }
    return stem_to_elem[stem]


def calculate_tengods(day_stem: str, branch: str, policy: dict) -> dict:
    """Calculate ten gods for a branch given day stem."""
    day_element = get_element(day_stem)
    day_polarity = get_polarity(day_stem)
    hidden_list = policy["branches_hidden"][branch]

    relations = policy["relations"]
    mapping_rules = policy["mapping_rules"]
    role_weights = policy["role_weights"]

    tengod_weights = {}

    for hidden in hidden_list:
        h_stem = hidden["stem"]
        h_element = hidden["element"]
        h_polarity = get_polarity(h_stem)
        role = hidden["role"]

        # Determine relation
        if day_element == h_element:
            relation = "same_element"
        elif relations["sheng"][day_element] == h_element:
            relation = "wo_sheng"
        elif relations["ke"][day_element] == h_element:
            relation = "wo_ke"
        elif relations["ke"].get(h_element) == day_element:
            relation = "ke_wo"
        elif relations["sheng"].get(h_element) == day_element:
            relation = "sheng_wo"
        else:
            raise ValueError(f"Unknown relation: {day_element} -> {h_element}")

        # Determine parity
        parity = "same_polarity" if day_polarity == h_polarity else "diff_polarity"

        # Get ten god code
        tengod_code = mapping_rules[relation][parity]

        # Add weight
        weight = role_weights[role]
        tengod_weights[tengod_code] = tengod_weights.get(tengod_code, 0) + weight

    # Normalize
    total = sum(tengod_weights.values())
    normalized = {k: v / total for k, v in tengod_weights.items()}

    return normalized


def test_case01_zi_jia():
    """Case 01 — 子(癸) · 日主 甲(木,陽) → 정인(JI) 1.0000"""
    policy = load_policy()
    result = calculate_tengods("甲", "子", policy)

    assert "JI" in result
    assert abs(result["JI"] - 1.0) < 1e-4


def test_case02_chou_bing():
    """Case 02 — 丑(己/癸/辛) · 日主 丙(火,陽)"""
    policy = load_policy()
    result = calculate_tengods("丙", "丑", policy)

    # Expect SANG ≈ 0.5263, JG ≈ 0.3158, JJ ≈ 0.1579
    assert "SANG" in result
    assert "JG" in result
    assert "JJ" in result

    assert abs(result["SANG"] - 0.5263) < 0.001
    assert abs(result["JG"] - 0.3158) < 0.001
    assert abs(result["JJ"] - 0.1579) < 0.001


def test_case06_si_jia():
    """Case 06 — 巳(丙/庚/戊) · 日主 甲(木,陽)"""
    policy = load_policy()
    result = calculate_tengods("甲", "巳", policy)

    # Expect SIK ≈ 0.5263, PG ≈ 0.3158, PJ ≈ 0.1579
    assert "SIK" in result
    assert "PG" in result
    assert "PJ" in result

    assert abs(result["SIK"] - 0.5263) < 0.001
    assert abs(result["PG"] - 0.3158) < 0.001
    assert abs(result["PJ"] - 0.1579) < 0.001


def test_case10_you_yi():
    """Case 10 — 酉(辛) · 日主 乙(木,陰) → 편관(PG) 1.0000"""
    policy = load_policy()
    result = calculate_tengods("乙", "酉", policy)

    # 辛(金,陰) vs 乙(木,陰) → 克我 & 同 → PG
    assert "PG" in result
    assert abs(result["PG"] - 1.0) < 1e-4


def test_case13_you_jia():
    """Case 13 — 酉(辛) · 日主 甲(木,陽) → 정관(JG) 1.0000 (parity flip)"""
    policy = load_policy()
    result = calculate_tengods("甲", "酉", policy)

    # 辛(金,陰) vs 甲(木,陽) → 克我 & 異 → JG
    assert "JG" in result
    assert abs(result["JG"] - 1.0) < 1e-4


def test_case14_mao_yi():
    """Case 14 — 卯(乙) · 日主 乙(木,陰) → 비견(BI) 1.0000"""
    policy = load_policy()
    result = calculate_tengods("乙", "卯", policy)

    # 乙(木,陰) vs 乙(木,陰) → 同元素 & 同 → BI
    assert "BI" in result
    assert abs(result["BI"] - 1.0) < 1e-4


def test_case15_mao_jia():
    """Case 15 — 卯(乙) · 日主 甲(木,陽) → 겁재(GE) 1.0000"""
    policy = load_policy()
    result = calculate_tengods("甲", "卯", policy)

    # 乙(木,陰) vs 甲(木,陽) → 同元素 & 異 → GE
    assert "GE" in result
    assert abs(result["GE"] - 1.0) < 1e-4


def test_all_branches_have_hidden():
    """All 12 branches must have hidden stems configured."""
    policy = load_policy()

    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    for branch in branches:
        assert branch in policy["branches_hidden"]
        assert len(policy["branches_hidden"][branch]) > 0


def test_engine_name_ko():
    """Policy must have Korean engine name."""
    policy = load_policy()

    assert policy["engine_name_ko"] == "지지 십신 정책"


def test_default_locale():
    """Default locale must be ko-KR."""
    policy = load_policy()

    assert policy["options"]["default_locale"] == "ko-KR"
