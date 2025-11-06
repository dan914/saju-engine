"""
Climate Advice MVP Tests

Tests for climate advice mapping policy v1.0
- 8 golden path scenarios (spring/summer/late-summer/autumn/winter)
- 1 fallback scenario (balanced, no match)
- Total: 9 test cases
"""

import json
from pathlib import Path

POLICY = json.loads(Path("policy/climate_advice_policy_v1.json").read_text(encoding="utf-8"))


def match(policy, ctx):
    """
    Match climate advice rule based on context.

    Args:
        policy: Climate advice policy dictionary
        ctx: Context with strength, climate, context fields

    Returns:
        Tuple of (matched_policy_id, advice_text)
    """
    season = ctx["context"]["season"]
    phase = ctx["strength"]["phase"]
    bal = ctx["strength"]["elements"]
    flags = ctx.get("climate", {}).get("flags", [])

    for row in policy["advice_table"]:
        w = row["when"]

        # Check season
        if "season" in w and season not in w["season"]:
            continue

        # Check strength phase
        if "strength_phase" in w and phase not in w["strength_phase"]:
            continue

        # Check balance - all specified keys must match
        if "balance" in w:
            ok = True
            for k, v in w["balance"].items():
                if bal.get(k) != v:
                    ok = False
                    break
            if not ok:
                continue

        # Check imbalance flags - all required flags must be present
        if "imbalance_flags" in w:
            if not all(f in flags for f in w["imbalance_flags"]):
                continue

        # Match found - return first match
        return row["id"], row["advice"]

    # No match - return fallback
    return None, policy["output"]["fallback"]


def test_spring_wood_over_fire_weak():
    """봄 + 왕 + 목high/화low → WOOD_OVER_FIRE_WEAK"""
    ctx = {
        "strength": {
            "phase": "왕",
            "elements": {
                "wood": "high",
                "fire": "low",
                "earth": "normal",
                "metal": "normal",
                "water": "normal",
            },
        },
        "climate": {"flags": []},
        "context": {"season": "봄", "month_branch": "辰"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "WOOD_OVER_FIRE_WEAK"
    assert "불기운" in advice


def test_summer_fire_over_water_weak():
    """여름 + 상 + 화high/수low → FIRE_OVER_WATER_WEAK"""
    ctx = {
        "strength": {
            "phase": "상",
            "elements": {
                "wood": "normal",
                "fire": "high",
                "earth": "normal",
                "metal": "normal",
                "water": "low",
            },
        },
        "climate": {"flags": []},
        "context": {"season": "여름", "month_branch": "午"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "FIRE_OVER_WATER_WEAK"
    assert "수 기운" in advice


def test_summer_earth_excess_dryness():
    """여름 + earth_excess+dryness flags → EARTH_EXCESS_DRYNESS"""
    ctx = {
        "strength": {
            "phase": "휴",
            "elements": {
                "wood": "normal",
                "fire": "normal",
                "earth": "normal",
                "metal": "normal",
                "water": "normal",
            },
        },
        "climate": {"flags": ["earth_excess", "dryness"]},
        "context": {"season": "여름", "month_branch": "未"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "EARTH_EXCESS_DRYNESS"
    assert "건조" in advice


def test_late_summer_earth_excess_humidity():
    """장하 + earth_excess+humidity flags → EARTH_EXCESS_HUMIDITY"""
    ctx = {
        "strength": {
            "phase": "휴",
            "elements": {
                "wood": "normal",
                "fire": "normal",
                "earth": "normal",
                "metal": "normal",
                "water": "normal",
            },
        },
        "climate": {"flags": ["earth_excess", "humidity"]},
        "context": {"season": "장하", "month_branch": "申"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "EARTH_EXCESS_HUMIDITY"
    assert "습담" in advice


def test_autumn_metal_over_wood_weak():
    """가을 + 왕 + 금high/목low → METAL_OVER_WOOD_WEAK"""
    ctx = {
        "strength": {
            "phase": "왕",
            "elements": {
                "wood": "low",
                "fire": "normal",
                "earth": "normal",
                "metal": "high",
                "water": "normal",
            },
        },
        "climate": {"flags": []},
        "context": {"season": "가을", "month_branch": "酉"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "METAL_OVER_WOOD_WEAK"
    assert "목 기운" in advice


def test_autumn_metal_dryness_relief():
    """가을 + 금high + dryness flag → METAL_DRYNESS_RELIEF"""
    ctx = {
        "strength": {
            "phase": "수",
            "elements": {
                "wood": "normal",
                "fire": "normal",
                "earth": "normal",
                "metal": "high",
                "water": "normal",
            },
        },
        "climate": {"flags": ["dryness"]},
        "context": {"season": "가을", "month_branch": "戌"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "METAL_DRYNESS_RELIEF"
    assert "건조" in advice


def test_winter_water_deficit():
    """겨울 + 수low → WATER_DEFICIT_IN_WINTER"""
    ctx = {
        "strength": {
            "phase": "휴",
            "elements": {
                "wood": "normal",
                "fire": "normal",
                "earth": "normal",
                "metal": "normal",
                "water": "low",
            },
        },
        "climate": {"flags": []},
        "context": {"season": "겨울", "month_branch": "子"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "WATER_DEFICIT_IN_WINTER"
    assert advice.startswith("수 보강")


def test_winter_water_over_fire_weak_with_coldness():
    """겨울 + 수high/화low + coldness flag → WATER_OVER_FIRE_WEAK"""
    ctx = {
        "strength": {
            "phase": "사",
            "elements": {
                "wood": "normal",
                "fire": "low",
                "earth": "normal",
                "metal": "normal",
                "water": "high",
            },
        },
        "climate": {"flags": ["coldness"]},
        "context": {"season": "겨울", "month_branch": "丑"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid == "WATER_OVER_FIRE_WEAK"
    assert "온기" in advice or "한기" in advice


def test_balanced_fallback():
    """균형 상태(매칭 없음) → fallback advice"""
    ctx = {
        "strength": {
            "phase": "휴",
            "elements": {
                "wood": "normal",
                "fire": "normal",
                "earth": "normal",
                "metal": "normal",
                "water": "normal",
            },
        },
        "climate": {"flags": []},
        "context": {"season": "봄", "month_branch": "卯"},
    }
    pid, advice = match(POLICY, ctx)
    assert pid is None
    assert "균형" in advice or "무리 없이" in advice
