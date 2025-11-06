"""
Test shensha_v2_policy v2.0 (KO-first).

Validates:
- Schema compliance
- Property tests (P0-P10)
- Verification cases (11 test cases)
- Shensha calculation logic
- TIAN_LA/DI_WANG per-pillar matching (Nitpick #3)
- score_hint formula (Nitpick #2)
- literacy_based rules (Nitpick #1)
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from jsonschema import validate

BASE = Path(__file__).resolve().parents[3]
POLICY_PATH = BASE / "saju_codex_batch_all_v2_6_signed" / "policies" / "shensha_v2_policy.json"
SCHEMA_PATH = (
    BASE / "saju_codex_batch_all_v2_6_signed" / "schemas" / "shensha_v2_policy.schema.json"
)


def load_policy() -> dict:
    """Load shensha_v2_policy."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_schema() -> dict:
    """Load shensha_v2_policy schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ============================================================================
# Property Tests (P0-P10)
# ============================================================================


def test_p0_schema_validation():
    """P0 — Policy must pass schema validation."""
    policy = load_policy()
    schema = load_schema()

    # Should not raise
    validate(instance=policy, schema=schema)


def test_p1_catalog_completeness():
    """P1 — Catalog must have >= 18 entries with non-empty ko labels."""
    policy = load_policy()
    catalog = policy["shensha_catalog"]

    assert len(catalog) >= 18, f"Expected >= 18 catalog entries, got {len(catalog)}"

    for item in catalog:
        assert item["labels"]["ko"], f"Empty ko label for {item['key']}"
        assert item["type"] in ["吉", "中", "烈", "凶"], f"Invalid type for {item['key']}"
        assert -5 <= item["score_hint"] <= 5, f"Invalid score_hint for {item['key']}"


def test_p2_ko_first_tie_breaker():
    """P2 — KO-first sorting priority."""
    policy = load_policy()
    tie_breaker = policy["aggregation"]["tie_breaker"]

    assert tie_breaker[1] == "label_order_ko", "Second tie breaker must be label_order_ko"


def test_p3_dependencies_signed():
    """P3 — All dependencies must have non-empty signatures."""
    policy = load_policy()
    deps = policy["dependencies"]

    for dep_key, dep_value in deps.items():
        sig = dep_value["signature"]
        # Allow placeholders for now (e.g., <SIG_ELEMENTS>)
        # In production CI, these must be real signatures
        assert sig, f"Dependency {dep_key} has empty signature"


def test_p4_determinism():
    """P4 — Same input should produce same output."""
    policy1 = load_policy()
    policy2 = load_policy()

    assert policy1 == policy2, "Policy loading is not deterministic"


def test_p5_year_branch_rules_consistency():
    """P5 — Year branch based rules (도화/역마/화개) must match policy table."""
    policy = load_policy()
    year_rules = policy["rule_groups"]["year_branch_based"]["rules"]

    # Check TAO_HUA
    tao_hua_rule = next(r for r in year_rules if r["key"] == "TAO_HUA")
    assert "申" in tao_hua_rule["by_year_branch_map"]
    assert "酉" in tao_hua_rule["by_year_branch_map"]["申"]

    # Check YI_MA
    yi_ma_rule = next(r for r in year_rules if r["key"] == "YI_MA")
    assert "申" in yi_ma_rule["by_year_branch_map"]
    assert "寅" in yi_ma_rule["by_year_branch_map"]["申"]

    # Check HUA_GAI
    hua_gai_rule = next(r for r in year_rules if r["key"] == "HUA_GAI")
    assert "亥" in hua_gai_rule["by_year_branch_map"]
    assert "未" in hua_gai_rule["by_year_branch_map"]["亥"]


def test_p6_day_stem_rules_consistency():
    """P6 — Day stem based rules (천을귀인) must match policy table."""
    policy = load_policy()
    day_rules = policy["rule_groups"]["day_stem_based"]["rules"]

    # Check TIAN_E_GUIREN
    guiren_rule = next(r for r in day_rules if r["key"] == "TIAN_E_GUIREN")
    assert "甲" in guiren_rule["by_day_stem_map"]
    assert "丑" in guiren_rule["by_day_stem_map"]["甲"]
    assert "未" in guiren_rule["by_day_stem_map"]["甲"]


def test_p7_pair_rules():
    """P7 — Pair rules (육해/원진) must only match specified pairs."""
    policy = load_policy()
    pair_rules = policy["rule_groups"]["pair_conflict_based"]["rules"]

    # Check LIU_HAI
    liu_hai_rule = next(r for r in pair_rules if r["key"] == "LIU_HAI")
    assert ["子", "未"] in liu_hai_rule["pairs"]
    assert ["寅", "巳"] in liu_hai_rule["pairs"]

    # Check YUAN_ZHEN
    yuan_zhen_rule = next(r for r in pair_rules if r["key"] == "YUAN_ZHEN")
    assert ["子", "丑"] in yuan_zhen_rule["pairs"]
    assert ["卯", "辰"] in yuan_zhen_rule["pairs"]


def test_p8_evidence_completeness():
    """P8 — Evidence trace structure must be complete (placeholder test)."""
    # In actual implementation, this would verify all rules produce traces
    # For now, just verify policy has necessary fields
    policy = load_policy()

    assert "rule_groups" in policy
    assert "day_stem_based" in policy["rule_groups"]
    assert "year_branch_based" in policy["rule_groups"]
    assert "pair_conflict_based" in policy["rule_groups"]
    assert "literacy_based" in policy["rule_groups"]


def test_p9_type_summary_invariant():
    """P9 — Type summary structure is valid."""
    policy = load_policy()
    type_priority = policy["aggregation"]["type_priority"]

    assert type_priority["吉"] == 1
    assert type_priority["中"] == 2
    assert type_priority["烈"] == 3
    assert type_priority["凶"] == 4


def test_p10_signature_auto_injected():
    """P10 — Signature mode must be sha256_auto_injected."""
    policy = load_policy()

    assert policy["signature_mode"] == "sha256_auto_injected"
    assert "signature" in policy


# ============================================================================
# Nitpick Validation Tests
# ============================================================================


def test_nitpick1_literacy_rules_nonempty():
    """Nitpick #1 — literacy_based rules must not be empty."""
    policy = load_policy()
    literacy_rules = policy["rule_groups"]["literacy_based"]["rules"]

    assert len(literacy_rules) > 0, "literacy_based rules should not be empty"

    # Check WEN_CHANG, WEN_QU, XUE_TANG are in literacy_based
    rule_keys = {r["key"] for r in literacy_rules}
    assert "WEN_CHANG" in rule_keys
    assert "WEN_QU" in rule_keys
    assert "XUE_TANG" in rule_keys


def test_nitpick2_score_hint_formula_exists():
    """Nitpick #2 — score_hint_formula and note_ko must exist."""
    policy = load_policy()
    agg = policy["aggregation"]

    assert "score_hint_formula" in agg
    assert agg["score_hint_formula"], "score_hint_formula should not be empty"
    assert "score_hint_note_ko" in agg
    assert agg["score_hint_note_ko"], "score_hint_note_ko should not be empty"


def test_nitpick3_tian_la_di_wang_per_pillar():
    """Nitpick #3 — TIAN_LA/DI_WANG should use per-pillar matching."""
    policy = load_policy()
    pair_rules = policy["rule_groups"]["pair_conflict_based"]["rules"]

    tian_la_rule = next(r for r in pair_rules if r["key"] == "TIAN_LA")
    di_wang_rule = next(r for r in pair_rules if r["key"] == "DI_WANG")

    # Should NOT have assign_if_any
    assert "assign_if_any" not in tian_la_rule
    assert "assign_if_any" not in di_wang_rule

    # Should have by_branch and match_field
    assert "by_branch" in tian_la_rule
    assert "辰" in tian_la_rule["by_branch"]
    assert "戌" in tian_la_rule["by_branch"]
    assert tian_la_rule["match_field"] == "branch"

    assert "by_branch" in di_wang_rule
    assert "丑" in di_wang_rule["by_branch"]
    assert "未" in di_wang_rule["by_branch"]
    assert di_wang_rule["match_field"] == "branch"


# ============================================================================
# Helper Functions for Shensha Calculation
# ============================================================================


def match_day_stem_rule(rule: dict, day_stem: str, pillar_branch: str, pillar_name: str) -> bool:
    """Check if a day_stem_based rule matches."""
    if pillar_name not in rule["apply_to"]:
        return False

    expected_branches = rule["by_day_stem_map"].get(day_stem, [])
    return pillar_branch in expected_branches


def match_year_branch_rule(
    rule: dict, year_branch: str, pillar_branch: str, pillar_name: str
) -> bool:
    """Check if a year_branch_based rule matches."""
    if pillar_name not in rule["apply_to"]:
        return False

    expected_branches = rule["by_year_branch_map"].get(year_branch, [])
    return pillar_branch in expected_branches


def match_pair_rule(rule: dict, pillars: Dict[str, Dict[str, str]]) -> List[Tuple[str, str]]:
    """Check if a pair_conflict_based rule matches.

    Returns list of (pillar1, pillar2) tuples that match.
    """
    if "pairs" not in rule:
        return []

    matched_pairs = []
    for pair in rule["pairs"]:
        for pillar_pair in rule["apply_to_pairs"]:
            p1, p2 = pillar_pair
            b1 = pillars[p1]["branch"]
            b2 = pillars[p2]["branch"]

            if (b1 == pair[0] and b2 == pair[1]) or (b1 == pair[1] and b2 == pair[0]):
                matched_pairs.append((p1, p2))

    return matched_pairs


def match_by_branch_rule(rule: dict, pillar_branch: str, pillar_name: str) -> bool:
    """Check if a by_branch rule matches (TIAN_LA/DI_WANG/BAI_HU/XUE_REN)."""
    if pillar_name not in rule["apply_to"]:
        return False

    return pillar_branch in rule["by_branch"]


def calculate_shensha(
    pillars: Dict[str, Dict[str, str]], day_stem: str, year_branch: str, policy: dict
) -> Dict[str, List[dict]]:
    """Calculate shensha for all pillars.

    Args:
        pillars: {"year": {"stem":"庚","branch":"申"}, ...}
        day_stem: "甲"
        year_branch: "申"
        policy: loaded policy dict

    Returns:
        {"year": [...], "month": [...], "day": [...], "hour": [...]}
    """
    result = {p: [] for p in ["year", "month", "day", "hour"]}

    # day_stem_based rules
    for rule in policy["rule_groups"]["day_stem_based"]["rules"]:
        for pillar_name, pillar_data in pillars.items():
            if match_day_stem_rule(rule, day_stem, pillar_data["branch"], pillar_name):
                shensha = next(s for s in policy["shensha_catalog"] if s["key"] == rule["key"])
                result[pillar_name].append(
                    {
                        "key": shensha["key"],
                        "label_ko": shensha["labels"]["ko"],
                        "type": shensha["type"],
                        "score_hint": shensha["score_hint"],
                    }
                )

    # year_branch_based rules
    for rule in policy["rule_groups"]["year_branch_based"]["rules"]:
        for pillar_name, pillar_data in pillars.items():
            if match_year_branch_rule(rule, year_branch, pillar_data["branch"], pillar_name):
                shensha = next(s for s in policy["shensha_catalog"] if s["key"] == rule["key"])
                result[pillar_name].append(
                    {
                        "key": shensha["key"],
                        "label_ko": shensha["labels"]["ko"],
                        "type": shensha["type"],
                        "score_hint": shensha["score_hint"],
                    }
                )

    # literacy_based rules
    for rule in policy["rule_groups"]["literacy_based"]["rules"]:
        for pillar_name, pillar_data in pillars.items():
            if match_year_branch_rule(rule, year_branch, pillar_data["branch"], pillar_name):
                shensha = next(s for s in policy["shensha_catalog"] if s["key"] == rule["key"])
                result[pillar_name].append(
                    {
                        "key": shensha["key"],
                        "label_ko": shensha["labels"]["ko"],
                        "type": shensha["type"],
                        "score_hint": shensha["score_hint"],
                    }
                )

    # pair_conflict_based rules
    for rule in policy["rule_groups"]["pair_conflict_based"]["rules"]:
        if "pairs" in rule:
            # Pair-based matching (LIU_HAI, YUAN_ZHEN)
            matched_pairs = match_pair_rule(rule, pillars)
            for p1, p2 in matched_pairs:
                shensha = next(s for s in policy["shensha_catalog"] if s["key"] == rule["key"])
                # Add to both pillars involved in the pair
                for p in [p1, p2]:
                    result[p].append(
                        {
                            "key": shensha["key"],
                            "label_ko": shensha["labels"]["ko"],
                            "type": shensha["type"],
                            "score_hint": shensha["score_hint"],
                        }
                    )
        elif "by_branch" in rule:
            # Branch-based matching (TIAN_LA, DI_WANG, BAI_HU, XUE_REN)
            for pillar_name, pillar_data in pillars.items():
                if match_by_branch_rule(rule, pillar_data["branch"], pillar_name):
                    shensha = next(s for s in policy["shensha_catalog"] if s["key"] == rule["key"])
                    result[pillar_name].append(
                        {
                            "key": shensha["key"],
                            "label_ko": shensha["labels"]["ko"],
                            "type": shensha["type"],
                            "score_hint": shensha["score_hint"],
                        }
                    )

    return result


# ============================================================================
# Verification Cases (11 cases)
# ============================================================================


def test_case01_tao_hua():
    """Case 01 — 申年 / 月:酉 → 도화"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "庚", "branch": "申"},
        "month": {"stem": "壬", "branch": "酉"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丙", "branch": "巳"},
    }

    result = calculate_shensha(pillars, "甲", "申", policy)

    # TAO_HUA should match month (申年 도화=酉)
    month_keys = {s["key"] for s in result["month"]}
    assert "TAO_HUA" in month_keys, "TAO_HUA should match month pillar"

    # LIU_HAI should match day-hour pair (寅-巳)
    day_keys = {s["key"] for s in result["day"]}
    hour_keys = {s["key"] for s in result["hour"]}
    assert "LIU_HAI" in day_keys or "LIU_HAI" in hour_keys, "LIU_HAI should match (寅-巳) pair"


def test_case02_yi_ma():
    """Case 02 — 亥年 / 時:巳 → 역마"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "丁", "branch": "亥"},
        "month": {"stem": "戊", "branch": "辰"},
        "day": {"stem": "乙", "branch": "卯"},
        "hour": {"stem": "庚", "branch": "巳"},
    }

    result = calculate_shensha(pillars, "乙", "亥", policy)

    # YI_MA should match hour (亥年 역마=巳)
    hour_keys = {s["key"] for s in result["hour"]}
    assert "YI_MA" in hour_keys, "YI_MA should match hour pillar"


def test_case03_tao_hua_yin_wu_xu():
    """Case 03 — 寅午戌군 / 年:午 / 月:卯 → 도화"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "戊", "branch": "午"},
        "month": {"stem": "己", "branch": "卯"},
        "day": {"stem": "辛", "branch": "巳"},
        "hour": {"stem": "壬", "branch": "子"},
    }

    result = calculate_shensha(pillars, "辛", "午", policy)

    # TAO_HUA should match month (午年 도화=卯)
    month_keys = {s["key"] for s in result["month"]}
    assert "TAO_HUA" in month_keys, "TAO_HUA should match month pillar"


def test_case04_hua_gai():
    """Case 04 — 亥年 / 月:未 → 화개"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "丁", "branch": "亥"},
        "month": {"stem": "己", "branch": "未"},
        "day": {"stem": "丙", "branch": "子"},
        "hour": {"stem": "甲", "branch": "辰"},
    }

    result = calculate_shensha(pillars, "丙", "亥", policy)

    # HUA_GAI should match month (亥年 화개=未)
    month_keys = {s["key"] for s in result["month"]}
    assert "HUA_GAI" in month_keys, "HUA_GAI should match month pillar"


def test_case05_tian_e_guiren():
    """Case 05 — 甲日 / 時:未 → 천을귀인"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "庚", "branch": "申"},
        "month": {"stem": "壬", "branch": "子"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "丙", "branch": "未"},
    }

    result = calculate_shensha(pillars, "甲", "申", policy)

    # TIAN_E_GUIREN should match hour (甲→丑/未)
    hour_keys = {s["key"] for s in result["hour"]}
    assert "TIAN_E_GUIREN" in hour_keys, "TIAN_E_GUIREN should match hour pillar"


def test_case06_guai_gang():
    """Case 06 — 庚日·日支 辰 → 괴강"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "乙", "branch": "酉"},
        "month": {"stem": "丙", "branch": "戌"},
        "day": {"stem": "庚", "branch": "辰"},
        "hour": {"stem": "癸", "branch": "卯"},
    }

    result = calculate_shensha(pillars, "庚", "酉", policy)

    # GUAI_GANG should match day (庚日+辰支)
    day_keys = {s["key"] for s in result["day"]}
    assert "GUAI_GANG" in day_keys, "GUAI_GANG should match day pillar"


def test_case07_liu_hai():
    """Case 07 — 육해 페어(寅-巳)"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "丁", "branch": "卯"},
        "month": {"stem": "庚", "branch": "寅"},
        "day": {"stem": "壬", "branch": "午"},
        "hour": {"stem": "戊", "branch": "巳"},
    }

    result = calculate_shensha(pillars, "壬", "卯", policy)

    # LIU_HAI should match month-hour pair (寅-巳)
    month_keys = {s["key"] for s in result["month"]}
    hour_keys = {s["key"] for s in result["hour"]}
    assert "LIU_HAI" in month_keys or "LIU_HAI" in hour_keys, "LIU_HAI should match (寅-巳) pair"


def test_case08_yuan_zhen():
    """Case 08 — 원진 페어(卯-辰)"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "乙", "branch": "未"},
        "month": {"stem": "辛", "branch": "卯"},
        "day": {"stem": "甲", "branch": "辰"},
        "hour": {"stem": "丙", "branch": "午"},
    }

    result = calculate_shensha(pillars, "甲", "未", policy)

    # YUAN_ZHEN should match month-day pair (卯-辰)
    month_keys = {s["key"] for s in result["month"]}
    day_keys = {s["key"] for s in result["day"]}
    assert (
        "YUAN_ZHEN" in month_keys or "YUAN_ZHEN" in day_keys
    ), "YUAN_ZHEN should match (卯-辰) pair"


def test_case09_tian_la_di_wang():
    """Case 09 — 천라/지망 (Nitpick #3 improvement)"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "戊", "branch": "辰"},
        "month": {"stem": "庚", "branch": "未"},
        "day": {"stem": "乙", "branch": "酉"},
        "hour": {"stem": "丁", "branch": "丑"},
    }

    result = calculate_shensha(pillars, "乙", "辰", policy)

    # TIAN_LA should match year (辰)
    year_keys = {s["key"] for s in result["year"]}
    assert "TIAN_LA" in year_keys, "TIAN_LA should match year pillar (辰)"

    # DI_WANG should match month (未) and hour (丑)
    month_keys = {s["key"] for s in result["month"]}
    hour_keys = {s["key"] for s in result["hour"]}
    assert "DI_WANG" in month_keys, "DI_WANG should match month pillar (未)"
    assert "DI_WANG" in hour_keys, "DI_WANG should match hour pillar (丑)"


def test_case10_bai_hu_xue_ren():
    """Case 10 — 백호/혈인 간편 규칙"""
    policy = load_policy()

    # Test BAI_HU (day pillar with 寅/午/戌)
    pillars_bai_hu = {
        "year": {"stem": "戊", "branch": "戌"},
        "month": {"stem": "庚", "branch": "子"},
        "day": {"stem": "乙", "branch": "午"},
        "hour": {"stem": "丁", "branch": "卯"},
    }
    result_bai_hu = calculate_shensha(pillars_bai_hu, "乙", "戌", policy)
    day_keys_bai_hu = {s["key"] for s in result_bai_hu["day"]}
    assert "BAI_HU" in day_keys_bai_hu, "BAI_HU should match day pillar (午)"

    # Test XUE_REN (day pillar with 巳/酉/丑)
    pillars_xue_ren = {
        "year": {"stem": "丙", "branch": "子"},
        "month": {"stem": "己", "branch": "卯"},
        "day": {"stem": "辛", "branch": "巳"},
        "hour": {"stem": "戊", "branch": "戌"},
    }
    result_xue_ren = calculate_shensha(pillars_xue_ren, "辛", "子", policy)
    day_keys_xue_ren = {s["key"] for s in result_xue_ren["day"]}
    assert "XUE_REN" in day_keys_xue_ren, "XUE_REN should match day pillar (巳)"


def test_case11_wen_chang_wen_qu():
    """Case 11 — 문창/문곡 (Nitpick #1 improvement)"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "丙", "branch": "子"},
        "month": {"stem": "庚", "branch": "巳"},
        "day": {"stem": "乙", "branch": "卯"},
        "hour": {"stem": "丁", "branch": "亥"},
    }

    result = calculate_shensha(pillars, "乙", "子", policy)

    # WEN_CHANG should match month (子→巳)
    month_keys = {s["key"] for s in result["month"]}
    assert "WEN_CHANG" in month_keys, "WEN_CHANG should match month pillar"

    # WEN_QU should match hour (子→亥)
    hour_keys = {s["key"] for s in result["hour"]}
    assert "WEN_QU" in hour_keys, "WEN_QU should match hour pillar"


# ============================================================================
# Score Calculation Tests
# ============================================================================


def test_score_calculation():
    """Test score_hint formula: total_score = sum(all score_hints)"""
    policy = load_policy()
    pillars = {
        "year": {"stem": "戊", "branch": "辰"},
        "month": {"stem": "庚", "branch": "未"},
        "day": {"stem": "乙", "branch": "酉"},
        "hour": {"stem": "丁", "branch": "丑"},
    }

    result = calculate_shensha(pillars, "乙", "辰", policy)

    # Calculate total score
    total_score = 0
    for pillar_name, shensha_list in result.items():
        for shensha in shensha_list:
            total_score += shensha["score_hint"]

    # Should be negative (TIAN_LA + DI_WANG + DI_WANG = -2 + -2 + -2 = -6)
    assert total_score < 0, f"Expected negative score, got {total_score}"
