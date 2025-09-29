"""API endpoints for timezone conversions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..core import TimeEventDetector, TimezoneConverter
from ..models import TimeConversionRequest, TimeConversionResponse

router = APIRouter(tags=["timezone"])


def get_event_detector() -> TimeEventDetector:
    """Provide the default event detector instance."""
    return TimeEventDetector()


def get_converter(
    detector: TimeEventDetector = Depends(get_event_detector),
) -> TimezoneConverter:
    """Return the converter bound to the current tzdb metadata."""
    return TimezoneConverter(tzdb_version="2025a", event_detector=detector)


@router.post(
    "/time/convert",
    status_code=status.HTTP_200_OK,
    response_model=TimeConversionResponse,
)
def convert_time(
    request: TimeConversionRequest,
    converter: TimezoneConverter = Depends(get_converter),
) -> TimeConversionResponse:
    """Convert instants between timezones with historical awareness."""
    return converter.convert(request)
