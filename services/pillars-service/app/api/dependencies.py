"""Dependency helpers for pillars-service."""

from __future__ import annotations

from functools import lru_cache

from ..core import PillarsEngine


@lru_cache(maxsize=1)
def _pillars_engine_singleton() -> PillarsEngine:
    """Return the shared PillarsEngine instance."""
    return PillarsEngine()


def get_pillars_engine() -> PillarsEngine:
    """FastAPI dependency exposing the cached PillarsEngine."""
    return _pillars_engine_singleton()


def preload_dependencies() -> None:
    """Warm singleton resources before serving traffic."""
    _pillars_engine_singleton()
