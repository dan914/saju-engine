"""Determine 旺/相/休/囚/死 states for elements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

SEASONS_WANG_MAP_PATH = (
    Path(__file__).resolve().parents[4] / "policies" / "seasons_wang_map_v2.json"
)


@dataclass(slots=True)
class WangStateMapper:
    """Load and provide wang state lookups."""

    mapping: Dict[str, Dict[str, str]]

    @classmethod
    def from_file(cls, path: Path = SEASONS_WANG_MAP_PATH) -> "WangStateMapper":
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)["map"]
        return cls(mapping=payload)

    def state_for(self, branch: str, element: str) -> str:
        for branches, states in self.mapping.items():
            if branch in branches:
                return states[element]
        raise KeyError(f"Branch {branch} not found in seasons_wang_map")
