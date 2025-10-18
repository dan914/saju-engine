"""Build evidence logs for 근거 보기."""

from __future__ import annotations

import json

# Import real implementations from shared common package
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pathlib import Path as _Path
from typing import Dict, Iterable, Tuple
from zoneinfo import ZoneInfo

sys.path.insert(0, str(_Path(__file__).resolve().parents[4] / "services" / "common"))
from saju_common.engines import LuckCalculator, LuckContext, ShenshaCatalog

from .month import SimpleSolarTermLoader
from .strength import StrengthEvaluator
from .wang import WangStateMapper

CLIMATE_POLICY_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_addendum_v2"
    / "policies"
    / "climate_map_v1.json"
)
TERM_DATA_PATH = Path(__file__).resolve().parents[4] / "data"
SCHOOL_POLICY_PATH = Path(__file__).resolve().parents[4] / "policies" / "school_profiles_v1.json"


@dataclass(slots=True)
class EvidenceBuilder:
    """Construct evidence logs aligned with the template contract."""

    strength_evaluator: StrengthEvaluator
    wang_mapper: WangStateMapper
    climate_map: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    term_loader: SimpleSolarTermLoader | None = None
    luck_calculator: LuckCalculator | None = None
    shensha_catalog: ShenshaCatalog | None = None
    school_profiles: Dict[str, object] | None = None

    @classmethod
    def default(cls) -> "EvidenceBuilder":
        climate_data: Dict[str, Dict[str, Dict[str, str]]] = {}
        if CLIMATE_POLICY_PATH.exists():
            with CLIMATE_POLICY_PATH.open("r", encoding="utf-8") as f:
                climate_data = json.load(f).get("bias", {})
        school_data = {}
        if SCHOOL_POLICY_PATH.exists():
            with SCHOOL_POLICY_PATH.open("r", encoding="utf-8") as sf:
                school_data = json.load(sf)
        return cls(
            strength_evaluator=StrengthEvaluator.from_files(),
            wang_mapper=WangStateMapper.from_file(),
            climate_map=climate_data,
            term_loader=SimpleSolarTermLoader(TERM_DATA_PATH),
            luck_calculator=LuckCalculator(),
            shensha_catalog=ShenshaCatalog(),
            school_profiles=school_data,
        )

    def _climate_bias(self, month_branch: str) -> Dict[str, str]:
        branch_data = self.climate_map.get(month_branch, {})
        segment_data = branch_data.get("중", {"temp": "neutral", "humid": "neutral"})
        return {
            "segment": "중",
            "temp_bias": segment_data.get("temp", "neutral"),
            "humid_bias": segment_data.get("humid", "neutral"),
        }

    def _solar_term_window(self, utc_dt: datetime) -> Tuple[object | None, object | None]:
        if not self.term_loader:
            return None, None
        terms = list(self.term_loader.load_year(utc_dt.year)) + list(
            self.term_loader.load_year(utc_dt.year + 1)
        )
        prev_term = None
        next_term = None
        for entry in terms:
            if entry.utc_time <= utc_dt:
                prev_term = entry
            if entry.utc_time > utc_dt:
                next_term = entry
                break
        return prev_term, next_term

    def build(
        self,
        *,
        local_dt: datetime,
        timezone_name: str,
        pillars_result: Dict[str, object],
        month_term: object,
        month_branch: str,
        delta_t_seconds: float = 57.4,
        combos: Dict[str, int] | None = None,
        visible_counts: Dict[str, int] | None = None,
        branch_roots: Iterable[str] | None = None,
        tzdb_version: str = "2025a",
    ) -> Dict[str, object]:
        combos = combos or {}
        visible_counts = visible_counts or {}
        branch_roots = list(branch_roots or [])

        tz = ZoneInfo(timezone_name)
        localized = local_dt.replace(tzinfo=tz)
        utc_dt = localized.astimezone(timezone.utc)
        offset = localized.utcoffset() or timedelta(0)
        dst_flag = bool(localized.dst())

        day_pillar = str(pillars_result["day"])
        strength_details = self.strength_evaluator.evaluate(
            month_branch=month_branch,
            day_pillar=day_pillar,
            branch_roots=branch_roots,
            visible_counts=visible_counts,
            combos=combos,
        )

        prev_term_entry, next_term_entry = self._solar_term_window(utc_dt)
        prev_term_name = getattr(prev_term_entry, "term", None) if prev_term_entry else None
        next_term_name = getattr(next_term_entry, "term", None) if next_term_entry else None
        prev_term_iso = (
            prev_term_entry.utc_time.isoformat().replace("+00:00", "Z")
            if prev_term_entry and getattr(prev_term_entry, "utc_time", None)
            else None
        )
        next_term_iso = (
            next_term_entry.utc_time.isoformat().replace("+00:00", "Z")
            if next_term_entry and getattr(next_term_entry, "utc_time", None)
            else None
        )

        interval_days = None
        days_from_prev = None
        start_age = None
        if next_term_entry and getattr(next_term_entry, "utc_time", None):
            interval_seconds = (next_term_entry.utc_time - utc_dt).total_seconds()
            interval_days = round(interval_seconds / 86400, 4)
            start_age = round(interval_days / 3.0, 4)
        if prev_term_entry and getattr(prev_term_entry, "utc_time", None):
            days_from_prev = round((utc_dt - prev_term_entry.utc_time).total_seconds() / 86400, 4)

        diffs = []
        if prev_term_entry and getattr(prev_term_entry, "utc_time", None):
            diffs.append(abs((utc_dt - prev_term_entry.utc_time).total_seconds()))
        if next_term_entry and getattr(next_term_entry, "utc_time", None):
            diffs.append(abs((next_term_entry.utc_time - utc_dt).total_seconds()))
        near_boundary_sec = min(diffs) if diffs else 0.0

        luck_calc = {
            "prev_term": prev_term_name,
            "next_term": next_term_name,
            "interval_days": interval_days,
            "days_from_prev": days_from_prev,
            "start_age": start_age,
        }
        luck_direction = {"direction": None, "method": None, "sex_at_birth": None}
        if self.luck_calculator:
            luck_context = LuckContext(local_dt=local_dt, timezone=timezone_name)
            luck_calc = self.luck_calculator.compute_start_age(luck_context)
            luck_direction = self.luck_calculator.luck_direction(luck_context)

        shensha = (
            self.shensha_catalog.list_enabled()
            if self.shensha_catalog
            else {"enabled": False, "list": []}
        )

        month_term_name = getattr(month_term, "term", None)
        month_term_iso = (
            getattr(month_term, "utc_time").isoformat().replace("+00:00", "Z")
            if getattr(month_term, "utc_time", None)
            else None
        )
        return {
            "engine": {"mode": "KR_classic", "ver": "1.4"},
            "inputs": {
                "birth_local": local_dt.strftime("%Y-%m-%d %H:%M"),
                "tzid": timezone_name,
            },
            "time_resolve": {
                "utc": utc_dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "tzdb_ver": tzdb_version,
                "dst": dst_flag,
                "offset_sec": int(offset.total_seconds()),
            },
            "solar_terms": {
                "prev_term": month_term_name,
                "prev_ts": month_term_iso,
                "next_term": next_term_name,
                "next_ts": next_term_iso,
            },
            "ΔT": {
                "value_sec": delta_t_seconds,
                "model": "Espenak–Meeus",
                "uncertainty_sec": 0.2,
                "flag": False,
            },
            "LMT": {"applied": False},
            "time_basis": "STD",
            "day_boundary_policy": "LCRO",
            "pillars": {
                "year": pillars_result["year"],
                "month": pillars_result["month"],
                "day": pillars_result["day"],
                "hour": pillars_result["hour"],
            },
            "month_branch": month_branch,
            "wang_map": self.wang_mapper.mapping.get(month_branch, {}),
            "climate": self._climate_bias(month_branch),
            "strength_scoring": strength_details,
            "root": {"level": "미구현", "hits": []},
            "seal": {"level": "미구현", "hits": []},
            "luck_calc": luck_calc,
            "luck_direction": luck_direction,
            "shensha": shensha,
            "lunar_info": {
                "is_leap_month": False,
                "leap_month_number": None,
                "actual_month_branch": month_branch,
                "next_solar_term": next_term_name,
                "next_term_utc": next_term_iso,
            },
            "boundary_review": {
                "near_term_boundary_sec": round(near_boundary_sec, 3),
                "action": "none",
                "secondary_engine_agreed": False,
            },
            "yugi": {"month_branch_minor_elevated": False},
            "five_he": {"transform_applied": False, "scope": "none"},
            "jdn_precision": {
                "day_start_utc": None,
                "birth_utc": utc_dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "comparison_millis": 0,
            },
            "policy_refs": {
                "seasons_wang_map": "v2.0",
                "strength_criteria": "v1.0",
                "strength_scale": "v1.1",
                "zanggan_table": "v1.0",
                "root_seal_criteria": "v1.0",
                "deltaT_policy": "v1.0",
                "lunar_policy": "v1.0",
                "boundary_review_policy": "v1.0",
                "luck_start_policy": "v1.1",
                "five_he_policy": "v1.0",
                "root_seal_policy": self.strength_evaluator.scorer.policy_version or "v2.3",
            },
        }
