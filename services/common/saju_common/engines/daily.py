
"""Daily luck calculator with v1.1.2 scoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional

from .annual import (
    ChartContext,
    DEFAULT_ENGINE_OPTIONS,
    EngineOptions,
    LuckFrame,
    _determine_strength_profile,
    _extract_frame_seed,
    _resolve_policy_config,
)
from .luck_components import compute_raw_components
from .luck_hierarchy import apply_hierarchy
from .luck_output import build_explain, collect_events, generate_alerts
from .utils.categories import apply_geokguk, build_recommendations, compute_categories


@dataclass
class DailyLuckCalculator:
    """Policy-driven daily luck computation."""

    def compute(
        self,
        chart: ChartContext,
        start_date: date,
        end_date: date,
        options: Optional[EngineOptions] = None,
    ) -> List[LuckFrame]:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        opts = self._merge_options(options)
        profile = chart.get("strength_profile") or _determine_strength_profile(chart)
        policy_cfg = _resolve_policy_config("daily", opts)
        seeds = _extract_frame_seed(chart, "day")
        gate_seed = seeds.get("gates", {}) if isinstance(seeds, dict) else {}

        frames: List[LuckFrame] = []
        parent_norms: Dict[str, float] = {}
        for current in self._iter_dates(start_date, end_date):
            raw_result = compute_raw_components(
                frame_kind="day",
                chart=chart,
                seeds=seeds,
                policy=policy_cfg,
            )
            hierarchy = apply_hierarchy(
                frame_kind="day",
                raw_score=raw_result.components.total(),
                gate_seed=gate_seed,
                policy=policy_cfg,
                parent_norms=parent_norms,
            )
            parent_norms["day"] = hierarchy.normalized

            ledger = raw_result.ledger
            sib_breakdown = ledger.breakdown("sibsin")
            rel_breakdown = ledger.breakdown("relations")
            rel_breakdown.setdefault("total", raw_result.components.relations)
            unseong_stage = seeds.get("unseong_stage") if isinstance(seeds, dict) else None
            unseong_role_coeff = policy_cfg.weights.get("unseong12_role_coeff", {})
            transform_effects = seeds.get("transform_effects") if isinstance(seeds, dict) else None

            category_scores = compute_categories(
                raw_components=raw_result.components.as_dict(),
                sibsin_breakdown=sib_breakdown,
                relations_breakdown=rel_breakdown,
                unseong_stage=unseong_stage,
                unseong_role_coeff=unseong_role_coeff,
                transform_effects=transform_effects,
                policy=policy_cfg,
            )
            geokguk_result = apply_geokguk(
                category_scores=category_scores.values,
                chart=chart,
                policy=policy_cfg,
            )

            events = collect_events(seeds if isinstance(seeds, dict) else None)
            recommendations = build_recommendations(
                category_scores=category_scores.values,
                events=events,
                policy=policy_cfg,
            )
            alerts = generate_alerts(
                frame_kind="day",
                normalized_score=hierarchy.normalized,
                events=events,
                policy=policy_cfg,
            )
            explain = build_explain(
                raw_result=raw_result,
                hierarchy=hierarchy,
                frame_kind="day",
            )

            drivers = ledger.to_summary()
            tags: Dict[str, object] = {
                "date": current.isoformat(),
                "calendar_mode": opts["calendar_mode"],
                "year_boundary": opts["year_boundary"],
                "month_boundary": opts["month_boundary"],
                "time_mode": opts["time_mode"],
                "strength_profile": profile,
                "policy_version": opts["policy_version"],
                "policy_suffix": opts["policy_suffix"],
                "signals": {"ten_god": None, "interactions": []},
                "raw_total": raw_result.components.total(),
                "gate_total": hierarchy.gate_total,
                "gates": hierarchy.gates,
                "categories": category_scores.values,
                "recommendations": recommendations,
            }
            if category_scores.overlays:
                tags["category_overlays"] = category_scores.overlays
            if geokguk_result.mode:
                tags["geokguk"] = {
                    "mode": geokguk_result.mode,
                    "info": geokguk_result.info,
                    "modifiers": geokguk_result.modifiers,
                }
            if alerts:
                tags["alerts"] = alerts
            if events:
                tags["events"] = events
            if hierarchy.breakthrough_applied:
                tags["breakthrough"] = hierarchy.breakthrough_applied

            frames.append(
                {
                    "kind": "day",
                    "pillar": "",
                    "start_dt": datetime.combine(current, datetime.min.time()).isoformat(),
                    "end_dt": datetime.combine(current + timedelta(days=1), datetime.min.time()).isoformat(),
                    "score": hierarchy.normalized,
                    "drivers": drivers,
                    "tags": tags,
                    "explain": explain,
                }
            )
        return frames

    def _merge_options(self, overrides: Optional[EngineOptions]) -> EngineOptions:
        merged: EngineOptions = DEFAULT_ENGINE_OPTIONS.copy()
        if overrides:
            merged.update(overrides)
        return merged

    @staticmethod
    def _iter_dates(start: date, end: date) -> Iterable[date]:
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)

