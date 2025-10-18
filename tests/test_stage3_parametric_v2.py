# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

# Handle hyphenated directory name
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "analysis-service" / "app" / "core"))

from climate_advice import ClimateAdvice
from engine import AnalysisEngine
from gyeokguk_classifier import GyeokgukClassifier
from luck_flow import LuckFlow
from pattern_profiler import PatternProfiler

CASES = sorted((Path(__file__).parent/"golden_cases").glob("case_*.json"))

def test_golden_cases_e2e():
    ca = ClimateAdvice(); lf = LuckFlow(); gk = GyeokgukClassifier(); pp = PatternProfiler()
    for fp in CASES:
        case = json.loads(fp.read_text(encoding="utf-8"))
        ctx = case["context"] | {
            "strength": case.get("strength", {}),
            "relation": case.get("relation", {}),
            "climate": case.get("climate", {}),
            "yongshin": case.get("yongshin", {}),
            "daewoon": case.get("daewoon", {}),
            "sewoon": case.get("sewoon", {})
        }
        luck = lf.run(ctx)
        gky = gk.run({**ctx, "luck_flow": luck})
        cav = ca.run(ctx)
        ppy = pp.run({**ctx, "luck_flow": luck, "gyeokguk": gky})

        exp = case.get("expect", {})
        if "climate_policy_id" in exp:
            assert cav["matched_policy_id"] == exp["climate_policy_id"], f"{case['id']} climate policy mismatch"
        if "luck_flow_trend" in exp:
            assert luck["trend"] == exp["luck_flow_trend"], f"{case['id']} luck trend mismatch"
        if "gyeokguk_type" in exp:
            assert gky["type"] == exp["gyeokguk_type"], f"{case['id']} gyeokguk mismatch"
        if "patterns_include" in exp:
            assert set(exp["patterns_include"]).issubset(set(ppy["patterns"])), f"{case['id']} pattern tags missing"

def test_engine_wrapper_smoke():
    fp = CASES[6]  # one rich case
    case = json.loads(fp.read_text(encoding="utf-8"))
    ctx = case["context"] | {
        "strength": case.get("strength", {}),
        "relation": case.get("relation", {}),
        "climate": case.get("climate", {}),
        "yongshin": case.get("yongshin", {}),
        "daewoon": case.get("daewoon", {}),
        "sewoon": case.get("sewoon", {})
    }
    out = AnalysisEngine().analyze(ctx)
    for k in ["luck_flow","gyeokguk","climate_advice","pattern"]:
        assert k in out and isinstance(out[k], dict)
