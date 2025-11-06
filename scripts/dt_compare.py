#!/usr/bin/env python3
"""Delta T comparison utility using policy thresholds."""
from __future__ import annotations

import argparse
import json

from scripts._script_loader import get_astro_module

DeltaTPolicy = get_astro_module("delta_t", "DeltaTPolicy")


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
