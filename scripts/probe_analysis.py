#!/usr/bin/env python3
"""Latency probe for analysis-service."""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

# Use Poetry-based imports via script loader
from scripts._script_loader import get_analysis_module

# Load required classes/functions from services
AnalysisEngine = get_analysis_module("engine", "AnalysisEngine")
AnalysisOptions = get_analysis_module("models", "AnalysisOptions")
AnalysisRequest = get_analysis_module("models", "AnalysisRequest")
PillarInput = get_analysis_module("models", "PillarInput")


def build_request() -> AnalysisRequest:
    """Return a representative AnalysisRequest payload."""

    pillars = {
        "year": PillarInput(pillar="庚辰"),
        "month": PillarInput(pillar="乙酉"),
        "day": PillarInput(pillar="乙亥"),
        "hour": PillarInput(pillar="辛巳"),
    }
    options = AnalysisOptions(
        birth_dt="2000-09-14T10:00:00+09:00",
        gender="F",
        timezone="Asia/Seoul",
    )
    return AnalysisRequest(pillars=pillars, options=options)


def percentile(samples: List[float], ratio: float) -> float:
    """Return the percentile value using linear interpolation."""

    if not samples:
        raise ValueError("samples must not be empty")
    if not 0.0 <= ratio <= 1.0:
        raise ValueError("ratio must be between 0.0 and 1.0")

    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * ratio
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return ordered[lower_index]

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    fraction = position - lower_index

    return lower_value + (upper_value - lower_value) * fraction


def run_probe(iterations: int, warmup: int) -> List[float]:
    """Execute the latency probe and return per-request timings in milliseconds."""

    engine = AnalysisEngine()

    for _ in range(warmup):
        engine.analyze(build_request())

    measurements: List[float] = []
    for _ in range(iterations):
        payload = build_request()
        start = time.perf_counter()
        engine.analyze(payload)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        measurements.append(elapsed_ms)

    return measurements


def format_stats(samples: List[float], iterations: int, warmup: int) -> dict[str, float | int]:
    """Compute summary statistics for the collected samples."""

    return {
        "iterations": iterations,
        "warmup": warmup,
        "p50_ms": round(percentile(samples, 0.5), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
        "mean_ms": round(sum(samples) / len(samples), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe analysis-service latency baselines.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=25,
        help="Number of timed calls to execute.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Number of warmup calls before recording timings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to persist metrics as JSON.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        help="Optional CSV file to append latency stats with timestamp.",
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        help="Existing baseline JSON to compare p95 latency against.",
    )
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=1.1,
        help="Multiplier over baseline p95 allowed before failing (default: 1.1).",
    )
    parser.add_argument(
        "--update-baseline-on-pass",
        action="store_true",
        help="Overwrite the baseline file when probe results stay within the threshold.",
    )
    args = parser.parse_args()

    if args.iterations <= 0:
        parser.error("--iterations must be greater than zero")
    if args.warmup < 0:
        parser.error("--warmup must be zero or greater")

    samples = run_probe(args.iterations, args.warmup)
    stats = format_stats(samples, args.iterations, args.warmup)

    baseline_p95: Optional[float] = None
    baseline_path_resolved: Optional[Path] = None
    regression_triggered = False

    if args.baseline_path:
        baseline_path_resolved = args.baseline_path.resolve()
        if args.baseline_path.exists():
            try:
                baseline_data = json.loads(args.baseline_path.read_text())
                baseline_value = baseline_data.get("p95_ms")
                if baseline_value is not None:
                    baseline_p95 = float(baseline_value)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                print(f"Warning: Could not parse baseline JSON ({exc}). Proceeding without threshold check.")
        else:
            print(f"Baseline file {args.baseline_path} not found; treating this run as initial baseline.")

    if baseline_p95 is not None:
        allowed = baseline_p95 * args.regression_threshold
        current_p95 = stats["p95_ms"]
        print(f"Baseline p95: {baseline_p95} ms; allowed up to {round(allowed, 3)} ms with threshold {args.regression_threshold}x.")
        if current_p95 > allowed:
            regression_triggered = True
            print(
                "Latency regression detected: current p95 "
                f"{current_p95} ms exceeds allowed {round(allowed, 3)} ms."
            )

    print("analysis-service latency probe")
    print(f"  iterations (timed): {stats['iterations']}")
    print(f"  warmup runs: {stats['warmup']}")
    print(f"  p50 latency: {stats['p50_ms']} ms")
    print(f"  p95 latency: {stats['p95_ms']} ms")
    print(f"  min latency: {stats['min_ms']} ms")
    print(f"  max latency: {stats['max_ms']} ms")
    print(f"  mean latency: {stats['mean_ms']} ms")

    if args.output:
        output_path = args.output.resolve()
        if regression_triggered and baseline_path_resolved and output_path == baseline_path_resolved:
            print(
                "Skipped writing metrics to baseline file to preserve canonical target. "
                "Provide a separate --output path for latest measurements."
            )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(stats, indent=2))
            print(f"\nSaved metrics to {args.output}")

    if args.history:
        args.history.parent.mkdir(parents=True, exist_ok=True)
        header = "timestamp,iterations,warmup,p50_ms,p95_ms,min_ms,max_ms,mean_ms\n"
        row = (
            f"{datetime.now(timezone.utc).isoformat()},"
            f"{stats['iterations']},"
            f"{stats['warmup']},"
            f"{stats['p50_ms']},"
            f"{stats['p95_ms']},"
            f"{stats['min_ms']},"
            f"{stats['max_ms']},"
            f"{stats['mean_ms']}\n"
        )

        if not args.history.exists():
            args.history.write_text(header + row)
        else:
            with args.history.open("a", encoding="utf-8") as fp:
                fp.write(row)
        print(f"Appended metrics to {args.history}")

    if args.update_baseline_on_pass and args.baseline_path and not regression_triggered:
        args.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        args.baseline_path.write_text(json.dumps(stats, indent=2))
        print(f"Baseline updated at {args.baseline_path}")

    if regression_triggered:
        sys.exit(1)


if __name__ == "__main__":
    main()
