"""Tests for dependency injection container."""

import pytest

from saju_common.container import Container, get_default_container, reset_default_container


class FakeEngine:
    """Fake engine for testing."""

    def __init__(self, config: str = "default"):
        self.config = config
        self.call_count = 0

    def process(self) -> str:
        self.call_count += 1
        return f"processed-{self.call_count}"


class FakeService:
    """Fake service for testing."""

    def __init__(self, engine: FakeEngine):
        self.engine = engine


def test_container_singleton_decorator():
    """Test singleton registration via decorator."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine()

    # Should return same instance
    engine1 = container.get("get_engine")
    engine2 = container.get("get_engine")

    assert engine1 is engine2
    assert isinstance(engine1, FakeEngine)


def test_container_factory_decorator():
    """Test factory registration via decorator."""
    container = Container()

    @container.factory
    def get_engine():
        return FakeEngine()

    # Should return different instances
    engine1 = container.get("get_engine")
    engine2 = container.get("get_engine")

    assert engine1 is not engine2
    assert isinstance(engine1, FakeEngine)
    assert isinstance(engine2, FakeEngine)


def test_container_manual_registration():
    """Test manual dependency registration."""
    container = Container()

    container.register("engine", lambda: FakeEngine("custom"), scope="singleton")
    container.register("service", lambda: FakeService(container.get("engine")), scope="factory")

    engine = container.get("engine")
    service1 = container.get("service")
    service2 = container.get("service")

    assert engine.config == "custom"
    assert service1.engine is engine
    assert service2.engine is engine
    assert service1 is not service2  # Factory scope


def test_container_provider():
    """Test provider function for FastAPI Depends."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine()

    provider = container.provider("get_engine")
    engine1 = provider()
    engine2 = provider()

    assert engine1 is engine2
    assert callable(provider)
    assert provider.__name__ == "provide_get_engine"


def test_container_override():
    """Test dependency override for testing."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine("prod")

    # Normal resolution
    prod_engine = container.get("get_engine")
    assert prod_engine.config == "prod"

    # Override for testing
    mock_engine = FakeEngine("mock")
    with container.override("get_engine", mock_engine):
        test_engine = container.get("get_engine")
        assert test_engine is mock_engine
        assert test_engine.config == "mock"

    # Back to normal after context
    normal_engine = container.get("get_engine")
    assert normal_engine is prod_engine


def test_container_reset():
    """Test container reset clears singleton instances."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine()

    engine1 = container.get("get_engine")
    engine1.call_count = 5

    container.reset()

    engine2 = container.get("get_engine")
    assert engine2 is not engine1
    assert engine2.call_count == 0


def test_container_preload():
    """Test eager instantiation of singletons."""
    container = Container()
    instantiated = []

    @container.singleton
    def get_engine():
        engine = FakeEngine()
        instantiated.append(engine)
        return engine

    # Before preload, no instances
    assert len(instantiated) == 0

    # After preload, singleton instantiated
    container.preload()
    assert len(instantiated) == 1

    # Get should return same instance
    engine = container.get("get_engine")
    assert engine is instantiated[0]
    assert len(instantiated) == 1  # No new instantiation


def test_container_unregistered_dependency():
    """Test error on unregistered dependency."""
    container = Container()

    with pytest.raises(KeyError, match="Dependency 'unknown' not registered"):
        container.get("unknown")


def test_default_container():
    """Test global default container."""
    container1 = get_default_container()
    container2 = get_default_container()

    assert container1 is container2

    # Register and retrieve
    container1.register("test", lambda: "value", scope="singleton")
    assert container2.get("test") == "value"


def test_reset_default_container():
    """Test resetting global default container."""
    # Reset first to clear any previous test pollution
    reset_default_container()

    container = get_default_container()
    container.register("reset_test_engine", lambda: FakeEngine(), scope="singleton")

    engine1 = container.get("reset_test_engine")
    engine1.call_count = 10

    reset_default_container()

    # Should get fresh instance after reset
    engine2 = container.get("reset_test_engine")
    assert engine2.call_count == 0


def test_container_nested_dependencies():
    """Test dependencies that depend on other dependencies."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine("nested")

    @container.singleton
    def get_service():
        return FakeService(container.get("get_engine"))

    service = container.get("get_service")
    engine = container.get("get_engine")

    assert service.engine is engine
    assert engine.config == "nested"


def test_container_override_nested():
    """Test override affects nested dependencies."""
    container = Container()

    @container.singleton
    def get_engine():
        return FakeEngine("prod")

    @container.factory
    def get_service():
        # Factory always creates new service with current engine
        return FakeService(container.get("get_engine"))

    # Normal resolution
    service1 = container.get("get_service")
    assert service1.engine.config == "prod"

    # Override engine
    mock_engine = FakeEngine("mock")
    with container.override("get_engine", mock_engine):
        service2 = container.get("get_service")
        assert service2.engine is mock_engine
        assert service2.engine.config == "mock"

    # Back to normal
    service3 = container.get("get_service")
    assert service3.engine.config == "prod"
