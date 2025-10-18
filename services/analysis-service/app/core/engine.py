# -*- coding: utf-8 -*-
"""AnalysisEngine - Bridge between API layer and SajuOrchestrator.

This engine:
1. Receives AnalysisRequest from the API
2. Extracts pillars and birth_context
3. Calls SajuOrchestrator for complete analysis
4. Maps orchestrator output to AnalysisResponse
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from ..models.analysis import (
        AnalysisRequest,
        AnalysisResponse,
        LuckDirectionResult,
        LuckResult,
        RecommendationResult,
        RelationsExtras,
        RelationsResult,
        SchoolProfileResult,
        ShenshaResult,
        StrengthDetails,
        StrengthResult,
        StructureResultModel,
        TenGodsResult,
    )
    from .saju_orchestrator import SajuOrchestrator
except ImportError:
    # Fallback for sys.path-based imports
    from models.analysis import (
        AnalysisRequest,
        AnalysisResponse,
        LuckDirectionResult,
        LuckResult,
        RecommendationResult,
        RelationsExtras,
        RelationsResult,
        SchoolProfileResult,
        ShenshaResult,
        StrengthDetails,
        StrengthResult,
        StructureResultModel,
        TenGodsResult,
    )
    from saju_orchestrator import SajuOrchestrator


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
        response = self._map_to_response(orchestrator_result, pillars)

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
        self, result: Dict[str, Any], pillars: Dict[str, str]
    ) -> AnalysisResponse:
        """Map orchestrator output to AnalysisResponse.

        Args:
            result: Orchestrator output dict
            pillars: Original pillars dict

        Returns:
            AnalysisResponse with all fields populated
        """
        # Extract ten_gods (from pillars stem analysis - generate from pillars if not present)
        ten_gods_data = result.get("ten_gods", {})
        if not ten_gods_data or "summary" not in ten_gods_data:
            # Generate basic ten_gods mapping from pillars
            ten_gods_data = {"summary": self._generate_ten_gods_summary(pillars)}

        # Extract relations
        relations_data = result.get("relations", {})

        # Extract relations_extras
        relations_extras_data = result.get("relations_extras", {})

        # Extract strength
        strength_data = result.get("strength", {})

        # Extract strength_details
        strength_details_data = result.get("strength_details", {})

        # Extract structure
        structure_data = result.get("structure", {})

        # Extract luck
        luck_data = result.get("luck", {})

        # Extract luck_direction
        luck_direction_data = result.get("luck_direction", {})

        # Extract shensha
        shensha_data = result.get("shensha", {})

        # Extract school_profile
        school_profile_data = result.get("school_profile", {})

        # Extract recommendation
        recommendation_data = result.get("recommendation", {})

        # Build trace
        trace = result.get("trace", {})
        if not trace:
            trace = {
                "orchestrator_keys": list(result.keys()),
                "pillars": pillars,
            }

        # Construct AnalysisResponse
        return AnalysisResponse(
            ten_gods=TenGodsResult(
                summary=ten_gods_data.get("summary", {})
            ),
            relations=RelationsResult(
                he6=relations_data.get("he6", []),
                sanhe=relations_data.get("sanhe", []),
                chong=relations_data.get("chong", []),
                hai=relations_data.get("hai", []),
                po=relations_data.get("po", []),
                xing=relations_data.get("xing", []),
            ),
            relation_extras=RelationsExtras(
                priority_hit=relations_extras_data.get("priority_hit"),
                transform_to=relations_extras_data.get("transform_to"),
                boosts=relations_extras_data.get("boosts", []),
                extras=relations_extras_data.get("extras", {}),
            ),
            strength=StrengthResult(
                level=strength_data.get("level", "unknown"),
                basis=strength_data.get("basis", {}),
            ),
            strength_details=StrengthDetails(
                month_state=strength_details_data.get("month_state", 0),
                branch_root=strength_details_data.get("branch_root", 0),
                stem_visible=strength_details_data.get("stem_visible", 0),
                combo_clash=strength_details_data.get("combo_clash", 0),
                season_adjust=strength_details_data.get("season_adjust", 0),
                month_stem_effect=strength_details_data.get("month_stem_effect", 0),
                wealth_location_bonus_total=strength_details_data.get("wealth_location_bonus_total", 0.0),
                wealth_location_hits=strength_details_data.get("wealth_location_hits", []),
                total=strength_details_data.get("total", 0.0),
                grade_code=strength_details_data.get("grade_code", "unknown"),
                grade=strength_details_data.get("grade", "unknown"),
                seal_validity=strength_details_data.get("seal_validity", {}),
            ),
            structure=StructureResultModel(
                primary=structure_data.get("primary"),
                confidence=structure_data.get("confidence", "low"),
                candidates=structure_data.get("candidates", []),
            ),
            luck=LuckResult(
                prev_term=luck_data.get("prev_term"),
                next_term=luck_data.get("next_term"),
                interval_days=luck_data.get("interval_days"),
                days_from_prev=luck_data.get("days_from_prev"),
                start_age=luck_data.get("start_age"),
            ),
            luck_direction=LuckDirectionResult(
                direction=luck_direction_data.get("direction"),
                method=luck_direction_data.get("method"),
                sex_at_birth=luck_direction_data.get("sex_at_birth"),
            ),
            shensha=ShenshaResult(
                enabled=shensha_data.get("enabled", False),
                list=shensha_data.get("list", []),
            ),
            school_profile=SchoolProfileResult(
                id=school_profile_data.get("id", "unknown"),
                notes=school_profile_data.get("notes"),
            ),
            recommendation=RecommendationResult(
                enabled=recommendation_data.get("enabled", False),
                action=recommendation_data.get("action", "none"),
                copy=recommendation_data.get("copy"),
            ),
            trace=trace,
        )

    def _generate_ten_gods_summary(self, pillars: Dict[str, str]) -> Dict[str, str]:
        """Generate a basic ten_gods summary from pillars.

        This is a fallback in case orchestrator doesn't provide ten_gods.
        In production, the orchestrator should always provide this.

        Args:
            pillars: Dict with year/month/day/hour pillars

        Returns:
            Dict mapping pillar positions to placeholder values
        """
        return {
            "year_stem": "placeholder",
            "year_branch": "placeholder",
            "month_stem": "placeholder",
            "month_branch": "placeholder",
            "day_stem": "日主",  # Day stem is always 日主 (self)
            "day_branch": "placeholder",
            "hour_stem": "placeholder",
            "hour_branch": "placeholder",
        }
