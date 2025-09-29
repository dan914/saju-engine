from app.core.climate import ClimateContext, ClimateEvaluator


def test_climate_bias_lookup() -> None:
    evaluator = ClimateEvaluator.from_file()
    ctx = ClimateContext(month_branch="午", segment="중")
    result = evaluator.evaluate(ctx)
    assert result["temp_bias"] == "hot"
    assert result["humid_bias"] == "neutral"


def test_climate_default_segment() -> None:
    evaluator = ClimateEvaluator.from_file()
    ctx = ClimateContext(month_branch="申")
    result = evaluator.evaluate(ctx)
    assert result["temp_bias"] in {"mild", "cool"}
