# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, Optional

from .climate import ClimateEvaluator

# Stage-3 wrapper (policy-driven, provided here)
from .engine import AnalysisEngine
from .korean_enricher import KoreanLabelEnricher
from .luck import LuckCalculator
from .recommendation import RecommendationGuard
from .relations import RelationTransformer
from .school import SchoolProfileManager

# Real core engines (must exist in your codebase)
from .strength import StrengthEvaluator
from .yongshin_selector import YongshinSelector

# Utilities
SEASON_BY_BRANCH = {
    "寅": "봄",
    "卯": "봄",
    "辰": "장하",
    "巳": "여름",
    "午": "여름",
    "未": "장하",
    "申": "가을",
    "酉": "가을",
    "戌": "장하",
    "亥": "겨울",
    "子": "겨울",
    "丑": "장하",
}


def _pillar_split(p: str):
    return (p[0], p[1]) if p and len(p) >= 2 else (None, None)


class MasterOrchestrator:
    """Master orchestrator that wires REAL core engines → Stage‑3 engines.
    No shim computation is performed. Only light-format adaptation is applied if needed.
    """

    def __init__(
        self,
        strength_engine: Optional[StrengthEvaluator] = None,
        relations_engine: Optional[RelationTransformer] = None,
        climate_engine: Optional[ClimateEvaluator] = None,
        yongshin_engine: Optional[YongshinSelector] = None,
        luck_engine: Optional[LuckCalculator] = None,
        korean_enricher: Optional[KoreanLabelEnricher] = None,
        school_manager: Optional[SchoolProfileManager] = None,
        recommendation_guard: Optional[RecommendationGuard] = None,
        stage3_engine: Optional[AnalysisEngine] = None,
    ):
        self.strength = strength_engine or StrengthEvaluator.from_files()
        self.relations = relations_engine or RelationTransformer.from_file()
        self.climate = climate_engine or ClimateEvaluator.from_file()
        self.yongshin = yongshin_engine or YongshinSelector()
        self.luck = luck_engine or LuckCalculator()
        self.korean = korean_enricher or KoreanLabelEnricher.from_files()
        self.school = school_manager or SchoolProfileManager.load()
        self.reco = recommendation_guard or RecommendationGuard.from_file()
        self.stage3 = stage3_engine or AnalysisEngine()
        self.version = "master_orchestrator_v1.1_real"

    # --- helpers -------------------------------------------------------------
    def _extract_season(self, month_pillar: str) -> str:
        _, br = _pillar_split(month_pillar)
        return SEASON_BY_BRANCH.get(br, "unknown")

    def _call_strength(self, pillars: Dict[str, str], season: str) -> Dict[str, Any]:
        # Try common call signatures
        for func in [
            getattr(self.strength, "evaluate", None),
            getattr(self.strength, "run", None),
            getattr(self.strength, "__call__", None),
        ]:
            if callable(func):
                out = (
                    func(pillars=pillars, season=season)
                    if func.__code__.co_argcount >= 2
                    else func(pillars)
                )
                return (
                    out
                    if isinstance(out, dict)
                    and "phase" in (out.get("strength", out)).get("phase", "")
                    or "phase" in out
                    else out
                )
        raise RuntimeError("StrengthEvaluator has no callable entrypoint")

    def _call_relations(self, pillars: Dict[str, str]) -> Dict[str, Any]:
        for func in [
            getattr(self.relations, "evaluate", None),
            getattr(self.relations, "run", None),
            getattr(self.relations, "__call__", None),
        ]:
            if callable(func):
                out = func(pillars=pillars) if func.__code__.co_argcount >= 1 else func(pillars)
                return out
        raise RuntimeError("RelationTransformer has no callable entrypoint")

    def _call_climate(
        self, pillars: Dict[str, str], season: str, strength: Dict[str, Any]
    ) -> Dict[str, Any]:
        # climate may need season & strength; pass both, fallback progressively
        for func in [
            getattr(self.climate, "evaluate", None),
            getattr(self.climate, "run", None),
            getattr(self.climate, "__call__", None),
        ]:
            if callable(func):
                try:
                    return func(pillars=pillars, season=season, strength=strength)
                except TypeError:
                    try:
                        return func(pillars=pillars, season=season)
                    except TypeError:
                        return func({"pillars": pillars, "season": season, "strength": strength})
        raise RuntimeError("ClimateEvaluator has no callable entrypoint")

    def _call_luck(self, pillars: Dict[str, str], birth_ctx: Dict[str, Any]) -> Dict[str, Any]:
        for name in ["compute", "compute_start_age", "run", "__call__"]:
            func = getattr(self.luck, name, None)
            if callable(func):
                try:
                    return func(
                        pillars=pillars,
                        birth_dt=birth_ctx.get("birth_dt"),
                        gender=birth_ctx.get("gender"),
                    )
                except TypeError:
                    return func(pillars, birth_ctx)
        raise RuntimeError("LuckCalculator has no callable entrypoint")

    def _call_yongshin(
        self,
        day_master: str,
        strength: Dict[str, Any],
        relations: Dict[str, Any],
        climate: Dict[str, Any],
    ) -> Dict[str, Any]:
        for func in [
            getattr(self.yongshin, "select", None),
            getattr(self.yongshin, "run", None),
            getattr(self.yongshin, "__call__", None),
        ]:
            if callable(func):
                try:
                    return func(
                        day_master=day_master,
                        strength=strength,
                        relations=relations,
                        climate=climate,
                    )
                except TypeError:
                    return func(
                        {
                            "day_master": day_master,
                            "strength": strength,
                            "relations": relations,
                            "climate": climate,
                        }
                    )
        raise RuntimeError("YongshinSelector has no callable entrypoint")

    # --- main ---------------------------------------------------------------
    def analyze(self, pillars: Dict[str, str], birth_context: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        season = self._extract_season(pillars["month"])
        day_stem, _ = _pillar_split(pillars["day"])

        # Core engines (REAL)
        strength = self._call_strength(pillars, season)
        relations = self._call_relations(pillars)
        climate = self._call_climate(pillars, season, strength)
        luck = self._call_luck(pillars, birth_context)
        yongshin = self._call_yongshin(day_stem, strength, relations, climate)

        # Normalize minimal keys used by Stage‑3 context
        strength_ctx = strength.get("strength", strength)
        elements = (
            strength_ctx.get("elements")
            or strength.get("elements")
            or strength.get("strength_elements")
            or {}
        )
        phase = strength_ctx.get("phase") or strength.get("phase")

        relation_flags = relations.get("relation_flags") or relations.get("flags") or []
        climate_flags = climate.get("flags") or []
        balance_index = climate.get("balance_index", 0)
        ys_primary = (yongshin.get("yongshin") or yongshin).get("primary")

        stage3_ctx = {
            "season": season,
            "strength": {"phase": phase, "elements": elements},
            "relation": {"flags": relation_flags},
            "climate": {"flags": climate_flags, "balance_index": balance_index},
            "yongshin": {"primary": ys_primary},
        }
        s3 = self.stage3.analyze(stage3_ctx)

        # Post processing
        enriched = self.korean.enrich(
            {
                "pillars": pillars,
                "season": season,
                "core": {
                    "strength": strength,
                    "relations": relations,
                    "climate": climate,
                    "yongshin": yongshin,
                    "luck": luck,
                },
                "stage3": s3,
            }
        )
        school_profile = self.school.get_default()
        recos = self.reco.filter(enriched, yongshin=yongshin, structure=None)

        out = {
            "meta": {
                "orchestrator_version": self.version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "pillars": pillars,
            "birth_context": birth_context,
            "season": season,
            "day_master": day_stem,
            "core": {
                "strength": strength,
                "relations": relations,
                "climate": climate,
                "yongshin": yongshin,
                "luck": luck,
            },
            "stage3": s3,
            "korean_labels": enriched.get("korean_labels") or enriched,
            "school_profile": school_profile,
            "recommendations": recos,
            "status": "success",
            "errors": errors,
            "warnings": warnings,
        }
        return out
