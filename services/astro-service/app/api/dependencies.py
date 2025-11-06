"""Singleton-backed dependencies for astro-service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ..core import SolarTermLoader, SolarTermService

DATA_ROOT = Path(__file__).resolve().parents[4] / "data"
SAMPLE_ROOT = DATA_ROOT / "sample"
DEFAULT_TABLE_PATH = SAMPLE_ROOT if SAMPLE_ROOT.exists() else DATA_ROOT


@lru_cache(maxsize=1)
def _solar_term_loader() -> SolarTermLoader:
    """Return the shared loader configured for the canonical dataset."""
    return SolarTermLoader(table_path=DEFAULT_TABLE_PATH)


@lru_cache(maxsize=1)
def _solar_term_service() -> SolarTermService:
    """Return the shared service using the cached loader."""
    return SolarTermService(loader=_solar_term_loader())


def get_solar_term_loader() -> SolarTermLoader:
    """Expose the cached loader as a FastAPI dependency."""
    return _solar_term_loader()


def get_solar_term_service() -> SolarTermService:
    """Expose the cached service as a FastAPI dependency."""
    return _solar_term_service()


def preload_dependencies() -> None:
    """Warm the loader/service caches at startup."""
    _solar_term_loader()
    _solar_term_service()
