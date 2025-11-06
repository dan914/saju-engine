"""Dependency injection using Container (Week 4 refactor).

This module replaces the @lru_cache singleton pattern with a proper
dependency injection container for better testability and lifecycle management.

Migration from dependencies.py:
- @lru_cache singletons → Container.singleton
- Direct function calls → Container.get() or Depends(container.provider())
- Test overrides → container.override() context manager
"""

from __future__ import annotations

from saju_common.container import Container

from ..core import AnalysisEngine
from ..core.llm_guard import LLMGuard

# Create service-specific container
container = Container()


@container.singleton
def get_analysis_engine():
    """Create and cache AnalysisEngine instance."""
    return AnalysisEngine()


@container.singleton
def get_llm_guard():
    """Create and cache LLMGuard instance."""
    return LLMGuard.default()


def preload_dependencies() -> None:
    """Warm the container at application startup.

    This ensures all singletons are instantiated during startup
    rather than on first request, avoiding cold-start latency.

    Usage:
        @app.on_event("startup")
        async def startup():
            preload_dependencies()
    """
    container.preload()


# Export for FastAPI Depends usage
provide_analysis_engine = container.provider("get_analysis_engine")
provide_llm_guard = container.provider("get_llm_guard")
