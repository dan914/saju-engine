"""Dependency injection using Container (Week 4 refactor).

Migration from dependencies.py @lru_cache pattern to Container-based DI.
"""

from __future__ import annotations

from pathlib import Path

from saju_common.container import Container

from ..core import SolarTermLoader, SolarTermService

# Data path configuration
DATA_ROOT = Path(__file__).resolve().parents[4] / "data"
SAMPLE_ROOT = DATA_ROOT / "sample"
DEFAULT_TABLE_PATH = SAMPLE_ROOT if SAMPLE_ROOT.exists() else DATA_ROOT

# Create service-specific container
container = Container()


@container.singleton
def get_solar_term_loader():
    """Create and cache SolarTermLoader instance."""
    return SolarTermLoader(table_path=DEFAULT_TABLE_PATH)


@container.singleton
def get_solar_term_service():
    """Create and cache SolarTermService instance."""
    return SolarTermService(loader=container.get("get_solar_term_loader"))


def preload_dependencies() -> None:
    """Warm the container at application startup."""
    container.preload()


# Export for FastAPI Depends usage
provide_solar_term_loader = container.provider("get_solar_term_loader")
provide_solar_term_service = container.provider("get_solar_term_service")
