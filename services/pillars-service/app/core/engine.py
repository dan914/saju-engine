"""Deterministic engine for four pillars."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from services.common import TraceMetadata

from ..models import (
    PillarComponent,
    PillarResult,
    PillarsComputeRequest,
    PillarsComputeResponse,
    TraceInfo,
)
from .evidence import EvidenceBuilder
from .pillars import PillarsCalculator, default_calculator


@dataclass(slots=True)
class PillarsEngine:
    """KR_classic v1.4 compliant engine (initial implementation)."""

    calculator: PillarsCalculator = field(default_factory=default_calculator)
    evidence_builder: EvidenceBuilder = field(default_factory=EvidenceBuilder.default)

    def compute(self, request: PillarsComputeRequest) -> PillarsComputeResponse:
        result = self.calculator.compute(request.localDateTime, request.timezone)

        trace_dict = TraceMetadata(
            rule_id="KR_classic_v1.4",
            delta_t_seconds=57.4,
            tz={"iana": request.timezone, "event": "none", "tzdbVersion": "2025a"},
            astro={"lambda_deg": 0.0, "delta_t": 57.4},
            boundary_policy="LCRO",
            epsilon_seconds=0.001,
            flags={"edge": False, "tzTransition": False, "deltaT>5s": False},
        ).to_dict()

        month_term = result["month_term"]
        month_branch = result["month"][1]
        evidence = self.evidence_builder.build(
            local_dt=request.localDateTime,
            timezone_name=request.timezone,
            pillars_result={
                "year": result["year"],
                "month": result["month"],
                "day": result["day"],
                "hour": result["hour"],
            },
            month_term=month_term,
            month_branch=month_branch,
        )
        trace_dict["evidence"] = evidence
        trace_payload = TraceInfo.model_validate(trace_dict)

        day_start: datetime = result["day_start"]
        hour_range = result["hour_range"]

        pillars = PillarResult(
            year=PillarComponent(
                pillar=result["year"],
                boundaryUTC=None,
                term=month_term.term,
                lambda_deg=month_term.lambda_deg,
            ),
            month=PillarComponent(
                pillar=result["month"],
                boundaryUTC=month_term.utc_time,
                term=month_term.term,
                lambda_deg=month_term.lambda_deg,
            ),
            day=PillarComponent(
                pillar=result["day"],
                dayStartLocal=day_start,
                policy="zi-start-23",
            ),
            hour=PillarComponent(
                pillar=result["hour"],
                rangeLocal=hour_range,
                rule="五鼠遁",
            ),
        )
        return PillarsComputeResponse(pillars=pillars, trace=trace_payload)
