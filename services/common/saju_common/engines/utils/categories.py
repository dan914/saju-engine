
"""Category scoring, geokguk adjustments, and recommendation logic for luck v1.1.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional

from ..policy_config import LuckPolicyConfig


@dataclass
class CategoryScores:
    values: Dict[str, float]
    overlays: Dict[str, dict]


def compute_categories(
    *,
    raw_components: Mapping[str, float],
    sibsin_breakdown: Mapping[str, float],
    relations_breakdown: Mapping[str, float],
    unseong_stage: Optional[str],
    unseong_role_coeff: Mapping[str, Mapping[str, float]],
    transform_effects: Iterable[Mapping[str, object]] | None,
    policy: LuckPolicyConfig,
) -> CategoryScores:
    values: Dict[str, float] = {
        "wealth": 0.0,
        "officer": 0.0,
        "study": 0.0,
        "output": 0.0,
        "network": 0.0,
        "health": 0.0,
        "move": 0.0,
    }

    def sib(name: str) -> float:
        return float(sibsin_breakdown.get(name, 0.0))

    relations_total = float(relations_breakdown.get("total", raw_components.get("relations", 0.0)))
    disrupt = relations_breakdown.get("chung", 0.0) + relations_breakdown.get("hyeong", 0.0)
    harm = relations_breakdown.get("pa", 0.0) + relations_breakdown.get("hae", 0.0)

    values["wealth"] += sib("pyeonjae") + sib("jeongjae") + 0.3 * sib("sik") + 0.2 * relations_total
    values["wealth"] -= 0.5 * relations_breakdown.get("chung", 0.0) + 0.3 * harm

    values["officer"] += sib("pyeongwan") + sib("jeonggwan") + 0.2 * sib("pyeonin") + 0.2 * relations_total
    values["officer"] -= 0.8 * sib("sang") + 0.4 * relations_breakdown.get("chung", 0.0)

    values["study"] += sib("pyeonin") + sib("jeongin") + 0.3 * sib("sik")
    values["study"] -= 0.2 * disrupt

    values["output"] += sib("sik") + 0.8 * sib("sang") + 0.3 * relations_total
    values["output"] -= 0.2 * (relations_breakdown.get("hyeong", 0.0) + relations_breakdown.get("pa", 0.0))

    values["network"] += sib("bi") + 0.8 * sib("jeok") + 0.4 * relations_total
    values["network"] -= 0.3 * harm

    values["health"] -= 0.6 * relations_breakdown.get("chung", 0.0)
    values["health"] -= 0.4 * relations_breakdown.get("hyeong", 0.0)
    values["health"] -= 0.3 * harm

    values["move"] += 0.4 * relations_breakdown.get("chung", 0.0) + 0.2 * relations_total
    values["move"] -= 0.2 * (relations_breakdown.get("hyeong", 0.0) + relations_breakdown.get("pa", 0.0))

    if unseong_stage and unseong_role_coeff:
        coeffs = unseong_role_coeff.get(unseong_stage, {})
        for cat, coeff in coeffs.items():
            if cat in values:
                values[cat] += coeff

    if transform_effects and policy.transformation_role_coeff:
        for effect in transform_effects:
            element = str(effect.get("to"))
            mapping = policy.transformation_role_coeff.get(element)
            if not mapping:
                continue
            scale = float(effect.get("confidence", 1.0))
            for cat, coeff in mapping.items():
                if cat in values:
                    values[cat] += coeff * scale

    overlays: Dict[str, dict] = {}
    overlays_cfg = policy.category_overlays or {}
    officer_overlays = overlays_cfg.get("officer", {})
    guards = officer_overlays.get("guards", [])
    for guard in guards:
        when = guard.get("when", {})
        if _guard_matches(when, sibsin_breakdown, relations_breakdown):
            effect = guard.get("effect", {})
            multiplier = float(effect.get("value", 1.0))
            if effect.get("scope") == "category_only" and "officer" in values:
                values["officer"] *= multiplier
                overlays[guard.get("id", "guard")] = {
                    "category": "officer",
                    "multiplier": multiplier,
                    "metadata": guard,
                }
            spillover = guard.get("spillover", {})
            for cat, mult in spillover.items():
                if cat in values:
                    values[cat] *= float(mult)

    return CategoryScores(values=values, overlays=overlays)


def _guard_matches(
    when: Mapping[str, object],
    sibsin_breakdown: Mapping[str, float],
    relations_breakdown: Mapping[str, float],
) -> bool:
    co_presence = when.get("co_presence")
    if co_presence:
        if not all(sibsin_breakdown.get(tg, 0.0) > 0 for tg in co_presence):
            return False

    dominance = when.get("dominance_ratio")
    if dominance:
        numerator = sum(sibsin_breakdown.get(tg, 0.0) for tg in dominance.get("numerator", []))
        denominator = sum(sibsin_breakdown.get(tg, 0.0) for tg in dominance.get("denominator", []))
        threshold = float(dominance.get("threshold", 1.0))
        if denominator <= 0 or numerator / denominator < threshold:
            return False

    levels = when.get("levels")
    if levels and "daily" not in levels:
        return False

    return True


@dataclass
class GeokgukResult:
    mode: Optional[str]
    info: Mapping[str, object]
    modifiers: Mapping[str, float]


def apply_geokguk(
    *,
    category_scores: Dict[str, float],
    chart: Mapping[str, object],
    policy: LuckPolicyConfig,
) -> GeokgukResult:
    if not policy.geokguk:
        return GeokgukResult(mode=None, info={}, modifiers={})

    detector = policy.geokguk.get("detector", {})
    mode = detector.get("mode")
    if mode != "two_stage":
        return GeokgukResult(mode=None, info={}, modifiers={})

    result = chart.get("geokguk_detect")
    if not isinstance(result, Mapping):
        return GeokgukResult(mode="two_stage", info={}, modifiers={})

    stage = result.get("stage")
    confidence = float(result.get("confidence", 0.0))
    modifiers: Dict[str, float] = {}

    effects = policy.geokguk.get("effects", {})
    if stage == "pseudo":
        multiplier = float(effects.get("pseudo", {}).get("raw_multiplier", 1.0))
        for cat in category_scores:
            category_scores[cat] *= multiplier
            modifiers[cat] = multiplier
    elif stage == "strong":
        strong_cfg = effects.get("strong", {})
        flip_map = strong_cfg.get("flip_map", {})
        follow_type = str(result.get("follow_type", ""))
        if follow_type in flip_map:
            caps = strong_cfg.get("caps", {})
            max_boost = float(caps.get("max_boost", 1.25))
            min_drop = float(caps.get("min_drop", 0.8))
            scale_conf = strong_cfg.get("confidence_scaling", True)
            for cat, base_mult in flip_map[follow_type].items():
                if cat not in category_scores:
                    continue
                mult = float(base_mult)
                if scale_conf:
                    mult = 1.0 + (mult - 1.0) * confidence
                if mult > 1.0:
                    mult = min(mult, max_boost)
                else:
                    mult = max(mult, min_drop)
                category_scores[cat] *= mult
                modifiers[cat] = mult
    return GeokgukResult(mode="two_stage", info=result, modifiers=modifiers)


def build_recommendations(
    *,
    category_scores: Mapping[str, float],
    events: Iterable[str],
    policy: LuckPolicyConfig,
) -> List[str]:
    if not policy.reco:
        return []
    reco_cfg = policy.reco
    base_weights = reco_cfg.get("cat_base_weights", {})
    critical_events = set(reco_cfg.get("critical_events", []))
    event_weights = reco_cfg.get("event_weights", {})
    top_k = int(reco_cfg.get("top_k", 3))

    priorities: Dict[str, float] = {}
    for cat, value in category_scores.items():
        weight = float(base_weights.get(cat, 1.0))
        score = weight * value
        for event in events:
            score += float(event_weights.get(event, 0.0))
            if event in critical_events:
                priorities[cat] = float("inf")
                break
        else:
            priorities[cat] = score

    ranked = sorted(priorities.items(), key=lambda item: item[1], reverse=True)
    return [cat for cat, _ in ranked[:top_k]]


def zscore(value: float, mean: float = 0.0, std: float = 1.0) -> float:
    std = std or 1.0
    return (value - mean) / std

