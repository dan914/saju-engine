"""Tests for OpenTelemetry tracing module."""

import pytest

from saju_common.tracing import (
    add_span_attribute,
    add_span_event,
    get_tracer,
    record_exception,
    setup_tracing,
    trace_function,
    trace_span,
)


def test_tracing_disabled_by_default():
    """Test that tracing is disabled by default."""
    # Tracing should be disabled without explicit setup
    tracer = get_tracer()
    assert tracer is None


def test_tracing_with_setting_disabled(monkeypatch):
    """Test that tracing respects settings.enable_tracing=False."""
    monkeypatch.setenv("SAJU_ENABLE_TRACING", "false")

    # Reset settings to pick up environment variable
    from saju_common.settings import SajuSettings

    settings = SajuSettings()
    assert settings.enable_tracing is False

    # Setup should return False when disabled
    result = setup_tracing()
    assert result is False

    tracer = get_tracer()
    assert tracer is None


def test_trace_span_graceful_when_disabled():
    """Test that trace_span works gracefully when tracing is disabled."""
    # Should not raise exceptions even when tracing disabled
    with trace_span("test_operation") as span:
        assert span is None
        result = 42

    assert result == 42


def test_trace_function_decorator_when_disabled():
    """Test that trace_function decorator works when tracing is disabled."""

    @trace_function("test_func")
    def my_function(x: int) -> int:
        return x * 2

    # Should work normally even without tracing
    result = my_function(21)
    assert result == 42


def test_trace_function_async_when_disabled():
    """Test that trace_function works with async functions when disabled."""

    @trace_function("async_test")
    async def async_function(x: int) -> int:
        return x * 2

    import asyncio

    result = asyncio.run(async_function(21))
    assert result == 42


def test_add_span_attribute_when_disabled():
    """Test that add_span_attribute doesn't crash when tracing disabled."""
    # Should not raise exceptions
    add_span_attribute("test.key", "test_value")
    add_span_attribute("test.number", 42)


def test_add_span_event_when_disabled():
    """Test that add_span_event doesn't crash when tracing disabled."""
    # Should not raise exceptions
    add_span_event("test_event")
    add_span_event("test_event_with_attrs", {"key": "value"})


def test_record_exception_when_disabled():
    """Test that record_exception doesn't crash when tracing disabled."""
    # Should not raise exceptions
    try:
        raise ValueError("test error")
    except ValueError as e:
        record_exception(e)


def test_trace_function_with_custom_attributes():
    """Test trace_function decorator with custom attribute extraction."""

    def extract_attrs(args, kwargs):
        return {"user_id": kwargs.get("user_id", "unknown")}

    @trace_function("process_user", attributes=extract_attrs)
    def process_user_data(data: str, user_id: str = None) -> str:
        return f"processed: {data}"

    result = process_user_data("test_data", user_id="user123")
    assert result == "processed: test_data"


def test_trace_span_with_attributes():
    """Test trace_span with custom attributes."""
    with trace_span("test_op", attributes={"test_key": "test_value"}):
        result = "operation_completed"

    assert result == "operation_completed"


def test_nested_trace_spans():
    """Test nested trace spans work correctly."""
    with trace_span("outer_span"):
        outer_result = "outer"

        with trace_span("inner_span"):
            inner_result = "inner"

        assert inner_result == "inner"

    assert outer_result == "outer"


def test_trace_function_preserves_function_metadata():
    """Test that trace_function preserves function name and docstring."""

    @trace_function()
    def documented_function(x: int) -> int:
        """This function has documentation."""
        return x + 1

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This function has documentation."


def test_exception_in_traced_function():
    """Test that exceptions propagate correctly in traced functions."""

    @trace_function("failing_func")
    def failing_function():
        raise ValueError("intentional error")

    with pytest.raises(ValueError, match="intentional error"):
        failing_function()


def test_trace_span_with_exception():
    """Test that exceptions in trace_span propagate correctly."""
    with pytest.raises(RuntimeError, match="test error"):
        with trace_span("error_span"):
            raise RuntimeError("test error")


# Integration tests (only run if OpenTelemetry is installed)
def test_setup_tracing_with_missing_otel():
    """Test setup_tracing handles missing OpenTelemetry gracefully."""
    # This test verifies that setup_tracing returns False
    # when OpenTelemetry is not installed (which is expected in CI)
    result = setup_tracing(service_name="test-service")

    # Result depends on whether OpenTelemetry is installed
    # Should either return True (installed) or False (not installed)
    assert isinstance(result, bool)


def test_settings_integration():
    """Test that tracing respects settings module."""
    from saju_common.settings import SajuSettings

    settings = SajuSettings()

    # Default should be False
    assert settings.enable_tracing is False

    # Service name should be optional
    assert settings.service_name is None


def test_settings_service_name_override(monkeypatch):
    """Test that service name can be overridden via environment."""
    monkeypatch.setenv("SAJU_SERVICE_NAME", "custom-service")

    from saju_common.settings import SajuSettings

    settings = SajuSettings()
    assert settings.service_name == "custom-service"


def test_trace_function_with_complex_return_types():
    """Test that trace_function works with various return types."""

    @trace_function()
    def return_dict() -> dict:
        return {"key": "value", "number": 42}

    @trace_function()
    def return_list() -> list:
        return [1, 2, 3]

    @trace_function()
    def return_none() -> None:
        pass

    assert return_dict() == {"key": "value", "number": 42}
    assert return_list() == [1, 2, 3]
    assert return_none() is None
