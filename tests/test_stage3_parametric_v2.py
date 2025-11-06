# -*- coding: utf-8 -*-
import json
from pathlib import Path

from tests._analysis_loader import get_core_attr, get_model_attr, load_app_module

ClimateAdvice = get_core_attr("climate_advice", "ClimateAdvice")
LuckFlow = get_core_attr("luck_flow", "LuckFlow")
GyeokgukClassifier = get_core_attr("gyeokguk_classifier", "GyeokgukClassifier")
PatternProfiler = get_core_attr("pattern_profiler", "PatternProfiler")
AnalysisEngine = load_app_module("core.engine").AnalysisEngine
AnalysisRequest = get_model_attr("analysis", "AnalysisRequest")
AnalysisOptions = get_model_attr("analysis", "AnalysisOptions")
AnalysisResponse = get_model_attr("analysis", "AnalysisResponse")
PillarInput = get_model_attr("analysis", "PillarInput")

CASES = sorted((Path(__file__).parent / "golden_cases").glob("case_*.json"))


def test_golden_cases_e2e():
    ca = ClimateAdvice()
    lf = LuckFlow()
    gk = GyeokgukClassifier()
    pp = PatternProfiler()
    for fp in CASES:
        case = json.loads(fp.read_text(encoding="utf-8"))
        ctx = case["context"] | {
            "strength": case.get("strength", {}),
            "relation": case.get("relation", {}),
            "climate": case.get("climate", {}),
            "yongshin": case.get("yongshin", {}),
            "daewoon": case.get("daewoon", {}),
            "sewoon": case.get("sewoon", {}),
        }
        luck = lf.run(ctx)
        gky = gk.run({**ctx, "luck_flow": luck})
        cav = ca.run(ctx)
        ppy = pp.run({**ctx, "luck_flow": luck, "gyeokguk": gky})

        exp = case.get("expect", {})
        if "climate_policy_id" in exp:
            assert (
                cav["matched_policy_id"] == exp["climate_policy_id"]
            ), f"{case['id']} climate policy mismatch"
        if "luck_flow_trend" in exp:
            assert luck["trend"] == exp["luck_flow_trend"], f"{case['id']} luck trend mismatch"
        if "gyeokguk_type" in exp:
            assert gky["type"] == exp["gyeokguk_type"], f"{case['id']} gyeokguk mismatch"
        if "patterns_include" in exp:
            assert set(exp["patterns_include"]).issubset(
                set(ppy["patterns"])
            ), f"{case['id']} pattern tags missing"


def test_engine_wrapper_smoke():
    fp = CASES[6]  # one rich case
    case = json.loads(fp.read_text(encoding="utf-8"))
    ctx = case["context"] | {
        "strength": case.get("strength", {}),
        "relation": case.get("relation", {}),
        "climate": case.get("climate", {}),
        "yongshin": case.get("yongshin", {}),
        "daewoon": case.get("daewoon", {}),
        "sewoon": case.get("sewoon", {}),
    }
    request = AnalysisRequest(
        pillars={pos: PillarInput(pillar="甲子") for pos in ["year", "month", "day", "hour"]},
        options=AnalysisOptions(
            birth_dt="2000-01-01T00:00:00+09:00",
            gender="F",
            timezone="Asia/Seoul",
        ),
    )
    response = AnalysisEngine().analyze(request)
    assert isinstance(response, AnalysisResponse)
