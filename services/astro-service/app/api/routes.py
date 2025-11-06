"""API endpoints for solar term lookups."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core import SolarTermService
from ..models import TermQuery, TermResponse
from .dependencies import get_solar_term_service

router = APIRouter(tags=["terms"])


@router.post("/terms", response_model=TermResponse, status_code=status.HTTP_200_OK)
def get_terms(
    query: TermQuery,
    service: SolarTermService = Depends(get_solar_term_service),
) -> TermResponse:
    """Return solar terms for the requested year and timezone."""
    return service.get_terms(query)
