"""API endpoints for timezone conversions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core import TimezoneConverter
from ..models import TimeConversionRequest, TimeConversionResponse
from .dependencies import get_timezone_converter

router = APIRouter(tags=["timezone"])


@router.post(
    "/time/convert",
    status_code=status.HTTP_200_OK,
    response_model=TimeConversionResponse,
)
def convert_time(
    request: TimeConversionRequest,
    converter: TimezoneConverter = Depends(get_timezone_converter),
) -> TimeConversionResponse:
    """Convert instants between timezones with historical awareness."""
    return converter.convert(request)
