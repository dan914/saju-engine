"""Shared test helpers for analysis-service."""

from __future__ import annotations

from app.models import AnalysisOptions, AnalysisRequest, PillarInput


def build_sample_request() -> AnalysisRequest:
    """Return a representative AnalysisRequest for integration tests."""

    pillars = {
        "year": PillarInput(pillar="庚辰"),
        "month": PillarInput(pillar="乙酉"),
        "day": PillarInput(pillar="乙亥"),
        "hour": PillarInput(pillar="辛巳"),
    }
    options = AnalysisOptions(
        birth_dt="2000-09-14T10:00:00+09:00",
        gender="F",
        timezone="Asia/Seoul",
    )
    return AnalysisRequest(pillars=pillars, options=options)
