"""Compute future pillars using current engine and predicted solar terms."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Use Poetry-based imports via script loader
from scripts._script_loader import get_pillars_module

# Load required classes/functions from pillars-service
MonthBranchResolver = get_pillars_module("month", "MonthBranchResolver")
SimpleSolarTermLoader = get_pillars_module("month", "SimpleSolarTermLoader")
PillarsCalculator = get_pillars_module("pillars", "PillarsCalculator")
DayBoundaryCalculator = get_pillars_module("resolve", "DayBoundaryCalculator")
TimeResolver = get_pillars_module("resolve", "TimeResolver")

OUTPUT_PATH = Path("data/canonical/pillars_generated_2021_2050.csv")
TIMEZONE = "Asia/Seoul"
TZ = ZoneInfo(TIMEZONE)
START = date(2021, 1, 1)
END = date(2050, 1, 22)

calculator = PillarsCalculator(
    month_resolver=MonthBranchResolver(
        loader=SimpleSolarTermLoader(table_path=Path("data")),
        time_resolver=TimeResolver(),
    ),
    day_boundary=DayBoundaryCalculator(),
    time_resolver=TimeResolver(),
)


def main() -> None:
    rows: list[dict[str, str]] = []
    current = START
    while current <= END:
        local_dt = datetime.combine(current, datetime.min.time()).replace(hour=12, tzinfo=TZ)
        result = calculator.compute(local_dt, TIMEZONE)
        rows.append(
            {
                "local_datetime": local_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "timezone": TIMEZONE,
                "longitude_deg": "126.9784",
                "latitude_deg": "37.5665",
                "year_pillar": result["year"],
                "month_pillar": result["month"],
                "day_pillar": result["day"],
                "hour_pillar": "",
                "month_term": result["month_term"].term if result.get("month_term") else "",
                "delta_t_seconds": "",
                "dataset_version": "ENGINE_PREDICTED",
                "notes": '{"source":"engine","terms":"predicted_quadratic"}',
            }
        )
        current += timedelta(days=1)

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "local_datetime",
                "timezone",
                "longitude_deg",
                "latitude_deg",
                "year_pillar",
                "month_pillar",
                "day_pillar",
                "hour_pillar",
                "month_term",
                "delta_t_seconds",
                "dataset_version",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
