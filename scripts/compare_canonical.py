"""Compare engine output with the SKY_LIZARD canonical dataset."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
PILLARS_SRC = REPO_ROOT / "services" / "pillars-service"

for candidate in (REPO_ROOT, PILLARS_SRC):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.append(candidate_str)

from app.core.month import MonthBranchResolver, SimpleSolarTermLoader
from app.core.pillars import PillarsCalculator
from app.core.resolve import DayBoundaryCalculator, TimeResolver

CANONICAL_ROOT = Path(__file__).resolve().parents[1] / "data" / "canonical"
TERMS_ROOT = Path(__file__).resolve().parents[1] / "data"


class ComparisonError(Exception):
    """Custom exception for fatal comparison issues."""


def iter_rows(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield row


def parse_local_datetime(raw: str) -> datetime:
    try:
        # fromisoformat handles both naive and UTC-offset timestamps.
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ComparisonError(f"Invalid local_datetime value: {raw}") from exc


class CanonicalComparator:
    def __init__(self, calculator: PillarsCalculator) -> None:
        self.calculator = calculator
        self.total = 0
        self.matches = 0
        self.mismatches: list[dict[str, object]] = []
        self.diff_counter: Counter[str] = Counter()

    def compare_row(self, row: dict[str, str]) -> None:
        local_dt_raw = row.get("local_datetime")
        timezone = row.get("timezone")
        if not local_dt_raw or not timezone:
            raise ComparisonError("Row missing local_datetime or timezone")
        local_dt = parse_local_datetime(local_dt_raw)
        try:
            result = self.calculator.compute(local_dt, timezone)
        except ValueError as exc:
            message = str(exc)
            if "No solar term data" in message:
                # canonical tables currently cover 1930-2020 only; skip later rows
                return
            raise
        dataset_values = {
            "year_pillar": (row.get("year_pillar") or "").strip(),
            "month_pillar": (row.get("month_pillar") or "").strip(),
            "day_pillar": (row.get("day_pillar") or "").strip(),
            "hour_pillar": (row.get("hour_pillar") or "").strip(),
        }
        result_values = {
            "year_pillar": result["year"],
            "month_pillar": result["month"],
            "day_pillar": result["day"],
            "hour_pillar": result["hour"],
        }
        self.total += 1
        keys_to_check = [key for key, value in dataset_values.items() if value]
        diff_keys = [k for k in keys_to_check if dataset_values[k] != result_values[k]]
        if not diff_keys:
            self.matches += 1
            return
        for key in diff_keys:
            self.diff_counter[key] += 1
        self.mismatches.append(
            {
                "local_datetime": local_dt_raw,
                "timezone": timezone,
                "dataset": dataset_values,
                "engine": result_values,
                "delta": diff_keys,
            }
        )

    def summary(self) -> dict[str, object]:
        return {
            "total": self.total,
            "matches": self.matches,
            "mismatches": len(self.mismatches),
            "delta_counts": dict(self.diff_counter),
        }


def discover_csv_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        help="Path to a specific canonical CSV file to compare",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=CANONICAL_ROOT,
        help="Canonical dataset directory (default: data/canonical)",
    )
    parser.add_argument(
        "--terms-root",
        type=Path,
        default=TERMS_ROOT,
        help="Directory containing terms_<year>.csv files (default: data/)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of rows to compare (useful for spot checks)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of rows to skip before comparing",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON file to write mismatch details",
    )
    args = parser.parse_args()

    if args.csv and not args.csv.exists():
        raise SystemExit(f"Specified CSV file not found: {args.csv}")

    targets = [args.csv] if args.csv else discover_csv_files(args.root)
    if not targets:
        print("No canonical CSV files found. Populate data/canonical/ to run comparisons.")
        return

    loader = SimpleSolarTermLoader(table_path=args.terms_root)
    calculator = PillarsCalculator(
        month_resolver=MonthBranchResolver(loader=loader, time_resolver=TimeResolver()),
        day_boundary=DayBoundaryCalculator(),
        time_resolver=TimeResolver(),
    )
    comparator = CanonicalComparator(calculator)

    try:
        for csv_path in targets:
            for idx, row in enumerate(iter_rows(csv_path)):
                if idx < args.skip:
                    continue
                comparator.compare_row(row)
                if args.limit and comparator.total >= args.limit:
                    break
            if args.limit and comparator.total >= args.limit:
                break
    except ComparisonError as exc:
        raise SystemExit(f"Comparison halted: {exc}") from exc

    summary = comparator.summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.out and comparator.mismatches:
        args.out.write_text(
            json.dumps(comparator.mismatches, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Mismatch details saved to {args.out}")


if __name__ == "__main__":
    main()
