"""Extrapolate solar-term timestamps beyond canonical coverage using linear regression."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

CANONICAL_TERMS_DIR = Path("data/canonical/terms")
OUTPUT_DIR = Path("data/canonical/terms_extrapolated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TERMS = [
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "驚蟄",
    "春分",
    "清明",
    "穀雨",
    "立夏",
    "小滿",
    "芒種",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "處暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
    "冬至",
]

START_YEAR = 1930
END_YEAR_CANONICAL = 2020
FUTURE_END_YEAR = 2050


def load_term_seconds() -> Dict[str, List[tuple[int, float]]]:
    data: Dict[str, List[tuple[int, float]]] = {term: [] for term in TERMS}
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


def linear_regression(points: List[tuple[int, float]]) -> tuple[float, float]:
    n = len(points)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    return intercept, slope


def extrapolate_term(term: str, points: List[tuple[int, float]]) -> Dict[int, float]:
    intercept, slope = linear_regression(points)
    return {
        year: intercept + slope * year
        for year in range(END_YEAR_CANONICAL + 1, FUTURE_END_YEAR + 1)
    }


def write_year(year: int, rows: List[dict[str, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
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
    for year in range(END_YEAR_CANONICAL + 1, FUTURE_END_YEAR + 1):
        rows: List[dict[str, str]] = []
        jan1 = datetime(year, 1, 1, tzinfo=timezone.utc)
        for term, points in data.items():
            if len(points) < 5:
                continue
            intercept, slope = linear_regression(points)
            seconds = intercept + slope * year
            dt = jan1 + timedelta(seconds=seconds)
            rows.append(
                {
                    "term": term,
                    "lambda_deg": "0",  # placeholder, not needed for month resolution
                    "utc_time": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "delta_t_seconds": "0.0",
                    "source": "REGRESSION_EXTRAPOLATION",
                    "algo_version": "linear",
                }
            )
        write_year(year, rows)


if __name__ == "__main__":
    main()
