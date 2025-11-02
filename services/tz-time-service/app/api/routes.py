"""API endpoints for timezone conversions."""

from __future__ import annotations

import zoneinfo

from fastapi import APIRouter, Depends, status

from ..core import TimeEventDetector, TimezoneConverter
from ..models import TimeConversionRequest, TimeConversionResponse

router = APIRouter(tags=["timezone"])


def get_tzdb_version() -> str:
    """
    Get installed tzdb version from zoneinfo.

    Tries multiple methods:
    1. zoneinfo.TZDATA_VERSION (Python 3.9+ with bundled tzdata)
    2. importlib.metadata for tzdata package
    3. System tzdata version file
    4. Fallback to "system" for system-provided tzdata

    Returns:
        TZDB version string (e.g., "2024b", "system", or "unknown")
    """
    try:
        # Python 3.9+ with bundled tzdata has TZDATA_VERSION attribute
        return zoneinfo.TZDATA_VERSION
    except AttributeError:
        pass

    # Try tzdata package metadata
    try:
        import importlib.metadata

        return importlib.metadata.version("tzdata")
    except (importlib.metadata.PackageNotFoundError, ModuleNotFoundError):
        pass

    # Try system tzdata version file (on some Unix systems)
    try:
        from pathlib import Path

        for tzdata_path in ["/usr/share/zoneinfo", "/usr/share/lib/zoneinfo"]:
            version_file = Path(tzdata_path) / "+VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
    except Exception:
        pass

    # Using system tzdata but can't determine version
    return "system"


def get_event_detector() -> TimeEventDetector:
    """Provide the default event detector instance."""
    return TimeEventDetector()


def get_converter(
    detector: TimeEventDetector = Depends(get_event_detector),
) -> TimezoneConverter:
    """Return the converter bound to the current tzdb metadata."""
    return TimezoneConverter(tzdb_version=get_tzdb_version(), event_detector=detector)


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
