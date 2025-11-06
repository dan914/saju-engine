
"""Annual luck calculator with v1.1.2 scoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple, TypedDict

from ..builtins import get_default_time_resolver
from ..file_solar_term_loader import FileSolarTermLoader
from ..interfaces import TimeResolver
from .luck_components import compute_raw_components
from .luck_hierarchy import apply_hierarchy
from .luck_output import build_explain, collect_events, generate_alerts
from .policy_config import LuckPolicyConfig, load_luck_policy
from .utils.categories import apply_geokguk, build_recommendations, compute_categories

DATA_DIR = Path(__file__).resolve().parents[5] / "data"
DEFAULT_POLICY_SUFFIX = "v1_1_2"


class EngineOptionsBase(TypedDict):
    calendar_mode: Literal["solar_terms", "gregorian", "lunar"]
    year_boundary: Literal["ipchun", "lunar_new_year"]
    month_boundary: Literal["jie", "zhongqi"]
    time_mode: Literal["local_standard", "lmt"]
    zi_hour_split: Literal["two_hour", "split"]
    policy_version: str
    policy_suffix: str
    policy_config: LuckPolicyConfig


class EngineOptions(EngineOptionsBase, total=False):
    pass


DEFAULT_ENGINE_OPTIONS: EngineOptions = {
    "calendar_mode": "solar_terms",
    "year_boundary": "ipchun",
    "month_boundary": "jie",
    "time_mode": "local_standard",
    "zi_hour_split": "two_hour",
    "policy_version": "luck_policy_v1.1.2",
    "policy_suffix": DEFAULT_POLICY_SUFFIX,
}


class _ChartContextRequired(TypedDict):
    birth_dt_utc: datetime
    birth_tz: str
    natal_pillars: Dict[str, Mapping[str, str]]
    day_master: str
    strength_index: float
    hidden_stems: Mapping[str, Sequence[str]]
    element_balance: Mapping[str, float]


class ChartContext(_ChartContextRequired, total=False):
    strength_profile: Literal["strong", "neutral", "weak"]
    strength_scalar: float
    frame_seeds: Mapping[str, Mapping[str, object]]


class LuckFrame(TypedDict):
    kind: Literal["decade", "year", "month", "day"]
    pillar: str
    start_dt: str
    end_dt: str
    score: float
    drivers: Sequence[dict]
    tags: Dict[str, object]
    explain: Dict[str, object]


@dataclass
class AnnualLuckCalculator:
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
        years: Iterable[int],
        options: Optional[EngineOptions] = None,
    ) -> List[LuckFrame]:
        frames: List[LuckFrame] = []
        opts = self._merge_options(options)
        tz = chart["birth_tz"]
        profile = chart.get("strength_profile") or _determine_strength_profile(chart)
        policy_cfg = _resolve_policy_config("annual", opts)

        parent_norms: Dict[str, float] = {}
        for year in years:
            start_dt, end_dt = self._resolve_year_window(year, tz, opts)
            seeds = _extract_frame_seed(chart, "year")
            raw_result = compute_raw_components(
                frame_kind="year",
                chart=chart,
                seeds=seeds,
                policy=policy_cfg,
            )
            gate_seed = seeds.get("gates", {}) if isinstance(seeds, dict) else {}
            hierarchy = apply_hierarchy(
                frame_kind="year",
                raw_score=raw_result.components.total(),
                gate_seed=gate_seed,
                policy=policy_cfg,
                parent_norms=parent_norms,
            )
            parent_norms["year"] = hierarchy.normalized

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
                frame_kind="year",
                normalized_score=hierarchy.normalized,
                events=events,
                policy=policy_cfg,
            )
            explain = build_explain(
                raw_result=raw_result,
                hierarchy=hierarchy,
                frame_kind="year",
            )

            drivers = ledger.to_summary()
            tags: Dict[str, object] = {
                "year": year,
                "calendar_mode": opts["calendar_mode"],
                "year_boundary": opts["year_boundary"],
                "month_boundary": opts["month_boundary"],
                "time_mode": opts["time_mode"],
                "strength_profile": profile,
                "policy_version": opts["policy_version"],
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
                    "kind": "year",
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

    def _resolve_year_window(
        self,
        year: int,
        tz: str,
        options: EngineOptions,
    ) -> Tuple[datetime, datetime]:
        calendar_mode = options["calendar_mode"]
        if calendar_mode == "solar_terms":
            start_utc = self._get_term_utc(year, "立春")
            end_utc = self._get_term_utc(year + 1, "立春")
            if not start_utc or not end_utc:
                raise ValueError(f"Solar term data incomplete for year {year}")
            start_local = self.time_resolver.from_utc(start_utc, tz)
            end_local = self.time_resolver.from_utc(end_utc, tz)
            return start_local, end_local

        if calendar_mode == "gregorian":
            start_local = self.time_resolver.from_utc(
                datetime(year, 1, 1, tzinfo=timezone.utc), tz
            )
            end_local = self.time_resolver.from_utc(
                datetime(year + 1, 1, 1, tzinfo=timezone.utc), tz
            )
            return start_local, end_local
        raise NotImplementedError(f"calendar_mode='{calendar_mode}' not yet supported")

    def _get_term_utc(self, year: int, target_term: str) -> Optional[datetime]:
        for entry in self.solar_terms.load_year(year):
            if entry.term == target_term:
                return entry.utc_time
        return None


def _extract_frame_seed(chart: Mapping[str, object], frame_key: str) -> Mapping[str, object]:
    seeds = chart.get("frame_seeds")
    if isinstance(seeds, Mapping):
        frame = seeds.get(frame_key, {})
        if isinstance(frame, Mapping):
            return frame
    return {}


@lru_cache(maxsize=16)
def _load_policy(kind: str, suffix: str) -> LuckPolicyConfig:
    return load_luck_policy(f"luck_{kind}_policy_{suffix}.json")


def _resolve_policy_config(kind: str, options: EngineOptions) -> LuckPolicyConfig:
    if "policy_config" in options and isinstance(options["policy_config"], LuckPolicyConfig):
        return options["policy_config"]
    suffix = options.get("policy_suffix", DEFAULT_POLICY_SUFFIX)
    return _load_policy(kind, suffix)


def _determine_strength_profile(chart: Mapping[str, object]) -> str:
    scalar = chart.get("strength_scalar")
    if scalar is None:
        scalar = chart.get("strength_index")
    try:
        value = float(scalar)
    except (TypeError, ValueError):
        value = 0.0
    if value <= -0.35:
        return "weak"
    if value >= 0.35:
        return "strong"
    return "neutral"

