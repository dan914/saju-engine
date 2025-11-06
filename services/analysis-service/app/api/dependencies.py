"""Dependency helpers with singleton-backed providers."""

from __future__ import annotations

from functools import lru_cache

from ..core import AnalysisEngine
from ..core.llm_guard import LLMGuard


@lru_cache(maxsize=1)
def _analysis_engine_singleton() -> AnalysisEngine:
    """Return the shared AnalysisEngine instance."""
    return AnalysisEngine()


@lru_cache(maxsize=1)
def _llm_guard_singleton() -> LLMGuard:
    """Return the shared LLMGuard wrapper."""
    return LLMGuard.default()


def get_analysis_engine() -> AnalysisEngine:
    """FastAPI dependency that returns the cached AnalysisEngine."""
    return _analysis_engine_singleton()


def get_llm_guard() -> LLMGuard:
    """FastAPI dependency that returns the cached LLMGuard."""
    return _llm_guard_singleton()


def preload_dependencies() -> None:
    """Warm the singletons at application startup."""
    _analysis_engine_singleton()
    _llm_guard_singleton()
