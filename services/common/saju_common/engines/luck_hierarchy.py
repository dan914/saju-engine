
"""Hierarchy gate and normalization helpers for luck engine v1.1.2."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Optional

from .policy_config import LuckPolicyConfig


@dataclass
class HierarchyResult:
    raw: float
    gate_total: float
    gates: Dict[str, float]
    normalized: float
    breakthrough_applied: Optional[str] = None


def apply_hierarchy(
    *,
    frame_kind: str,
    raw_score: float,
    gate_seed: Mapping[str, float],
    policy: LuckPolicyConfig,
    parent_norms: Optional[Mapping[str, float]] = None,
) -> HierarchyResult:
    hierarchy = policy.hierarchy or {}
    gates_cfg = hierarchy.get("gates", {})
    gate_clip = hierarchy.get("gate_clip", [0.6, 1.4])
    min_gate, max_gate = float(gate_clip[0]), float(gate_clip[1])
    compound_floor = float(hierarchy.get("compound_floor_daily", 0.0))
    breakthrough = hierarchy.get("breakthrough", {})

    normalization = policy.normalization or {}
    scale_cfg = normalization.get("scale", {})
    clip_value = float(normalization.get("clip", 95))

    gate_inputs = {
        "daewoon": float(gate_seed.get("daewoon_norm", gate_seed.get("daewoon", 0.0))),
        "year": float(gate_seed.get("year_norm", gate_seed.get("year", 0.0))),
        "month": float(gate_seed.get("month_norm", gate_seed.get("month", 0.0))),
    }

    gates: Dict[str, float] = {}

    def gate_factor(name: str, norm_value: float, coeff_key: str) -> float:
        coeff = float(gates_cfg.get(coeff_key, 0.0))
        gate = 1.0 + coeff * (norm_value / 100.0)
        return max(min_gate, min(max_gate, gate))

    total_gate = 1.0
    breakthrough_applied: Optional[str] = None

    if frame_kind == "year":
        gate = gate_factor("daewoon", gate_inputs["daewoon"], "alpha")
        gates["daewoon"] = gate
        total_gate *= gate
    elif frame_kind == "month":
        gate_d = gate_factor("daewoon", gate_inputs["daewoon"], "alpha")
        gate_y = gate_factor("year", gate_inputs["year"], "beta")
        gates["daewoon"] = gate_d
        gates["year"] = gate_y
        total_gate *= gate_d * gate_y
        if breakthrough:
            threshold = float(breakthrough.get("year_relief_threshold", float("inf")))
            floor_val = float(breakthrough.get("year_relief_floor_month", 0.0))
            if gate_inputs["year"] >= threshold:
                breakthrough_applied = "year_breakthrough"
                if floor_val and total_gate < floor_val:
                    total_gate = floor_val
    elif frame_kind == "day":
        gate_d = gate_factor("daewoon", gate_inputs["daewoon"], "alpha")
        gate_y = gate_factor("year", gate_inputs["year"], "beta")
        gate_m = gate_factor("month", gate_inputs["month"], "gamma")
        gates["daewoon"] = gate_d
        gates["year"] = gate_y
        gates["month"] = gate_m
        total_gate *= gate_d * gate_y * gate_m
        gate_floor = compound_floor if compound_floor else 0.0
        if breakthrough:
            thresh_month = float(breakthrough.get("month_relief_threshold", float("inf")))
            floor_daily = float(breakthrough.get("month_relief_floor_daily", 0.0))
            if gate_inputs["month"] >= thresh_month:
                breakthrough_applied = "month_breakthrough"
                if floor_daily:
                    gate_floor = max(gate_floor, floor_daily)
            thresh_year = float(breakthrough.get("year_relief_threshold", float("inf")))
            floor_month = float(breakthrough.get("year_relief_floor_month", 0.0))
            if gate_inputs["year"] >= thresh_year:
                breakthrough_applied = "year_breakthrough"
                if floor_month:
                    gate_floor = max(gate_floor, floor_month)
        if gate_floor and total_gate < gate_floor:
            total_gate = gate_floor
            breakthrough_applied = breakthrough_applied or "compound_floor"
    else:
        total_gate = 1.0

    scale = float(scale_cfg.get(frame_kind, 1.0))
    if scale <= 0:
        normalized = raw_score * total_gate
    else:
        normalized = 100.0 * math.tanh((raw_score * total_gate) / scale)
    if clip_value:
        normalized = max(-clip_value, min(clip_value, normalized))

    return HierarchyResult(
        raw=raw_score,
        gate_total=total_gate,
        gates=gates,
        normalized=normalized,
        breakthrough_applied=breakthrough_applied,
    )

