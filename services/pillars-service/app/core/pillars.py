"""Core computations for four pillars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from .constants import (
    DAY_ANCHOR,
    DAY_STEM_TO_HOUR_START,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    HOUR_BRANCHES,
    SEXAGENARY_CYCLE,
    YEAR_ANCHOR,
    YEAR_STEM_TO_MONTH_START,
)
from .month import MonthBranchResolver, default_month_resolver
from .resolve import DayBoundaryCalculator, TimeResolver


def year_pillar(year: int) -> str:
    anchor_year, anchor_pillar = YEAR_ANCHOR
    anchor_index = SEXAGENARY_CYCLE.index(anchor_pillar)
    offset = year - anchor_year
    index = (anchor_index + offset) % 60
    return SEXAGENARY_CYCLE[index]


def month_pillar(year_stem: str, month_branch: str) -> str:
    start_stem = YEAR_STEM_TO_MONTH_START[year_stem]
    start_index = HEAVENLY_STEMS.index(start_stem)
    anchor_index = EARTHLY_BRANCHES.index("寅")
    month_index = EARTHLY_BRANCHES.index(month_branch)
    offset = (month_index - anchor_index) % 12
    stem_index = (start_index + offset) % 10
    return HEAVENLY_STEMS[stem_index] + month_branch


def day_pillar(local_day_start: datetime) -> str:
    anchor_year, anchor_month, anchor_day, anchor_pillar = DAY_ANCHOR
    anchor_index = SEXAGENARY_CYCLE.index(anchor_pillar)
    anchor_dt = datetime(anchor_year, anchor_month, anchor_day)
    delta_days = (local_day_start.date() - anchor_dt.date()).days
    index = (anchor_index + delta_days) % 60
    return SEXAGENARY_CYCLE[index]


def hour_branch_for_time(local_dt: datetime) -> str:
    hour = local_dt.hour
    branch_index = ((hour + 1) // 2) % 12
    return HOUR_BRANCHES[branch_index]


def hour_range(hour_branch: str) -> Tuple[str, str]:
    index = HOUR_BRANCHES.index(hour_branch)
    start_hour = (index * 2 - 1) % 24
    end_hour = (start_hour + 2) % 24
    return (f"{start_hour:02d}:00:00", f"{end_hour:02d}:00:00")


def hour_pillar(day_stem: str, hour_branch: str) -> str:
    start_stem = DAY_STEM_TO_HOUR_START[day_stem]
    stem_index = HEAVENLY_STEMS.index(start_stem)
    branch_index = HOUR_BRANCHES.index(hour_branch)
    stem_index = (stem_index + branch_index) % 10
    return HEAVENLY_STEMS[stem_index] + hour_branch


@dataclass(slots=True)
class PillarsCalculator:
    """High-level calculator composing resolvers."""

    month_resolver: MonthBranchResolver
    day_boundary: DayBoundaryCalculator
    time_resolver: TimeResolver

    def compute(self, local_dt: datetime, timezone: str) -> dict[str, object]:
        year_p = year_pillar(local_dt.year)
        year_stem = year_p[0]

        month_branch, term_entry = self.month_resolver.resolve(local_dt, timezone)
        month_p = month_pillar(year_stem, month_branch)

        day_start = self.day_boundary.compute(local_dt, timezone)
        day_p = day_pillar(day_start)
        day_stem = day_p[0]

        hour_branch = hour_branch_for_time(local_dt)
        hour_p = hour_pillar(day_stem, hour_branch)
        hour_range_values = hour_range(hour_branch)

        return {
            "year": year_p,
            "month": month_p,
            "day": day_p,
            "hour": hour_p,
            "month_term": term_entry,
            "day_start": day_start,
            "hour_branch": hour_branch,
            "hour_range": hour_range_values,
        }


def default_calculator() -> PillarsCalculator:
    return PillarsCalculator(
        month_resolver=default_month_resolver(),
        day_boundary=DayBoundaryCalculator(),
        time_resolver=TimeResolver(),
    )
