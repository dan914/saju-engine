"""
Property Tests for Sixty Jiazi Policy (六十甲子 v1.0).

Validates:
- Schema compliance
- Uniqueness and progression rules
- Yin/Yang and element distributions
- NaYin pairing rules
- Label completeness and pattern matching
- Dependency integrity
"""

import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import validate

BASE = Path(__file__).resolve().parents[3]
POLICY_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "sixty_jiazi.json"
SCHEMA_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "schemas" / "sixty_jiazi.schema.json"
LOCALIZATION_PATH = (
    BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "localization_en_v1.json"
)


def load_policy() -> dict:
    """Load sixty_jiazi policy."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_schema() -> dict:
    """Load sixty_jiazi schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_localization() -> dict:
    """Load localization_en_v1 policy."""
    return json.loads(LOCALIZATION_PATH.read_text(encoding="utf-8"))


# P0 — Schema Validity
def test_schema_validation():
    """Policy must pass schema validation."""
    policy = load_policy()
    schema = load_schema()

    # Should not raise
    validate(instance=policy, schema=schema)


# P1 — Uniqueness (Unique Pair)
def test_unique_stem_branch_pairs():
    """All (stem, branch) combinations must be unique."""
    policy = load_policy()
    pairs = [(r["stem"], r["branch"]) for r in policy["records"]]

    assert len(pairs) == len(set(pairs)), "Duplicate stem-branch pairs found"
    assert len(pairs) == 60


# P2 — Index Progression Rules
def test_index_progression():
    """Stem and branch indices must follow modulo progression."""
    policy = load_policy()

    for record in policy["records"]:
        idx = record["index"]
        expected_stem_idx = ((idx - 1) % 10) + 1
        expected_branch_idx = ((idx - 1) % 12) + 1

        assert (
            record["stem_index"] == expected_stem_idx
        ), f"Record {idx}: stem_index {record['stem_index']} != expected {expected_stem_idx}"
        assert (
            record["branch_index"] == expected_branch_idx
        ), f"Record {idx}: branch_index {record['branch_index']} != expected {expected_branch_idx}"


# P3 — Wrapping Integrity
def test_wrapping_integrity():
    """Last record must have index=60, and cycle wraps to 1."""
    policy = load_policy()

    last_record = policy["records"][-1]
    assert last_record["index"] == 60

    # Check documented wrapping
    assert policy["relationships"]["next_cycle"] == "wraps after 60 → 1"


# P4 — Yin/Yang Distribution
def test_yin_yang_distribution():
    """Must have exactly 30 Yang and 30 Yin."""
    policy = load_policy()

    polarities = [r["polarity"] for r in policy["records"]]
    counter = Counter(polarities)

    assert counter["陽"] == 30
    assert counter["陰"] == 30

    # Verify matches relationships metadata
    assert policy["relationships"]["yin_yang_distribution"]["yang"] == 30
    assert policy["relationships"]["yin_yang_distribution"]["yin"] == 30


# P5 — Element Distribution (Stem-based)
def test_element_distribution():
    """Each element must appear exactly 12 times."""
    policy = load_policy()

    elements = [r["element"] for r in policy["records"]]
    counter = Counter(elements)

    for elem in ["木", "火", "土", "金", "水"]:
        assert counter[elem] == 12, f"Element {elem} count: {counter[elem]} != 12"

    # Verify matches relationships metadata
    for elem in ["木", "火", "土", "金", "水"]:
        assert policy["relationships"]["element_distribution"][elem] == 12


# P6 — NaYin Pairing Rules
def test_nayin_pairs():
    """Each NaYin must appear exactly twice, with same nayin_element."""
    policy = load_policy()

    # Group by nayin
    nayin_groups = {}
    for record in policy["records"]:
        nayin = record["nayin"]
        if nayin not in nayin_groups:
            nayin_groups[nayin] = []
        nayin_groups[nayin].append(record)

    # Each group must have size 2
    for nayin, group in nayin_groups.items():
        assert len(group) == 2, f"NaYin '{nayin}' has {len(group)} records (expected 2)"

        # All nayin_element in group must be equal
        nayin_elements = [r["nayin_element"] for r in group]
        assert (
            len(set(nayin_elements)) == 1
        ), f"NaYin '{nayin}' has inconsistent nayin_elements: {nayin_elements}"


# P7 — Label Completeness
def test_label_completeness():
    """All records must have non-empty labels."""
    policy = load_policy()

    for record in policy["records"]:
        assert record["label_ko"], f"Record {record['index']} missing label_ko"
        assert record["label_zh"], f"Record {record['index']} missing label_zh"
        assert record["label_en"], f"Record {record['index']} missing label_en"


# P8 — Stem/Branch Enum Compliance
def test_stem_branch_enums():
    """Stems and branches must be in valid sets."""
    policy = load_policy()

    valid_stems = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
    valid_branches = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}

    for record in policy["records"]:
        assert record["stem"] in valid_stems, f"Invalid stem: {record['stem']}"
        assert record["branch"] in valid_branches, f"Invalid branch: {record['branch']}"


# P9 — Dependency Integrity
def test_dependency_integrity():
    """All dependencies must have name, version, and signature."""
    policy = load_policy()
    deps = policy["dependencies"]

    required_deps = ["elements_distribution", "branch_tengods_policy", "localization_en"]

    for dep_name in required_deps:
        assert dep_name in deps, f"Missing dependency: {dep_name}"
        dep = deps[dep_name]

        assert "name" in dep, f"{dep_name} missing 'name'"
        assert "version" in dep, f"{dep_name} missing 'version'"
        assert "signature" in dep, f"{dep_name} missing 'signature'"
        assert dep["signature"], f"{dep_name} has empty signature"


# P10 — label_en Pattern Match
def test_label_en_pattern():
    """All label_en must match the standard pattern."""
    policy = load_policy()
    localization = load_localization()

    pattern = localization["label_en_pattern"]
    regex = re.compile(pattern)

    for record in policy["records"]:
        label_en = record["label_en"]
        assert regex.match(
            label_en
        ), f"Record {record['index']} label_en '{label_en}' does not match pattern {pattern}"


# P11 — label_en Glossary Match
def test_label_en_glossary():
    """All NaYin must exist in localization glossary, and label_en parentheses must match."""
    policy = load_policy()
    localization = load_localization()

    nayin_en = localization["nayin_en"]

    for record in policy["records"]:
        nayin = record["nayin"]
        label_en = record["label_en"]

        # NaYin must exist in glossary
        assert nayin in nayin_en, f"NaYin '{nayin}' not in localization glossary"

        # Extract text inside parentheses
        match = re.search(r"\(([^)]+)\)", label_en)
        assert match, f"Record {record['index']} label_en '{label_en}' has no parentheses"

        nayin_text = match.group(1)
        expected_text = nayin_en[nayin]

        assert (
            nayin_text == expected_text
        ), f"Record {record['index']} NaYin '{nayin}': label_en has '{nayin_text}', expected '{expected_text}'"


# P12 — Signature Mode
def test_signature_mode():
    """Policy must have sha256_auto_injected signature mode."""
    policy = load_policy()

    assert policy.get("signature_mode") == "sha256_auto_injected"
    assert "signature" in policy


def test_all_nayin_values():
    """Verify all 30 unique NaYin values are present."""
    policy = load_policy()

    expected_nayin = {
        "海中金",
        "炉中火",
        "大林木",
        "路旁土",
        "剑锋金",
        "山头火",
        "涧下水",
        "城头土",
        "白蜡金",
        "杨柳木",
        "泉中水",
        "屋上土",
        "霹雳火",
        "松柏木",
        "长流水",
        "砂中金",
        "山下火",
        "平地木",
        "壁上土",
        "金箔金",
        "覆灯火",
        "天河水",
        "大驿土",
        "钗钏金",
        "桑柘木",
        "大溪水",
        "沙中土",
        "天上火",
        "石榴木",
        "大海水",
    }

    actual_nayin = {r["nayin"] for r in policy["records"]}
    assert actual_nayin == expected_nayin


def test_first_record():
    """First record must be Jia-Zi."""
    policy = load_policy()

    first = policy["records"][0]
    assert first["index"] == 1
    assert first["stem"] == "甲"
    assert first["branch"] == "子"
    assert first["label_en"] == "Jia-Zi (Metal in the Sea)"


def test_last_record():
    """Last record must be Gui-Hai."""
    policy = load_policy()

    last = policy["records"][-1]
    assert last["index"] == 60
    assert last["stem"] == "癸"
    assert last["branch"] == "亥"
    assert last["label_en"] == "Gui-Hai (Great Sea Water)"
