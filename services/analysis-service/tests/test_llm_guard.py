from app.core.engine import AnalysisEngine
from app.core.llm_guard import LLMGuard
from app.models import AnalysisRequest


def test_llm_guard_roundtrip() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = AnalysisRequest(pillars={}, options={})
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    result = guard.postprocess(
        response,
        payload,
        structure_primary=response.structure.primary,
        topic_tags=["건강"],
    )
    assert result.trace["recommendation"]["enabled"] is False
    assert result.recommendation.enabled is False


def test_llm_guard_detects_trace_mutation() -> None:
    engine = AnalysisEngine()
    guard = LLMGuard.default()
    request = AnalysisRequest(pillars={}, options={})
    response = engine.analyze(request)
    payload = guard.prepare_payload(response)
    payload["trace"]["rule_id"] = "mutated"
    try:
        guard.postprocess(response, payload, structure_primary=response.structure.primary)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError when trace mutated")
