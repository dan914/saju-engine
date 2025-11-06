"""Singleton-backed dependencies and helpers for tz-time-service."""

from __future__ import annotations

import importlib.metadata
from functools import lru_cache
from pathlib import Path
from typing import Callable

from ..core import TimeEventDetector, TimezoneConverter


@lru_cache(maxsize=1)
def get_tzdb_version() -> str:
    """Detect the tzdb version shipped with the runtime."""
    import zoneinfo

    try:
        return zoneinfo.TZDATA_VERSION
    except AttributeError:
        pass

    try:
        return importlib.metadata.version("tzdata")
    except importlib.metadata.PackageNotFoundError:
        pass

    for base in (Path("/usr/share/zoneinfo"), Path("/usr/share/lib/zoneinfo")):
        version_file = base / "+VERSION"
        if version_file.exists():
            return version_file.read_text().strip() or "system"

    return "system"


@lru_cache(maxsize=1)
def _event_detector_singleton() -> TimeEventDetector:
    """Return the shared event detector instance."""
    return TimeEventDetector()


@lru_cache(maxsize=1)
def _converter_singleton() -> TimezoneConverter:
    """Return the shared timezone converter bound to the detected tzdb version."""
    return TimezoneConverter(
        tzdb_version=get_tzdb_version(),
        event_detector=_event_detector_singleton(),
    )


def get_event_detector() -> TimeEventDetector:
    """FastAPI dependency providing the cached event detector."""
    return _event_detector_singleton()


def get_timezone_converter() -> TimezoneConverter:
    """FastAPI dependency providing the cached converter."""
    return _converter_singleton()


def preload_dependencies() -> None:
    """Warm cached dependencies at application startup."""
    get_tzdb_version()
    _event_detector_singleton()
    _converter_singleton()
