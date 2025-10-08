"""API endpoints for solar term lookups."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, status

from ..core import SolarTermLoader, SolarTermService
from ..models import TermQuery, TermResponse

router = APIRouter(tags=["terms"])


DATA_ROOT = Path(__file__).resolve().parents[4] / "data" / "sample"


def get_loader() -> SolarTermLoader:
    """Return a loader instance bound to the default dataset path."""
    return SolarTermLoader(table_path=DATA_ROOT)


def get_service(loader: SolarTermLoader = Depends(get_loader)) -> SolarTermService:
    """Resolve the domain service with dependency injection."""
    return SolarTermService(loader=loader)


@router.post("/terms", response_model=TermResponse, status_code=status.HTTP_200_OK)
def get_terms(query: TermQuery, service: SolarTermService = Depends(get_service)) -> TermResponse:
    """Return solar terms for the requested year and timezone."""
    return service.get_terms(query)
