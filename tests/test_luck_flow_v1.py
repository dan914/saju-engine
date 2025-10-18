# -*- coding: utf-8 -*-
"""
정책 기반 모의 평가(mock)로 trend만 검증합니다.
실제 엔진 구현없이 policy/examples를 활용합니다.
"""
import json
from pathlib import Path

POLICY = json.loads(Path("policy/luck_flow_policy_v1.json").read_text(encoding="utf-8"))

WEIGHTS = POLICY["scoring"]["weights"]
CLAMP_MIN, CLAMP_MAX = POLICY["scoring"]["clamp_range"]
THRESH = POLICY["scoring"]["trend_thresholds"]
SIGNALS = POLICY["signals"]

def _primary(ctx):
    return ctx["yongshin"]["primary"]

def _elem_level(ctx, elem_name):
    return ctx["strength"]["elements"][elem_name]

def _check_when(when, ctx):
    # yongshin.primary_in
    if "yongshin.primary_in" in when:
        if _primary(ctx) not in when["yongshin.primary_in"]:
            return False
    # climate indices
    bi = ctx.get("climate", {}).get("balance_index", 0)
    if "climate.balance_index_gte" in when:
        if not (bi >= when["climate.balance_index_gte"]):
            return False
    if "climate.balance_index_lte" in when:
        if not (bi <= when["climate.balance_index_lte"]):
            return False
    # strength.elements_any
    if "strength.elements_any" in when:
        ok_any = False
        for token in when["strength.elements_any"]:
            level, elem = token.split(":")
            if elem == "primary":
                elem = _primary(ctx)
            if _elem_level(ctx, _map_korean_to_elem(elem, ctx)) == level:
                ok_any = True
                break
        if not ok_any:
            return False
    # relation.flags_any
    if "relation.flags_any" in when:
        flags = set(ctx.get("relation", {}).get("flags", []))
        if not flags.intersection(set(when["relation.flags_any"])):
            return False
    # boolean flags
    def _b(path, default=False):
        root, key = path.split(".", 1)
        return ctx.get(root, {}).get(key, default)
    for bkey in [
        "daewoon.turning_to_support_primary",
        "daewoon.turning_to_counter_primary",
        "sewoon.supports_primary",
        "sewoon.counters_primary",
    ]:
        if bkey in when:
            if bool(_b(bkey)) is not bool(when[bkey]):
                return False
    return True

def _map_korean_to_elem(elem, ctx):
    # input may be "목/화/토/금/수" or "wood/fire/earth/metal/water"
    mapping = {
        "목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water",
        "wood": "wood", "fire": "fire", "earth": "earth", "metal": "metal", "water": "water"
    }
    return mapping.get(elem, elem)

def evaluate_policy(policy, ctx):
    delta_raw = 0.0
    drivers = []
    detractors = []
    for sig_name, sig in SIGNALS.items():
        if _check_when(sig["when"], ctx):
            weight_key = sig["eval"]
            w = WEIGHTS[weight_key]
            delta_raw += w
            (drivers if w > 0 else detractors).append(sig_name)
    delta = max(CLAMP_MIN, min(CLAMP_MAX, delta_raw))
    if delta >= THRESH["rising"]:
        trend = "rising"
    elif delta <= THRESH["declining"]:
        trend = "declining"
    else:
        trend = "stable"
    score = abs(delta)  # 0..1
    # naive confidence: number of signals triggered scaled
    conf = min(1.0, (len(drivers) + len(detractors)) / 4.0)
    return {
        "trend": trend,
        "score": score,
        "confidence": conf,
        "delta_raw": delta_raw,
        "delta": delta,
        "drivers": drivers,
        "detractors": detractors
    }

def _get_example(ex_id):
    for ex in POLICY["examples"]:
        if ex["id"] == ex_id:
            return ex
    raise KeyError(f"example not found: {ex_id}")

def test_rising_example_from_policy_examples():
    ex = _get_example("EX_RISING_FIRE")
    out = evaluate_policy(POLICY, ex)
    assert out["trend"] == ex["expect_trend"]

def test_stable_example_from_policy_examples():
    ex = _get_example("EX_STABLE_TRANSITION")
    out = evaluate_policy(POLICY, ex)
    assert out["trend"] == ex["expect_trend"]

def test_declining_example_from_policy_examples():
    ex = _get_example("EX_DECLINING_EARTH")
    out = evaluate_policy(POLICY, ex)
    assert out["trend"] == ex["expect_trend"]

def test_threshold_boundary_clamping():
    ex = _get_example("EX_CLAMP_RISING_PEAK")
    out = evaluate_policy(POLICY, ex)
    assert out["trend"] == "rising"
    assert out["delta_raw"] > POLICY["scoring"]["clamp_range"][1]
    assert 0.0 <= out["score"] <= 1.0
