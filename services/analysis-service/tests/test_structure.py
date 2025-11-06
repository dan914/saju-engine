from .structure import StructureContext, StructureDetector


def build_detector() -> StructureDetector:
    return StructureDetector.from_file()


def test_structure_primary_selected_with_confidence() -> None:
    detector = build_detector()
    ctx = StructureContext(scores={"정관": 15, "정재": 8, "편재": 5})
    result = detector.evaluate(ctx)
    assert result.primary == "정관"
    assert result.confidence == "mid"
    assert any(cand["type"] == "정관" for cand in result.candidates)


def test_structure_candidates_only_when_below_primary_threshold() -> None:
    detector = build_detector()
    ctx = StructureContext(scores={"정관": 8, "편재": 7, "비겁": 5})
    result = detector.evaluate(ctx)
    assert result.primary is None
    assert result.confidence == "low"
    assert len(result.candidates) >= 1
    assert any(cand["type"] == "정관" for cand in result.candidates)
