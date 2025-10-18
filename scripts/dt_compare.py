#!/usr/bin/env python3
"""Delta T comparison utility using policy thresholds."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import from common package (replaces cross-service import)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "common"))
from saju_common import SimpleDeltaT


# Wrapper class for backwards compatibility
class DeltaTPolicy:
    """Wrapper for SimpleDeltaT with legacy load() method."""

    @staticmethod
    def load():
        return {"engine": 1.0, "boundary": 0.5}

    @staticmethod
    def delta_t_seconds(year: int, month: int) -> float:
        """Calculate ΔT using SimpleDeltaT implementation"""
        dt_impl = SimpleDeltaT()
        return dt_impl.delta_t_seconds(year, month)


def decide_alerts(
    deltaT_A_sec: float,
    deltaT_B_sec: float,
    boundary_margin_sec: float,
    mode: str,
    thresholds: dict,
) -> dict:
    diff = abs(deltaT_A_sec - deltaT_B_sec)
    alerts = []
    if diff > thresholds["engine"]:
        alerts.append({"type": "engine_discrepancy", "value_sec": diff})
    if diff >= thresholds["diverge"]:
        alerts.append({"type": "em_vs_horizons_divergence", "value_sec": diff})
    near_threshold = thresholds["near_strict"] if mode == "strict" else thresholds["near_std"]
    if boundary_margin_sec <= near_threshold:
        alerts.append({"type": "near_boundary", "margin_sec": boundary_margin_sec, "mode": mode})
    return {"diff_sec": diff, "alerts": alerts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare ΔT models using policy thresholds")
    parser.add_argument("--dtA", type=float, required=True, help="ΔT of model A (sec)")
    parser.add_argument("--dtB", type=float, required=True, help="ΔT of model B (sec)")
    parser.add_argument(
        "--margin", type=float, required=True, help="|event - boundary| margin (sec)"
    )
    parser.add_argument("--mode", choices=["standard", "strict"], default="standard")
    args = parser.parse_args()

    policy = DeltaTPolicy.load()
    result = decide_alerts(args.dtA, args.dtB, args.margin, args.mode, policy.thresholds)
    result["policy_version"] = policy.version
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
