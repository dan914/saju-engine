"""Dependency injection container for 사주 services.

This module provides a simple, testable dependency container to replace
@lru_cache singleton patterns. It supports:
- Singleton scoped dependencies
- Factory scoped dependencies (new instance per call)
- Override mechanisms for testing
- Clear lifecycle management

Example:
    >>> from saju_common.container import Container
    >>>
    >>> # Create container
    >>> container = Container()
    >>>
    >>> # Register singleton
    >>> @container.singleton
    >>> def get_analysis_engine():
    >>>     return AnalysisEngine()
    >>>
    >>> # Use in FastAPI
    >>> @app.get("/analyze")
    >>> def analyze(engine: AnalysisEngine = Depends(container.get("analysis_engine"))):
    >>>     return engine.analyze(...)
    >>>
    >>> # Override for testing
    >>> with container.override("analysis_engine", mock_engine):
    >>>     result = client.get("/analyze")
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Dict, Literal, Optional, TypeVar

T = TypeVar("T")


class Container:
    """Simple dependency injection container.

    Supports two scopes:
    - singleton: One instance for the lifetime of the container
    - factory: New instance on every resolution

    Attributes:
        _singletons: Registry of singleton factory functions
        _factories: Registry of factory functions
        _instances: Cache of singleton instances
        _overrides: Temporary overrides for testing
    """

    def __init__(self) -> None:
        """Initialize empty container."""
        self._singletons: Dict[str, Callable[[], Any]] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._overrides: Dict[str, Any] = {}

    def singleton(self, func: Callable[[], T]) -> Callable[[], T]:
        """Register a singleton factory.

        The factory function will be called once, and the result cached.

        Args:
            func: Factory function with no arguments

        Returns:
            The original function (for use as decorator)

        Example:
            >>> @container.singleton
            >>> def get_engine():
            >>>     return AnalysisEngine()
        """
        name = func.__name__
        self._singletons[name] = func
        return func

    def factory(self, func: Callable[[], T]) -> Callable[[], T]:
        """Register a factory function.

        The factory will be called every time the dependency is resolved.

        Args:
            func: Factory function with no arguments

        Returns:
            The original function (for use as decorator)

        Example:
            >>> @container.factory
            >>> def get_request_id():
            >>>     return str(uuid4())
        """
        name = func.__name__
        self._factories[name] = func
        return func

    def register(
        self,
        name: str,
        factory: Callable[[], T],
        scope: Literal["singleton", "factory"] = "singleton",
    ) -> None:
        """Register a dependency manually.

        Args:
            name: Dependency identifier
            factory: Factory function to create the dependency
            scope: Lifecycle scope (singleton or factory)

        Example:
            >>> container.register(
            >>>     "analysis_engine",
            >>>     lambda: AnalysisEngine(),
            >>>     scope="singleton"
            >>> )
        """
        if scope == "singleton":
            self._singletons[name] = factory
        else:
            self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Resolve a dependency by name.

        Args:
            name: Dependency identifier

        Returns:
            The resolved dependency instance

        Raises:
            KeyError: If dependency not registered

        Example:
            >>> engine = container.get("analysis_engine")
        """
        # Check for override first
        if name in self._overrides:
            return self._overrides[name]

        # Resolve singleton
        if name in self._singletons:
            if name not in self._instances:
                self._instances[name] = self._singletons[name]()
            return self._instances[name]

        # Resolve factory
        if name in self._factories:
            return self._factories[name]()

        raise KeyError(f"Dependency '{name}' not registered")

    def provider(self, name: str) -> Callable[[], Any]:
        """Get a provider function for FastAPI Depends.

        Args:
            name: Dependency identifier

        Returns:
            Provider function suitable for Depends()

        Example:
            >>> @app.get("/analyze")
            >>> def analyze(
            >>>     engine: AnalysisEngine = Depends(container.provider("analysis_engine"))
            >>> ):
            >>>     return engine.analyze(...)
        """
        def _provider() -> Any:
            return self.get(name)

        _provider.__name__ = f"provide_{name}"
        return _provider

    @contextmanager
    def override(self, name: str, instance: Any):
        """Temporarily override a dependency for testing.

        Args:
            name: Dependency identifier
            instance: Override instance

        Yields:
            None

        Example:
            >>> with container.override("analysis_engine", mock_engine):
            >>>     result = client.get("/analyze")  # Uses mock
        """
        self._overrides[name] = instance
        try:
            yield
        finally:
            del self._overrides[name]

    def reset(self) -> None:
        """Clear all singleton instances.

        Useful for testing to ensure clean state between tests.
        Does not clear registrations, only cached instances.

        Example:
            >>> # In test teardown
            >>> container.reset()
        """
        self._instances.clear()
        self._overrides.clear()

    def preload(self) -> None:
        """Eagerly instantiate all singletons.

        Useful for warming caches at application startup to avoid
        lazy loading delays on first request.

        Example:
            >>> @app.on_event("startup")
            >>> async def startup():
            >>>     container.preload()
        """
        for name in self._singletons:
            if name not in self._instances:
                self._instances[name] = self._singletons[name]()


# Global default container for convenience
_default_container: Optional[Container] = None


def get_default_container() -> Container:
    """Get or create the global default container.

    Returns:
        The default container instance

    Example:
        >>> from saju_common.container import get_default_container
        >>> container = get_default_container()
    """
    global _default_container
    if _default_container is None:
        _default_container = Container()
    return _default_container


def reset_default_container() -> None:
    """Reset the global default container.

    Useful for testing to ensure clean state.

    Example:
        >>> # In test teardown
        >>> reset_default_container()
    """
    global _default_container
    if _default_container is not None:
        _default_container.reset()
