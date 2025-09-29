"""Recommendation guard per policy."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import json

POLICY_PATH = Path(__file__).resolve().parents[5] / "saju_codex_addendum_v2_1" / "policies" / "recommendation_policy_v1.json"


@dataclass(slots=True)
class RecommendationGuard:
    require_structure: bool
    fallback_action: str
    ui_copy: str

    @classmethod
    def from_file(cls, path: Path = POLICY_PATH) -> "RecommendationGuard":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            require_structure=data.get("require_structure", True),
            fallback_action=data.get("fallback_when_no_structure", "suppress"),
            ui_copy=data.get("ui_copy", ""),
        )

    def decide(self, *, structure_primary: str | None) -> Dict[str, object]:
        if self.require_structure and not structure_primary:
            return {"enabled": False, "action": self.fallback_action, "copy": self.ui_copy}
        return {"enabled": True, "action": "allow", "copy": ""}
