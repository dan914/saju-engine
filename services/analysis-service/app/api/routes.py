"""API endpoints for analysis service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core import AnalysisEngine
from ..core.llm_guard import LLMGuard
from ..models import AnalysisRequest, AnalysisResponse
from .dependencies import get_analysis_engine, get_llm_guard

router = APIRouter(tags=["analysis"])


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    response_model=AnalysisResponse,
)
def analyze(
    payload: AnalysisRequest,
    engine: AnalysisEngine = Depends(get_analysis_engine),
    guard: LLMGuard = Depends(get_llm_guard),
) -> AnalysisResponse:
    """Return ten gods / relations / strength analysis."""
    response = engine.analyze(payload)
    llm_payload = guard.prepare_payload(response)
    structure_primary = response.structure.primary if response.structure else None
    final_response = guard.postprocess(
        response,
        llm_payload,
        structure_primary=structure_primary,
        topic_tags=[],
    )
    return final_response
