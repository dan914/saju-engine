"""Delta T policy utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

POLICY_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_bundle_v1"
    / "policy"
    / "deltaT_policy_v1.json"
)


@dataclass(slots=True)
class DeltaTPolicy:
    version: str
    thresholds: Dict[str, float]
    fallback_triggers: List[Dict[str, object]]
    source_precedence: List[Dict[str, object]]
    logging_fields: List[str]

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> "DeltaTPolicy":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        thresholds = data.get("thresholds", {})
        mapped = {
            "standard": thresholds.get("standard_alert_sec", 5),
            "strict": thresholds.get("strict_alert_sec", 2),
            "engine": thresholds.get("engine_discrepancy_sec", 1),
            "diverge": thresholds.get("em_vs_horizons_divergence_sec", 3),
            "near_std": thresholds.get("boundary_near_standard_sec", 5),
            "near_strict": thresholds.get("boundary_near_strict_sec", 1),
        }
        return cls(
            version=data.get("version", "unknown"),
            thresholds=mapped,
            fallback_triggers=data.get("fallback_triggers", []),
            source_precedence=data.get("source_precedence", []),
            logging_fields=data.get("logging_fields", []),
        )

    def select_source(self, year: int) -> Tuple[str | None, str | None]:
        for entry in self.source_precedence:
            start, end = entry.get("years", [None, None])
            if start is None or end is None:
                continue
            if start <= year <= end:
                return entry.get("prefer"), entry.get("fallback")
        return None, None
