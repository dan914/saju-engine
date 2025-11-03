"""Generate weighted vs unweighted element distribution comparison for 200 cases."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "reports" / "saju_testcases_200_results.json"
OUTPUT_PATH = REPO_ROOT / "reports" / "saju_testcases_200_elements_comparison.json"

# Allow importing the analysis-service package

# Use Poetry-based imports via script loader
from scripts._script_loader import get_analysis_module

# Load required classes/functions from services
UnweightedElementDistribution = get_analysis_module(
    "elements_unweighted", "UnweightedElementDistribution"
)

ELEMENTS = ("木", "火", "土", "金", "水")


def _to_percent(dist: Dict[str, float]) -> Dict[str, float]:
    return {k: round(dist.get(k, 0.0) * 100, 1) for k in ELEMENTS}


def main() -> None:
    if not REPORT_PATH.exists():
        raise SystemExit(f"Report not found: {REPORT_PATH}")

    data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    calc = UnweightedElementDistribution()

    comparisons: List[Dict[str, object]] = []
    deltas_per_elem: Dict[str, List[float]] = {elem: [] for elem in ELEMENTS}

    for entry in data:
        pillars = entry["pillars"]
        weighted = entry.get("elements_distribution", {})
        unweighted = calc.calculate(pillars)

        weighted_pct = _to_percent(weighted)
        unweighted_pct = _to_percent(unweighted)
        delta_pct = {
            elem: round(unweighted_pct[elem] - weighted_pct[elem], 1) for elem in ELEMENTS
        }
        for elem in ELEMENTS:
            deltas_per_elem[elem].append(delta_pct[elem])

        comparisons.append(
            {
                "case_id": entry["case_id"],
                "season": entry.get("season"),
                "case_type": entry.get("case_type"),
                "birth_date": entry.get("birth_date"),
                "birth_time": entry.get("birth_time"),
                "gender": entry.get("gender_ko"),
                "pillars": entry["pillars"],
                "weighted_pct": weighted_pct,
                "unweighted_pct": unweighted_pct,
                "delta_pct": delta_pct,
            }
        )

    summary = {
        "average_delta_pct": {elem: round(mean(vals), 2) for elem, vals in deltas_per_elem.items()},
        "min_delta_pct": {elem: min(vals) for elem, vals in deltas_per_elem.items()},
        "max_delta_pct": {elem: max(vals) for elem, vals in deltas_per_elem.items()},
    }

    payload = {"summary": summary, "cases": comparisons}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote comparison for {len(comparisons)} cases → {OUTPUT_PATH}")
    print("Average delta (unweighted − weighted) [%]:", summary["average_delta_pct"])
    print("Max delta [%]:", summary["max_delta_pct"])
    print("Min delta [%]:", summary["min_delta_pct"])


if __name__ == "__main__":
    main()
