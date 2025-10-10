"""Luck direction and start-age calculations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from zoneinfo import ZoneInfo

# Import from common package (replaces cross-service imports)
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[6] / "services" / "common"))
from saju_common import TableSolarTermLoader as SimpleSolarTermLoader
from saju_common import BasicTimeResolver as TimeResolver
from policy_loader import resolve_policy_path


# Use policy loader for flexible path resolution
LUCK_POLICY_PATH = resolve_policy_path("luck_policy_v1.json")
SHENSHA_CATALOG_PATH = resolve_policy_path("shensha_catalog_v1.json")
TERM_DATA_PATH = Path(__file__).resolve().parents[5] / "data"


@dataclass(slots=True)
class LuckContext:
    local_dt: datetime
    timezone: str
    day_master: Optional[str] = None
    gender: Optional[str] = None


class LuckCalculator:
    def __init__(self) -> None:
        with LUCK_POLICY_PATH.open("r", encoding="utf-8") as f:
            self._policy = json.load(f)
        self._term_loader = SimpleSolarTermLoader(TERM_DATA_PATH)
        self._resolver = TimeResolver()

    def compute_start_age(self, ctx: LuckContext) -> Dict[str, float | str]:
        localized = ctx.local_dt.replace(tzinfo=ZoneInfo(ctx.timezone))
        birth_utc, _ = self._resolver.resolve(ctx.local_dt, ctx.timezone)
        year = birth_utc.year
        terms = list(self._term_loader.load_year(year)) + list(
            self._term_loader.load_year(year + 1)
        )
        next_term = next((entry for entry in terms if entry.utc_time > birth_utc), None)
        prev_term = None
        for entry in terms:
            if entry.utc_time <= birth_utc:
                prev_term = entry
            else:
                break
        if not next_term or not prev_term:
            return {"start_age": 0.0, "interval_days": 0.0, "prev_term": None, "next_term": None}
        interval_sec = (next_term.utc_time - birth_utc).total_seconds()
        interval_days = round(interval_sec / 86400, 4)
        start_age = round(interval_days / 3.0, 4)
        days_from_prev = round((birth_utc - prev_term.utc_time).total_seconds() / 86400, 4)
        return {
            "prev_term": prev_term.term,
            "next_term": next_term.term,
            "interval_days": interval_days,
            "days_from_prev": days_from_prev,
            "start_age": start_age,
        }

    def luck_direction(self, ctx: LuckContext) -> Dict[str, str | None]:
        methods = self._policy.get("methods", {})
        method_info = methods.get("traditional_sex", {})
        method_name = (
            "traditional_sex" if method_info.get("default", False) else next(iter(methods), None)
        )
        direction = None
        if ctx.gender:
            gender = ctx.gender.lower()
            if gender in ("male", "m"):
                direction = "forward"
            elif gender in ("female", "f"):
                direction = "reverse"
        return {"direction": direction, "method": method_name, "sex_at_birth": ctx.gender}


class ShenshaCatalog:
    def __init__(self) -> None:
        with SHENSHA_CATALOG_PATH.open("r", encoding="utf-8") as f:
            self._catalog = json.load(f)

    def list_enabled(self, pro_mode: bool = False) -> Dict[str, object]:
        data = self._catalog.get("pro_mode" if pro_mode else "default", {})
        return {"enabled": data.get("enabled", False), "list": data.get("list", [])}
