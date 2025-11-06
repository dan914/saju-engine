"""Determine month branch based on solar term boundaries."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from .resolve import TimeResolver

MAJOR_TERMS = [
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
    "小寒",
]

TERM_TO_BRANCH = {
    "立春": "寅",
    "驚蟄": "卯",
    "清明": "辰",
    "立夏": "巳",
    "芒種": "午",
    "小暑": "未",
    "立秋": "申",
    "白露": "酉",
    "寒露": "戌",
    "立冬": "亥",
    "大雪": "子",
    "小寒": "丑",
}


@dataclass(slots=True)
class TermEntry:
    term: str
    lambda_deg: float
    utc_time: datetime
    local_time: datetime
    delta_t_seconds: float
    source: str
    algo_version: str


@dataclass(slots=True)
class SimpleSolarTermLoader:
    table_path: Path

    def load_year(self, year: int) -> Iterable[TermEntry]:
        file_path = self.table_path / f"terms_{year}.csv"
        if not file_path.exists():
            return []
        with file_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                utc_time = datetime.fromisoformat(row["utc_time"].replace("Z", "+00:00"))
                yield TermEntry(
                    term=row["term"],
                    lambda_deg=float(row["lambda_deg"]),
                    utc_time=utc_time,
                    local_time=utc_time,
                    delta_t_seconds=float(row["delta_t_seconds"]),
                    source=row["source"],
                    algo_version=row["algo_version"],
                )


@dataclass(slots=True)
class MonthBranchResolver:
    """Resolve the month branch using precomputed solar terms."""

    loader: SimpleSolarTermLoader
    time_resolver: TimeResolver

    def resolve(self, local_dt: datetime, timezone: str) -> tuple[str, TermEntry]:
        utc_dt, _ = self.time_resolver.resolve(local_dt, timezone)
        year = utc_dt.year
        terms = list(self.loader.load_year(year))
        if not terms:
            terms = list(self.loader.load_year(year - 1))
            if not terms:
                raise ValueError(f"No solar term data for year {year}")
        if utc_dt < terms[0].utc_time:
            previous_year_terms = list(self.loader.load_year(year - 1))
            terms = previous_year_terms + terms

        major_entries = [entry for entry in terms if entry.term in MAJOR_TERMS]
        major_entries.sort(key=lambda e: e.utc_time)
        current = None
        for entry in major_entries:
            if entry.utc_time <= utc_dt:
                current = entry
            else:
                break
        if current is None:
            current = major_entries[-1]
        branch = TERM_TO_BRANCH[current.term]
        local_current = TermEntry(
            term=current.term,
            lambda_deg=current.lambda_deg,
            utc_time=current.utc_time,
            local_time=current.utc_time.astimezone(ZoneInfo(timezone)),
            delta_t_seconds=current.delta_t_seconds,
            source=current.source,
            algo_version=current.algo_version,
        )
        return branch, local_current


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "data"


def default_month_resolver() -> MonthBranchResolver:
    loader = SimpleSolarTermLoader(table_path=DEFAULT_DATA_PATH)
    return MonthBranchResolver(loader=loader, time_resolver=TimeResolver())
