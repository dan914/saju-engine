"""Structure detection according to structure_rules_v1."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json

POLICY_BASE = Path(__file__).resolve().parents[5]
STRUCTURE_POLICY_V26 = POLICY_BASE / "saju_codex_blueprint_v2_6_SIGNED" / "policies" / "structure_rules_v2_6.json"
STRUCTURE_POLICY_V25 = POLICY_BASE / "saju_codex_v2_5_bundle" / "policies" / "structure_rules_v2_5.json"
STRUCTURE_POLICY_V1 = POLICY_BASE / "saju_codex_addendum_v2" / "policies" / "structure_rules_v1.json"


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
        policy_path = path or (STRUCTURE_POLICY_V26 if STRUCTURE_POLICY_V26.exists() else (STRUCTURE_POLICY_V25 if STRUCTURE_POLICY_V25.exists() else STRUCTURE_POLICY_V1))
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
                candidates.append({
                    "type": structure,
                    "score": score,
                    "reasons": [],
                })

        primary = None
        confidence = "none"
        if scored:
            top_structure, top_score = scored[0]
            second_score = scored[1][1] if len(scored) > 1 else None
            if top_score >= self._threshold_primary:
                if self._tie_delta and second_score is not None and top_score - second_score < self._tie_delta:
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
