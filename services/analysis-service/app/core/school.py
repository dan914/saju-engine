"""School profile loader"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

POLICY_PATH = Path(__file__).resolve().parents[5] / "policies" / "school_profiles_v1.json"


@dataclass(slots=True)
class SchoolProfileManager:
    profiles: Dict[str, Dict[str, object]]
    default_id: str

    @classmethod
    def load(cls) -> "SchoolProfileManager":
        with POLICY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        default_id = data.get("default_profile") or data.get("default", "practical_balanced")
        return cls(profiles=data.get("profiles", {}), default_id=default_id)

    def get_profile(self, profile_id: str | None = None) -> Dict[str, object]:
        pid = profile_id or self.default_id
        profile = self.profiles.get(pid, {})
        return {"id": pid, "notes": profile.get("notes")}
