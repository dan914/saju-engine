
"""Monthly luck calculator with v1.1.2 scoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Mapping, Optional

from ..builtins import get_default_time_resolver
from ..file_solar_term_loader import FileSolarTermLoader
from ..interfaces import TimeResolver
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

DATA_DIR = Path(__file__).resolve().parents[5] / "data"


@dataclass
class MonthlyLuckCalculator:
    solar_terms: FileSolarTermLoader
    time_resolver: TimeResolver

    def __init__(
        self,
        *,
        solar_terms: Optional[FileSolarTermLoader] = None,
        time_resolver: Optional[TimeResolver] = None,
    ) -> None:
        self.solar_terms = solar_terms or FileSolarTermLoader(DATA_DIR)
        self.time_resolver = time_resolver or get_default_time_resolver()

    def compute(
        self,
        chart: ChartContext,
        year: int,
        options: Optional[EngineOptions] = None,
    ) -> List[LuckFrame]:
        opts = self._merge_options(options)
        tz = chart["birth_tz"]
        profile = chart.get("strength_profile") or _determine_strength_profile(chart)
        policy_cfg = _resolve_policy_config("monthly", opts)

        frames: List[LuckFrame] = []
        parent_norms: Dict[str, float] = {}
        for idx, (start_dt, end_dt, term_name) in enumerate(
            self._resolve_month_windows(year, tz, opts)
        ):
            seeds = _extract_frame_seed(chart, "month")
            raw_result = compute_raw_components(
                frame_kind="month",
                chart=chart,
                seeds=seeds,
                policy=policy_cfg,
            )
            gate_seed = seeds.get("gates", {}) if isinstance(seeds, dict) else {}
            hierarchy = apply_hierarchy(
                frame_kind="month",
                raw_score=raw_result.components.total(),
                gate_seed=gate_seed,
                policy=policy_cfg,
                parent_norms=parent_norms,
            )
            parent_norms["month"] = hierarchy.normalized

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
                frame_kind="month",
                normalized_score=hierarchy.normalized,
                events=events,
                policy=policy_cfg,
            )
            explain = build_explain(
                raw_result=raw_result,
                hierarchy=hierarchy,
                frame_kind="month",
            )

            drivers = ledger.to_summary()
            tags: Dict[str, object] = {
                "year": year,
                "month_index": idx + 1,
                "term": term_name,
                "calendar_mode": opts["calendar_mode"],
                "year_boundary": opts["year_boundary"],
                "month_boundary": opts["month_boundary"],
                "time_mode": opts["time_mode"],
                "strength_profile": profile,
                "policy_version": opts["policy_version"],
                "day_candidates": {"good": [], "caution": []},
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
                    "kind": "month",
                    "pillar": "",
                    "start_dt": start_dt.isoformat(),
                    "end_dt": end_dt.isoformat(),
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

    def _resolve_month_windows(
        self,
        year: int,
        tz: str,
        options: EngineOptions,
    ) -> Iterable[tuple[datetime, datetime, str]]:
        calendar_mode = options["calendar_mode"]
        if calendar_mode != "solar_terms":
            raise NotImplementedError(
                f"calendar_mode='{calendar_mode}' not yet supported for monthly luck"
            )

        terms = list(self.solar_terms.load_year(year))
        if not terms:
            raise ValueError(f"Solar term data missing for year {year}")
        next_terms = list(self.solar_terms.load_year(year + 1))
        if not next_terms:
            raise ValueError(f"Solar term data missing for year {year + 1}")

        combined = terms + [next_terms[0]]
        for idx in range(len(terms)):
            start_utc = combined[idx].utc_time
            end_utc = combined[idx + 1].utc_time
            start_local = self.time_resolver.from_utc(start_utc, tz)
            end_local = self.time_resolver.from_utc(end_utc, tz)
            yield start_local, end_local, terms[idx].term

