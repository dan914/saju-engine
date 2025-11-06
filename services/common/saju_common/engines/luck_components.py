
"""Raw component scoring for luck engine v1.1.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Optional

from .policy_config import LuckPolicyConfig

TenGodExposure = Mapping[str, float]


@dataclass
class RawComponentScores:
    sibsin: float = 0.0
    relations: float = 0.0
    unseong12: float = 0.0
    taese: float = 0.0
    season: float = 0.0

    def total(self) -> float:
        return self.sibsin + self.relations + self.unseong12 + self.taese + self.season

    def as_dict(self) -> Dict[str, float]:
        return {
            "sibsin": self.sibsin,
            "relations": self.relations,
            "unseong12": self.unseong12,
            "taese": self.taese,
            "season": self.season,
        }


@dataclass
class LedgerEntry:
    component: str
    key: str
    delta: float
    metadata: Mapping[str, object] | None = None


class AttributionLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def add(self, component: str, key: str, delta: float, metadata: Optional[Mapping[str, object]] = None) -> None:
        if not delta:
            return
        self._entries.append(LedgerEntry(component=component, key=key, delta=delta, metadata=dict(metadata or {})))

    def extend(self, entries: Iterable[LedgerEntry]) -> None:
        for entry in entries:
            self.add(entry.component, entry.key, entry.delta, entry.metadata)

    def to_summary(self) -> list[dict]:
        return [
            {
                "component": entry.component,
                "key": entry.key,
                "delta": round(entry.delta, 6),
                "metadata": entry.metadata,
            }
            for entry in self._entries
        ]

    def sum_by_component(self, component: str) -> float:
        return sum(entry.delta for entry in self._entries if entry.component == component)

    def breakdown(self, component: str) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for entry in self._entries:
            if entry.component != component:
                continue
            result[entry.key] = result.get(entry.key, 0.0) + entry.delta
        return result


@dataclass
class RawComputationResult:
    components: RawComponentScores
    ledger: AttributionLedger


def compute_raw_components(
    *,
    frame_kind: str,
    chart: Mapping[str, object],
    seeds: Mapping[str, object],
    policy: LuckPolicyConfig,
) -> RawComputationResult:
    ledger = AttributionLedger()
    scores = RawComponentScores()

    strength_scalar = _coerce_strength_scalar(chart.get("strength_scalar"), chart.get("strength_index"))

    sibsin_seed = seeds.get("sibsin", {})
    scores.sibsin = _compute_sibsin_component(sibsin_seed, policy, strength_scalar, ledger)

    relations_seed = seeds.get("relations", [])
    scores.relations += _compute_relations_component(relations_seed, policy, ledger)

    axis_seed = seeds.get("axis_patterns", [])
    scores.relations += _compute_axis_patterns(axis_seed, policy, ledger)

    overlap_seed = seeds.get("pilar_overlap", [])
    scores.relations += _compute_pilar_overlap(overlap_seed, policy, ledger)

    unseong_seed = seeds.get("unseong12", {})
    scores.unseong12 = _compute_unseong_component(unseong_seed, policy, ledger)

    taese_seed = seeds.get("taese", [])
    scores.taese = _compute_taise_component(taese_seed, policy, ledger)

    season_seed = seeds.get("season", {})
    scores.season = _compute_season_component(season_seed, policy, strength_scalar, frame_kind, ledger)

    return RawComputationResult(components=scores, ledger=ledger)


# ---------------------------------------------------------------------------
# Sibsin (Ten Gods)
# ---------------------------------------------------------------------------

def _compute_sibsin_component(
    seed: Mapping[str, object],
    policy: LuckPolicyConfig,
    strength_scalar: float,
    ledger: AttributionLedger,
) -> float:
    if not seed:
        return 0.0

    weights = policy.weights.get("sibsin", {})
    base_weights: Dict[str, float] = weights.get("ten_gods", {})  # type: ignore[assignment]
    multipliers = weights.get("multipliers", {})
    anchors: Dict[str, Dict[str, float]] = multipliers.get("by_strength_anchors", {})  # type: ignore[assignment]
    hidden_mult: Dict[str, float] = multipliers.get("hidden_stem", {})  # type: ignore[assignment]

    raw_exposures: TenGodExposure
    if "ten_gods" in seed:
        raw_exposures = seed.get("ten_gods", {})  # type: ignore[assignment]
    else:
        raw_exposures = seed  # type: ignore[assignment]

    total = 0.0
    for tg, exposure in raw_exposures.items():
        base = float(base_weights.get(tg, 0.0))
        mult = _interpolate_strength_multiplier(tg, strength_scalar, anchors)
        delta = float(exposure) * base * mult
        if delta:
            total += delta
            ledger.add("sibsin", tg, delta, {"exposure": exposure, "base": base, "strength_scalar": strength_scalar})

    hidden = seed.get("hidden", {})  # type: ignore[assignment]
    if isinstance(hidden, Mapping):
        for tier, mapping in hidden.items():
            tier_mult = float(hidden_mult.get(tier, 1.0))
            if not isinstance(mapping, Mapping):
                continue
            for tg, exposure in mapping.items():
                base = float(base_weights.get(tg, 0.0))
                mult = _interpolate_strength_multiplier(tg, strength_scalar, anchors)
                delta = float(exposure) * base * tier_mult * mult
                if delta:
                    total += delta
                    ledger.add(
                        "sibsin",
                        f"hidden:{tier}:{tg}",
                        delta,
                        {"exposure": exposure, "base": base, "tier_multiplier": tier_mult, "strength_scalar": strength_scalar},
                    )

    return total


def _interpolate_strength_multiplier(
    tg: str,
    strength_scalar: float,
    anchors: Mapping[str, Mapping[str, float]],
) -> float:
    neutral = float(anchors.get("neutral", {}).get(tg, 1.0))
    if strength_scalar <= 0.0:
        weak = float(anchors.get("weak_end", {}).get(tg, neutral))
        t = (strength_scalar + 1.0) / 1.0
        return _lerp(weak, neutral, max(0.0, min(1.0, t)))
    strong = float(anchors.get("strong_end", {}).get(tg, neutral))
    t = strength_scalar / 1.0
    return _lerp(neutral, strong, max(0.0, min(1.0, t)))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

def _compute_relations_component(
    seed: Iterable[Mapping[str, object]],
    policy: LuckPolicyConfig,
    ledger: AttributionLedger,
) -> float:
    weights = policy.weights.get("relations", {})
    base_weights: Dict[str, float] = {k: float(v) for k, v in weights.items() if isinstance(v, (int, float))}
    bonus_weights: Dict[str, float] = {k: float(v) for k, v in weights.get("bonuses", {}).items()}

    total = 0.0
    for event in seed or []:
        kind = str(event.get("kind", ""))
        magnitude = float(event.get("magnitude", 1.0))
        base = base_weights.get(kind, 0.0)
        delta = magnitude * base
        if delta:
            total += delta
            ledger.add("relations", kind, delta, {"magnitude": magnitude})
        for bonus_key in event.get("bonus_keys", []):
            bonus = bonus_weights.get(str(bonus_key), 0.0)
            bonus_delta = magnitude * bonus
            if bonus_delta:
                total += bonus_delta
                ledger.add("relations", f"bonus:{bonus_key}", bonus_delta, {"magnitude": magnitude})
    return total


def _compute_axis_patterns(
    seed: Iterable[Mapping[str, object]],
    policy: LuckPolicyConfig,
    ledger: AttributionLedger,
) -> float:
    weights = policy.weights.get("axis_patterns", {})
    total = 0.0
    for event in seed or []:
        pattern = str(event.get("pattern", ""))
        state = str(event.get("state", "complete"))
        mapping = weights.get(pattern, {})
        value = float(mapping.get(state, 0.0))
        if not value:
            continue
        total += value
        metadata = {"state": state}
        if mapping.get("emit_flag"):
            metadata["emit_flag"] = mapping["emit_flag"]
        ledger.add("relations", f"axis:{pattern}:{state}", value, metadata)
    return total


def _compute_pilar_overlap(
    seed: Iterable[Mapping[str, object]],
    policy: LuckPolicyConfig,
    ledger: AttributionLedger,
) -> float:
    weights = policy.weights.get("pilar_overlap", {})
    total = 0.0
    for event in seed or []:
        overlap_type = str(event.get("type", ""))
        if overlap_type == "same":
            delta = float(weights.get("same_pillar_bonus", 0.0))
        elif overlap_type == "reverse":
            delta = float(weights.get("reverse_pillar_penalty", 0.0))
        else:
            delta = 0.0
        if delta:
            total += delta
            metadata = {}
            if weights.get("emit_flag"):
                metadata["emit_flag"] = weights["emit_flag"]
            ledger.add("relations", f"pilar_overlap:{overlap_type}", delta, metadata)
    return total


# ---------------------------------------------------------------------------
# 12 Unseong, Taese, Season
# ---------------------------------------------------------------------------

def _compute_unseong_component(
    seed: Mapping[str, object],
    policy: LuckPolicyConfig,
    ledger: AttributionLedger,
) -> float:
    weights = policy.weights.get("unseong12", {})
    total = 0.0
    for stage, exposure in (seed or {}).items():
        base = float(weights.get(stage, 0.0))
        delta = float(exposure) * base
        if delta:
            total += delta
            ledger.add("unseong12", stage, delta, {"exposure": exposure})
    return total


def _compute_taise_component(
    seed: Iterable[Mapping[str, object]],
    policy: LuckPolicyConfig,
    ledger: AttributionLedger,
) -> float:
    weights = policy.weights.get("taese", {})
    total = 0.0
    for event in seed or []:
        relation_type = str(event.get("relation", ""))
        base = float(weights.get(f"{relation_type}_taese", 0.0))
        magnitude = float(event.get("magnitude", 1.0))
        delta = base * magnitude
        if delta:
            total += delta
            metadata = {"magnitude": magnitude}
            if event.get("synergy"):
                metadata["synergy"] = event["synergy"]
            ledger.add("taese", relation_type, delta, metadata)
    return total


def _compute_season_component(
    seed: Mapping[str, object],
    policy: LuckPolicyConfig,
    strength_scalar: float,
    frame_kind: str,
    ledger: AttributionLedger,
) -> float:
    season_policy = policy.weights.get("season", {})
    by_branch = season_policy.get("by_branch", {})
    by_strength = season_policy.get("by_strength", {})
    apply_levels = season_policy.get("apply_levels", {})
    total = 0.0

    if apply_levels and not apply_levels.get(frame_kind, True):
        return 0.0

    branch = str(seed.get("branch", ""))
    element = str(seed.get("element", ""))
    if branch and element:
        branch_weights = by_branch.get(branch, {})
        base = float(branch_weights.get(element, 0.0))
        strength_mult = _season_strength_multiplier(strength_scalar, by_strength)
        delta = base * strength_mult
        if delta:
            total += delta
            ledger.add("season", f"{branch}:{element}", delta, {"strength_scalar": strength_scalar})
    return total


def _season_strength_multiplier(strength_scalar: float, mapping: Mapping[str, float]) -> float:
    if strength_scalar <= 0.0:
        weak = float(mapping.get("weak", 1.0))
        neutral = float(mapping.get("neutral", weak))
        t = (strength_scalar + 1.0) / 1.0
        return _lerp(weak, neutral, max(0.0, min(1.0, t)))
    strong = float(mapping.get("strong", 1.0))
    neutral = float(mapping.get("neutral", strong))
    t = strength_scalar / 1.0
    return _lerp(neutral, strong, max(0.0, min(1.0, t)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_strength_scalar(value: Optional[object], fallback: Optional[object]) -> float:
    if value is None:
        value = fallback
    try:
        scalar = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(-1.0, min(1.0, scalar))

