# -*- coding: utf-8 -*-
"""AnalysisEngine - Bridge between API layer and SajuOrchestrator.

This engine:
1. Receives AnalysisRequest from the API
2. Extracts pillars and birth_context
3. Calls SajuOrchestrator for complete analysis
4. Maps orchestrator output to AnalysisResponse
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    LuckDirectionResult,
    LuckResult,
    LuckV112Result,
    RecommendationResult,
    RelationsExtras,
    RelationsResult,
    RelationsWeightedResult,
    SchoolProfileResult,
    ShenshaResult,
    StrengthDetails,
    StrengthResult,
    StructureResultModel,
    TenGodsResult,
    TwelveStagesResult,
)
from .saju_orchestrator import SajuOrchestrator


class AnalysisEngine:
    """Main analysis engine that orchestrates all Saju analysis components."""

    def __init__(self):
        """Initialize the engine with a SajuOrchestrator instance."""
        self.orchestrator = SajuOrchestrator()

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Run complete Saju analysis.

        Args:
            request: AnalysisRequest with pillars and options

        Returns:
            AnalysisResponse with all analysis results
        """
        # 1. Extract pillars dictionary (60甲子 format)
        pillars = self._extract_pillars(request)

        # 2. Extract birth context from options
        birth_context = self._extract_birth_context(request.options)

        # 3. Call orchestrator for complete analysis
        orchestrator_result = self.orchestrator.analyze(pillars, birth_context)

        # 4. Map orchestrator output to AnalysisResponse
        response = self._map_to_response(orchestrator_result, pillars, request)

        return response

    def _extract_pillars(self, request: AnalysisRequest) -> Dict[str, str]:
        """Extract pillars dictionary from AnalysisRequest.

        Args:
            request: AnalysisRequest with pillars field

        Returns:
            Dict with keys: year, month, day, hour (60甲子 format)
        """
        pillars = {}
        for pos in ["year", "month", "day", "hour"]:
            pillar_input = request.pillars.get(pos)
            if pillar_input:
                pillars[pos] = pillar_input.pillar
        return pillars

    def _extract_birth_context(self, options: Any) -> Dict[str, Any]:
        """Extract birth context from AnalysisOptions.

        Args:
            options: AnalysisOptions with birth_dt, gender, timezone

        Returns:
            Dict with birth_dt, gender, timezone
        """
        return {
            "birth_dt": options.birth_dt,
            "gender": options.gender,
            "timezone": getattr(options, "timezone", "Asia/Seoul"),
        }

    def _map_to_response(
        self,
        result: Dict[str, Any],
        pillars: Dict[str, str],
        request: AnalysisRequest,
    ) -> AnalysisResponse:
        """Map orchestrator output to AnalysisResponse.

        Args:
            result: Orchestrator output dict
            pillars: Original pillars dict

        Returns:
            AnalysisResponse with all fields populated
        """
        ten_gods = TenGodsResult.model_validate(result.get("ten_gods", {}))
        twelve_stages_data = result.get("twelve_stages")
        twelve_stages = (
            TwelveStagesResult.model_validate(twelve_stages_data)
            if isinstance(twelve_stages_data, dict)
            else None
        )

        relations = RelationsResult.model_validate(result.get("relations", {}))
        relations_weighted_data = result.get("relations_weighted")
        relations_weighted = (
            RelationsWeightedResult.model_validate(relations_weighted_data)
            if isinstance(relations_weighted_data, dict)
            else None
        )
        relations_extras = RelationsExtras.model_validate(result.get("relations_extras", {}))

        strength = StrengthResult.model_validate(result.get("strength", {}))
        strength_details = strength.details
        if strength_details is None:
            strength_details_data = result.get("strength", {}).get("details")
            if isinstance(strength_details_data, dict):
                strength_details = StrengthDetails.model_validate(strength_details_data)

        structure = self._resolve_structure(result)
        climate = result.get("climate", {})
        yongshin = result.get("yongshin", {})

        luck = LuckResult.model_validate(result.get("luck", {}))
        luck_v112_data = result.get("luck_v1_1_2")
        luck_v112 = (
            LuckV112Result.model_validate(luck_v112_data)
            if isinstance(luck_v112_data, dict)
            else None
        )
        luck_direction = None
        if luck.direction or luck.method:
            luck_direction = LuckDirectionResult(
                direction=luck.direction,
                method=luck.method,
                sex_at_birth=request.options.gender,
            )

        shensha = ShenshaResult.model_validate(result.get("shensha", {}))
        school_profile = SchoolProfileResult.model_validate(result.get("school_profile", {}))
        recommendation = RecommendationResult.model_validate(result.get("recommendations", {}))

        trace = self._build_trace(result, pillars, request)

        return AnalysisResponse(
            status=result.get("status", "success"),
            season=result.get("season"),
            ten_gods=ten_gods,
            twelve_stages=twelve_stages,
            relations=relations,
            relations_weighted=relations_weighted,
            relations_extras=relations_extras,
            strength=strength,
            strength_details=strength_details,
            structure=structure,
            climate=climate,
            yongshin=yongshin,
            luck=luck,
            luck_v1_1_2=luck_v112,
            luck_direction=luck_direction,
            shensha=shensha,
            void=result.get("void"),
            yuanjin=result.get("yuanjin"),
            stage3=result.get("stage3", {}),
            elements_distribution_raw=result.get("elements_distribution_raw", {}),
            elements_distribution=result.get("elements_distribution", {}),
            elements_distribution_transformed=result.get(
                "elements_distribution_transformed", {}
            ),
            combination_trace=result.get("combination_trace", []),
            evidence=result.get("evidence", {}),
            engine_summaries=result.get("engine_summaries", {}),
            school_profile=school_profile,
            recommendation=recommendation,
            llm_guard=result.get("llm_guard", {}),
            text_guard=result.get("text_guard", {}),
            meta=result.get("meta", {}),
            trace=trace,
            compat_view=result.get("compat_view", {}),
        )

    def _resolve_structure(self, result: Dict[str, Any]) -> StructureResultModel | None:
        stage3 = result.get("stage3")
        if not isinstance(stage3, dict):
            return None

        gyeokguk = stage3.get("gyeokguk")
        if not isinstance(gyeokguk, dict):
            return None

        primary = gyeokguk.get("type") or gyeokguk.get("classification")
        confidence = gyeokguk.get("confidence")

        candidates: List[Dict[str, Any]] = []
        if primary is not None:
            candidate = {
                "id": primary,
                "score": confidence,
                "notes": gyeokguk.get("notes"),
            }
            candidates.append(candidate)

        if primary is None and not candidates:
            return None

        return StructureResultModel(primary=primary, confidence=confidence, candidates=candidates)

    def _build_trace(
        self,
        result: Dict[str, Any],
        pillars: Dict[str, str],
        request: AnalysisRequest,
    ) -> Dict[str, Any]:
        existing = result.get("trace")
        if isinstance(existing, dict):
            trace = dict(existing)
        else:
            trace = {}

        meta = result.get("meta", {})

        trace.setdefault("rule_id", meta.get("rule_id", "KR_classic_v1.4"))
        trace.setdefault("orchestrator_version", meta.get("orchestrator_version"))
        trace["pillars"] = pillars
        trace["options"] = request.options.model_dump()
        trace["orchestrator_keys"] = sorted(result.keys())

        if "timestamp" in meta:
            trace["timestamp"] = meta["timestamp"]
        if "engines_used" in meta:
            trace["engines_used"] = meta["engines_used"]

        return trace
