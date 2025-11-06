
import math

from services.common.saju_common.engines.luck_components import compute_raw_components
from services.common.saju_common.engines.luck_hierarchy import apply_hierarchy
from services.common.saju_common.engines.policy_config import LuckPolicyConfig
from services.common.saju_common.engines.utils.categories import (
    apply_geokguk,
    build_recommendations,
    compute_categories,
)


def _policy_base() -> LuckPolicyConfig:
    data = {
        "policy_version": "luck_policy_v1.1.2",
        "weights": {
            "sibsin": {
                "ten_gods": {"pyeonjae": 1.0},
                "multipliers": {
                    "hidden_stem": {},
                    "by_strength_anchors": {
                        "weak_end": {"pyeonjae": -0.5},
                        "neutral": {"pyeonjae": 1.0},
                        "strong_end": {"pyeonjae": 2.0},
                    },
                },
            },
            "relations": {
                "hap": 1.0,
                "chung": -2.0,
                "bonuses": {"sam_hap_complete": 3.0},
            },
            "axis_patterns": {"sajeong_chung": {"complete": -5.0}},
            "pilar_overlap": {"same_pillar_bonus": 1.5},
            "unseong12": {"changsheng": 5, "mu": -2},
            "taese": {"hap_taese": 3.0, "chung_taese": -4.0},
            "season": {
                "by_branch": {"yin": {"wood": 3, "earth": 0}},
                "by_strength": {"weak": 1.1, "neutral": 1.0, "strong": 0.9},
                "apply_levels": {"year": True, "month": True, "day": True},
            },
            "unseong12_role_coeff": {
                "changsheng": {"wealth": 0.4},
                "mu": {"health": -0.3},
            },
        },
        "hierarchy": {
            "mode": "multiplicative_gate",
            "gates": {"alpha": 0.4, "beta": 0.3, "gamma": 0.2},
            "gate_clip": [0.6, 1.4],
            "compound_floor_daily": 0.55,
            "breakthrough": {
                "month_relief_threshold": 60,
                "month_relief_floor_daily": 0.75,
                "year_relief_threshold": 60,
                "year_relief_floor_month": 0.70,
            },
        },
        "normalization": {"method": "tanh", "scale": {"year": 10, "month": 10, "day": 10}, "clip": 95},
        "options": {},
        "transformation_role_coeff": {"to_fire": {"output": 0.6}},
        "geokguk": {
            "detector": {"mode": "two_stage"},
            "effects": {
                "pseudo": {"raw_multiplier": 0.9},
                "strong": {
                    "flip_map": {"cong_wealth": {"wealth": 1.2, "resource": 0.8}},
                    "confidence_scaling": True,
                    "caps": {"max_boost": 1.25, "min_drop": 0.8},
                },
            },
        },
        "reco": {
            "cat_base_weights": {"wealth": 1.0, "officer": 1.0},
            "event_weights": {"fan_yin": 2.0},
            "critical_events": ["fan_yin"],
            "top_k": 2,
        },
    }
    return LuckPolicyConfig.from_mapping(data)


def test_strength_multiplier_interpolation():
    policy = _policy_base()
    chart = {"strength_scalar": 1.0}
    seeds = {"sibsin": {"ten_gods": {"pyeonjae": 1.0}}}
    result = compute_raw_components(frame_kind="year", chart=chart, seeds=seeds, policy=policy)
    assert math.isclose(result.components.sibsin, 2.0, rel_tol=1e-6)
    chart["strength_scalar"] = -1.0
    result_weak = compute_raw_components(frame_kind="year", chart=chart, seeds=seeds, policy=policy)
    assert math.isclose(result_weak.components.sibsin, -0.5, rel_tol=1e-6)


def test_apply_hierarchy_with_breakthrough():
    policy = _policy_base()
    gate_seed = {"daewoon_norm": 80}
    result = apply_hierarchy(
        frame_kind="year",
        raw_score=10.0,
        gate_seed=gate_seed,
        policy=policy,
        parent_norms={},
    )
    assert result.gate_total > 1.0
    assert abs(result.normalized) <= 95

    gate_seed = {"daewoon_norm": 10, "year_norm": 70}
    result_month = apply_hierarchy(
        frame_kind="month",
        raw_score=5.0,
        gate_seed=gate_seed,
        policy=policy,
        parent_norms={"year": 65.0},
    )
    assert result_month.gate_total >= 0.70
    assert result_month.breakthrough_applied == "year_breakthrough"


def test_category_scoring_and_geokguk():
    policy = _policy_base()
    raw_components = {"sibsin": 0.0, "relations": -2.0, "unseong12": 0.0, "taese": 0.0, "season": 0.0}
    sib_breakdown = {"pyeonjae": 2.0, "jeongjae": 1.0, "sang": -0.5}
    rel_breakdown = {"chung": -2.0, "total": -2.0}

    categories = compute_categories(
        raw_components=raw_components,
        sibsin_breakdown=sib_breakdown,
        relations_breakdown=rel_breakdown,
        unseong_stage="changsheng",
        unseong_role_coeff=policy.weights.get("unseong12_role_coeff", {}),
        transform_effects=[{"to": "to_fire", "confidence": 0.8}],
        policy=policy,
    )
    assert categories.values["wealth"] > 0

    chart = {"geokguk_detect": {"stage": "strong", "follow_type": "cong_wealth", "confidence": 0.5}}
    result = apply_geokguk(category_scores=categories.values, chart=chart, policy=policy)
    assert result.mode == "two_stage"
    assert "wealth" in result.modifiers


def test_recommendation_with_critical_event():
    policy = _policy_base()
    categories = {"wealth": 10.0, "officer": -5.0}
    recos = build_recommendations(
        category_scores=categories,
        events=["fan_yin"],
        policy=policy,
    )
    assert recos[0] == "wealth"
    assert len(recos) == 2
