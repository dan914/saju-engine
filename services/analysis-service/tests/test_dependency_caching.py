"""Latency-oriented checks for singleton dependency providers."""

from __future__ import annotations

import time

from app.api.dependencies import (
    _analysis_engine_singleton,
    _llm_guard_singleton,
    preload_dependencies,
)


def _measure(callable_):
    start = time.perf_counter()
    value = callable_()
    elapsed = time.perf_counter() - start
    return value, elapsed


def test_analysis_engine_singleton_latency() -> None:
    _analysis_engine_singleton.cache_clear()
    first_engine, first_duration = _measure(_analysis_engine_singleton)
    second_engine, second_duration = _measure(_analysis_engine_singleton)

    assert first_engine is second_engine
    assert second_duration < first_duration
    assert (first_duration - second_duration) >= 0.001

    preload_dependencies()


def test_llm_guard_singleton_latency() -> None:
    _llm_guard_singleton.cache_clear()
    first_guard, first_duration = _measure(_llm_guard_singleton)
    second_guard, second_duration = _measure(_llm_guard_singleton)

    assert first_guard is second_guard
    assert second_duration < first_duration

    preload_dependencies()
