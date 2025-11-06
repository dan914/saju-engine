from .engine import AnalysisEngine
from .llm_guard import LLMGuard

from .helpers import build_sample_request


def test_llm_guard_roundtrip() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = build_sample_request()
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    result = guard.postprocess(
        response,
        payload,
        structure_primary=response.structure.primary if response.structure else None,
        topic_tags=["건강"],
    )
    trace_reco = result.trace["recommendation"]
    assert isinstance(trace_reco["enabled"], bool)
    assert result.recommendation.enabled is trace_reco["enabled"]


def test_llm_guard_detects_trace_mutation() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = build_sample_request()
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    payload["trace"]["rule_id"] = "mutated"
    try:
        guard.postprocess(
            response,
            payload,
            structure_primary=response.structure.primary if response.structure else None,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError when trace mutated")
