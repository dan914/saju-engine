"""Climate evaluation based on climate_map_v1 policy."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import json

POLICY_PATH = Path(__file__).resolve().parents[5] / "saju_codex_addendum_v2" / "policies" / "climate_map_v1.json"


@dataclass(slots=True)
class ClimateContext:
    month_branch: str
    segment: str = "중"  # 초/중/말
    day_master: Optional[str] = None
    strength_grade: Optional[str] = None


class ClimateEvaluator:
    def __init__(self, policy: Dict[str, object]) -> None:
        self._policy = policy
        self._bias = policy.get("bias", {})

    @classmethod
    def from_file(cls, path: Path = POLICY_PATH) -> "ClimateEvaluator":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def evaluate(self, ctx: ClimateContext) -> Dict[str, object]:
        branch_bias = self._bias.get(ctx.month_branch, {})
        segment_bias = branch_bias.get(ctx.segment, {"temp": "neutral", "humid": "neutral"})
        return {
            "temp_bias": segment_bias.get("temp", "neutral"),
            "humid_bias": segment_bias.get("humid", "neutral"),
            "advice_bucket": [],  # placeholder for future advice mapping
        }
