"""Recommendation guard per policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

# Import from common package (replaces cross-service imports)
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[6] / "services" / "common"))
from policy_loader import resolve_policy_path

# Use policy loader for flexible path resolution
POLICY_PATH = resolve_policy_path("recommendation_policy_v1.json")


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
