"""School profile management for analysis interpretation styles.

Extracted from analysis-service to services/common for shared use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict

from policy_loader import resolve_policy_path

POLICY_PATH = resolve_policy_path("school_profiles_v1.json")


@dataclass(slots=True)
class SchoolProfileManager:
    """Manage school profiles for different analysis interpretation styles."""

    profiles: Dict[str, Dict[str, object]]
    default_id: str

    @classmethod
    def load(cls) -> "SchoolProfileManager":
        """Load school profiles from policy file.

        Returns:
            SchoolProfileManager instance with loaded profiles
        """
        with POLICY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        default_id = data.get("default_profile") or data.get("default", "practical_balanced")
        return cls(profiles=data.get("profiles", {}), default_id=default_id)

    def get_profile(self, profile_id: str | None = None) -> Dict[str, object]:
        """Get a specific school profile or the default.

        Args:
            profile_id: Profile ID to retrieve (None for default)

        Returns:
            Dict with keys:
                - id: str (profile identifier)
                - notes: str (profile description)
        """
        pid = profile_id or self.default_id
        profile = self.profiles.get(pid, {})
        return {"id": pid, "notes": profile.get("notes")}
