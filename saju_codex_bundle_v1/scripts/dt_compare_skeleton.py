
#!/usr/bin/env python3
import argparse, json

def decide_alerts(deltaT_A_sec, deltaT_B_sec, boundary_margin_sec, mode="standard",
                  thresholds=None):
    T = thresholds or {"standard":5, "strict":2, "engine":1, "diverge":3, "near_std":5, "near_strict":1}
    alerts = []
    diff = abs(deltaT_A_sec - deltaT_B_sec)
    if diff > T["engine"]:
        alerts.append({"type":"engine_discrepancy", "value_sec":diff})
    if diff >= T["diverge"]:
        alerts.append({"type":"em_vs_horizons_divergence", "value_sec":diff})
    near_th = T["near_strict"] if mode=="strict" else T["near_std"]
    if boundary_margin_sec <= near_th:
        alerts.append({"type":"near_boundary", "margin_sec":boundary_margin_sec, "mode":mode})
    return {"diff_sec": diff, "alerts": alerts}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dtA", type=float, required=True, help="ΔT of model A (sec)")
    ap.add_argument("--dtB", type=float, required=True, help="ΔT of model B (sec)")
    ap.add_argument("--margin", type=float, required=True, help="|event - boundary| margin (sec)")
    ap.add_argument("--mode", choices=["standard","strict"], default="standard")
    args = ap.parse_args()
    res = decide_alerts(args.dtA, args.dtB, args.margin, args.mode)
    print(json.dumps(res, ensure_ascii=False))
