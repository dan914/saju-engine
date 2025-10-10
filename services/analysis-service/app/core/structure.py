"""Structure detection according to structure_rules_v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Import from common package (replaces cross-service imports)
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[6] / "services" / "common"))
from policy_loader import resolve_policy_path


# Use policy loader for flexible path resolution with version fallback
def _resolve_with_fallback(primary: str, *fallbacks: str) -> Path:
    """Try primary policy file, fall back to older versions if not found."""
    try:
        return resolve_policy_path(primary)
    except FileNotFoundError:
        for fb in fallbacks:
            try:
                return resolve_policy_path(fb)
            except FileNotFoundError:
                continue
        # If all fail, raise with primary filename
        raise FileNotFoundError(f"Policy file not found: {primary} (tried fallbacks: {fallbacks})")


STRUCTURE_POLICY_PATH = _resolve_with_fallback(
    "structure_rules_v2_6.json",
    "structure_rules_v2_5.json",
    "structure_rules_v1.json"
)


@dataclass(slots=True)
class StructureContext:
    scores: Dict[str, int]


@dataclass(slots=True)
class StructureResult:
    primary: Optional[str]
    confidence: str
    candidates: List[Dict[str, object]]


class StructureDetector:
    def __init__(self, policy: Dict[str, object]) -> None:
        self._policy = policy
        self._structures = policy.get("structures", [])
        thresholds = policy.get("thresholds", {})
        guards = policy.get("guards", {})
        self._threshold_primary = thresholds.get("primary") or guards.get("resolved_min", 10)
        self._threshold_candidate = thresholds.get("candidate") or guards.get("proto_min", 6)
        self._tie_delta = guards.get("tie_delta")

    @classmethod
    def from_file(cls, path: Path | None = None) -> "StructureDetector":
        policy_path = path or STRUCTURE_POLICY_PATH
        with policy_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def evaluate(self, ctx: StructureContext) -> StructureResult:
        scored = [(structure, ctx.scores.get(structure, 0)) for structure in self._structures]
        scored = [item for item in scored if item[1] > 0]
        scored.sort(key=lambda item: item[1], reverse=True)

        candidates: List[Dict[str, object]] = []
        for structure, score in scored:
            if score >= self._threshold_candidate:
                candidates.append(
                    {
                        "type": structure,
                        "score": score,
                        "reasons": [],
                    }
                )

        primary = None
        confidence = "none"
        if scored:
            top_structure, top_score = scored[0]
            second_score = scored[1][1] if len(scored) > 1 else None
            if top_score >= self._threshold_primary:
                if (
                    self._tie_delta
                    and second_score is not None
                    and top_score - second_score < self._tie_delta
                ):
                    confidence = "low"
                else:
                    primary = top_structure
                    if top_score >= self._threshold_primary + 5:
                        confidence = "high"
                    elif top_score >= self._threshold_primary + 2:
                        confidence = "mid"
                    else:
                        confidence = "low"
            elif top_score >= self._threshold_candidate:
                confidence = "low"

        return StructureResult(primary=primary, confidence=confidence, candidates=candidates)
