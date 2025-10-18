"""Luck direction and start-age calculations.

Extracted from analysis-service to services/common for shared use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from policy_loader import resolve_policy_path
from saju_common import BasicTimeResolver as TimeResolver

# Import from parent saju_common package
from saju_common import FileSolarTermLoader

# Use policy loader for flexible path resolution
LUCK_POLICY_PATH = resolve_policy_path("luck_policy_v1.json")
TERM_DATA_PATH = Path(__file__).resolve().parents[4] / "data"


@dataclass(slots=True)
class LuckContext:
    """Context for luck calculations."""
    local_dt: datetime
    timezone: str
    day_master: Optional[str] = None
    gender: Optional[str] = None
    year_stem: Optional[str] = None  # For direction calculation


class LuckCalculator:
    """Calculate luck cycle start age and direction."""

    def __init__(self) -> None:
        with LUCK_POLICY_PATH.open("r", encoding="utf-8") as f:
            self._policy = json.load(f)
        self._term_loader = FileSolarTermLoader(TERM_DATA_PATH)
        self._resolver = TimeResolver()

    def compute_start_age(self, ctx: LuckContext, direction: Optional[str] = None) -> Dict[str, float | str]:
        """
        Calculate luck cycle start age based on direction.

        Rule (from luck_pillars_policy.json):
        - Forward (순행): Use interval from birth to NEXT solar term
        - Backward (역행): Use interval from PREVIOUS solar term to birth

        Args:
            ctx: LuckContext with birth datetime and timezone
            direction: "forward" or "backward" (default: "forward")
        """
        birth_utc = self._resolver.to_utc(ctx.local_dt, ctx.timezone)
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

        # Calculate interval based on direction
        if direction == "backward":
            # Backward: use interval from prev_term to birth
            interval_sec = (birth_utc - prev_term.utc_time).total_seconds()
        else:
            # Forward (default): use interval from birth to next_term
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
        """
        Calculate luck direction based on year stem yin/yang and gender.

        Rule (from luck_pillars_policy.json):
        - Male + Yang year stem = Forward (순행)
        - Male + Yin year stem = Backward (역행)
        - Female + Yang year stem = Backward (역행)
        - Female + Yin year stem = Forward (순행)
        """
        methods = self._policy.get("methods", {})
        method_info = methods.get("traditional_sex", {})
        method_name = (
            "traditional_sex" if method_info.get("default", False) else next(iter(methods), None)
        )

        direction = None
        if ctx.gender and ctx.year_stem:
            gender = ctx.gender.lower()

            # Determine year stem yin/yang
            YANG_STEMS = ["甲", "丙", "戊", "庚", "壬"]
            YIN_STEMS = ["乙", "丁", "己", "辛", "癸"]

            is_yang = ctx.year_stem in YANG_STEMS
            is_yin = ctx.year_stem in YIN_STEMS

            # Apply direction matrix from policy
            if gender in ("male", "m"):
                if is_yang:
                    direction = "forward"
                elif is_yin:
                    direction = "backward"
            elif gender in ("female", "f"):
                if is_yang:
                    direction = "backward"
                elif is_yin:
                    direction = "forward"

        return {"direction": direction, "method": method_name, "sex_at_birth": ctx.gender}

    def compute(
        self,
        pillars: Optional[Dict[str, str]] = None,
        birth_dt: Optional[str | datetime] = None,
        gender: Optional[str] = None,
        timezone: str = "Asia/Seoul",
    ) -> Dict[str, object]:
        """
        Unified compute method for orchestrator compatibility.

        Combines start_age calculation and direction determination.

        Args:
            pillars: Four pillars dict (required for direction calculation)
            birth_dt: Birth datetime (ISO string or datetime object)
            gender: Gender ("M"/"F" or "male"/"female")
            timezone: IANA timezone string (default: "Asia/Seoul")

        Returns:
            Dict with keys:
                - start_age: float (when 대운 starts, in years)
                - prev_term: str (previous solar term name)
                - next_term: str (next solar term name)
                - interval_days: float (days to next term)
                - days_from_prev: float (days since previous term)
                - direction: str ("forward" or "backward")
                - method: str (method used, e.g., "traditional_sex")
                - sex_at_birth: str (gender value)
        """
        # Parse birth_dt if string
        if isinstance(birth_dt, str):
            birth_dt = datetime.fromisoformat(birth_dt.replace("Z", "+00:00"))
            if birth_dt.tzinfo is None:
                birth_dt = birth_dt.replace(tzinfo=ZoneInfo(timezone))

        if birth_dt is None:
            raise ValueError("birth_dt is required for luck calculation")

        # Extract year stem from pillars for direction calculation
        year_stem = None
        if pillars and "year" in pillars:
            year_stem = pillars["year"][0]  # First character is the stem

        # Create context
        ctx = LuckContext(
            local_dt=birth_dt,
            timezone=timezone,
            gender=gender,
            year_stem=year_stem
        )

        # First determine direction (needed for start_age calculation)
        direction_result = self.luck_direction(ctx)
        direction = direction_result.get("direction")

        # Then compute start age using the correct direction
        start_age_result = self.compute_start_age(ctx, direction=direction)

        # Merge results
        return {
            **start_age_result,
            **direction_result,
        }
