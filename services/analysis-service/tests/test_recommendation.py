from .recommendation import RecommendationGuard


def build_guard() -> RecommendationGuard:
    return RecommendationGuard.from_file()


def test_recommendation_disabled_without_structure() -> None:
    guard = build_guard()
    result = guard.decide(structure_primary=None)
    assert result["enabled"] is False
    assert result["action"] != "allow"


def test_recommendation_allowed_with_structure() -> None:
    guard = build_guard()
    result = guard.decide(structure_primary="정관")
    assert result["enabled"] is True
    assert result["action"] == "allow"
