"""API endpoints for KR_classic v1.4 four pillars computation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core import DayBoundaryPolicy, PillarsEngine
from ..models import PillarsComputeRequest, PillarsComputeResponse

router = APIRouter(tags=["pillars"])


def get_engine() -> PillarsEngine:
    """Provide a pillars engine instance."""
    return PillarsEngine(policy=DayBoundaryPolicy())


@router.post(
    "/pillars/compute",
    response_model=PillarsComputeResponse,
    status_code=status.HTTP_200_OK,
)
def compute_pillars(
    payload: PillarsComputeRequest,
    engine: PillarsEngine = Depends(get_engine),
) -> PillarsComputeResponse:
    """Compute the four pillars for the given birth details."""
    return engine.compute(payload)
