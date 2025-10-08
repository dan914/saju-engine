"""Predict solar term timestamps beyond canonical range via quadratic regression."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

CANONICAL_TERMS_DIR = Path("data/canonical/terms")
OUTPUT_DIR = Path("data/canonical/terms_predicted")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TERMS = [
    "小寒",
    "立春",
    "驚蟄",
    "清明",
    "立夏",
    "芒種",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
]

START_YEAR = 1930
END_YEAR_CANONICAL = 2020
PREDICT_START_YEAR = 2021
PREDICT_END_YEAR = 2050
REFERENCE_YEAR = 2000


def load_term_seconds() -> Dict[str, List[Tuple[int, float]]]:
    data: Dict[str, List[Tuple[int, float]]] = {term: [] for term in TERMS}
    for year in range(START_YEAR, END_YEAR_CANONICAL + 1):
        path = CANONICAL_TERMS_DIR / f"terms_{year}.csv"
        if not path.exists():
            continue
        jan1 = datetime(year, 1, 1, tzinfo=timezone.utc)
        with path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                term = row["term"]
                dt = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                seconds = (dt - jan1).total_seconds()
                data[term].append((year, seconds))
    return data


def solve_quadratic(points: List[Tuple[int, float]]) -> Tuple[float, float, float]:
    # Fit seconds = a + b*x + c*x^2, where x = year - REFERENCE_YEAR
    n = len(points)
    if n < 3:
        raise ValueError("Need at least 3 points for quadratic fit")
    xs = [year - REFERENCE_YEAR for year, _ in points]
    ys = [seconds for _, seconds in points]
    sum_x = sum(xs)
    sum_x2 = sum(x * x for x in xs)
    sum_x3 = sum(x * x * x for x in xs)
    sum_x4 = sum(x * x * x * x for x in xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2y = sum((x * x) * y for x, y in zip(xs, ys))

    # Normal equations
    # [n, sum_x, sum_x2][a]   [sum_y]
    # [sum_x, sum_x2, sum_x3][b] = [sum_xy]
    # [sum_x2, sum_x3, sum_x4][c]  [sum_x2y]
    A = [
        [n, sum_x, sum_x2],
        [sum_x, sum_x2, sum_x3],
        [sum_x2, sum_x3, sum_x4],
    ]
    B = [sum_y, sum_xy, sum_x2y]

    # Gaussian elimination for 3x3 system
    for i in range(3):
        # Pivot
        pivot = A[i][i]
        if abs(pivot) < 1e-12:
            raise ValueError("Singular matrix in regression")
        for j in range(i, 3):
            A[i][j] /= pivot
        B[i] /= pivot
        # Eliminate
        for k in range(3):
            if k == i:
                continue
            factor = A[k][i]
            for j in range(i, 3):
                A[k][j] -= factor * A[i][j]
            B[k] -= factor * B[i]
    a, b, c = B
    return a, b, c


def predict_seconds(year: int, coeffs: Tuple[float, float, float]) -> float:
    a, b, c = coeffs
    x = year - REFERENCE_YEAR
    return a + b * x + c * x * x


def write_year(year: int, rows: List[Dict[str, str]]) -> None:
    path = OUTPUT_DIR / f"terms_{year}.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "term",
                "lambda_deg",
                "utc_time",
                "delta_t_seconds",
                "source",
                "algo_version",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    data = load_term_seconds()
    for term, points in data.items():
        if len(points) < 6:
            raise SystemExit(f"Insufficient data for term {term}")
    coeffs_map = {term: solve_quadratic(points) for term, points in data.items()}
    for year in range(PREDICT_START_YEAR, PREDICT_END_YEAR + 1):
        rows: List[Dict[str, str]] = []
        jan1 = datetime(year, 1, 1, tzinfo=timezone.utc)
        for term in TERMS:
            coeffs = coeffs_map[term]
            seconds = predict_seconds(year, coeffs)
            dt = jan1 + timedelta(seconds=seconds)
            rows.append(
                {
                    "term": term,
                    "lambda_deg": "0",
                    "utc_time": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "delta_t_seconds": "0.0",
                    "source": "POLY_EXTRAPOLATION",
                    "algo_version": "quadratic",
                }
            )
        write_year(year, rows)
        print(f"Predicted terms for {year}")


if __name__ == "__main__":
    main()
