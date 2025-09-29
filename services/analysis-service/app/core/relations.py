"""Advanced relation transformations based on addendum v2 policies."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import json

POLICY_BASE = Path(__file__).resolve().parents[5]
RELATION_POLICY_V25 = POLICY_BASE / "saju_codex_v2_5_bundle" / "policies" / "relation_structure_adjust_v2_5.json"
RELATION_POLICY_V21 = POLICY_BASE / "saju_codex_addendum_v2_1" / "policies" / "relation_transform_rules_v1_1.json"
RELATION_POLICY_V2 = POLICY_BASE / "saju_codex_addendum_v2" / "policies" / "relation_transform_rules.json"
FIVE_HE_POLICY_V12 = POLICY_BASE / "saju_codex_blueprint_v2_6_SIGNED" / "policies" / "five_he_policy_v1_2.json"
FIVE_HE_POLICY_V10 = POLICY_BASE / "policies" / "five_he_policy_v1.json"
ZIXING_POLICY_PATH = POLICY_BASE / "saju_codex_addendum_v2_1" / "policies" / "zixing_rules_v1.json"


@dataclass(slots=True)
class RelationContext:
    branches: List[str]
    month_branch: str
    conflicts: Optional[List[str]] = None  # precomputed conflict indicators (e.g., chong pairs)
    branch_states: Optional[Dict[str, str]] = None
    five_he_pairs: Optional[List[Dict[str, object]]] = None
    zixing_counts: Optional[Dict[str, int]] = None


@dataclass(slots=True)
class RelationResult:
    priority_hit: Optional[str]
    transform_to: Optional[str]
    boosts: List[Dict[str, str]]
    notes: List[str]
    extras: Dict[str, object]


class RelationTransformer:
    """Evaluate relation transformations according to policy priority."""

    def __init__(self, policy: Dict[str, object]) -> None:
        self._policy = policy
        self._definitions = policy.get("definitions", {})
        self._priority = policy.get("priority", [])
        self._five_he_policy: Dict[str, object] = {}
        if FIVE_HE_POLICY_PATH.exists():
            with FIVE_HE_POLICY_PATH.open("r", encoding="utf-8") as f:
                self._five_he_policy = json.load(f)
        self._zixing_policy: Dict[str, object] = {}
        if ZIXING_POLICY_PATH.exists():
            with ZIXING_POLICY_PATH.open("r", encoding="utf-8") as f:
                self._zixing_policy = json.load(f)

    @classmethod
    def from_file(cls, path: Optional[Path] = None) -> "RelationTransformer":
        policy_path = path or (RELATION_POLICY_V25 if RELATION_POLICY_V25.exists() else (RELATION_POLICY_V21 if RELATION_POLICY_V21.exists() else RELATION_POLICY_V2))
        with policy_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def evaluate(self, ctx: RelationContext) -> RelationResult:
        extras: Dict[str, object] = {}
        priority_entry: Optional[Tuple[str, Optional[str], List[Dict[str, str]], List[str]]] = None
        for rule in self._priority:
            if rule == "sanhe_transform":
                transform = self._check_sanhe_transform(ctx)
                if transform:
                    priority_entry = ("sanhe_transform", transform, [], ["sanhe_transform"])
                    break
            elif rule == "banhe_boost":
                boosts = self._check_banhe_boost(ctx)
                if boosts:
                    extras["banhe_boost"] = boosts
                    priority_entry = ("banhe_boost", None, boosts, ["banhe_boost"])
                    break
            elif rule == "sanhui_boost":
                boosts = self._check_sanhui_boost(ctx)
                if boosts:
                    priority_entry = ("sanhui_boost", None, boosts, ["sanhui_boost"])
                    break
            elif rule == "chong":
                pair = self._check_pairs(ctx.branches, self._definitions.get("chong_pairs", []))
                if pair:
                    priority_entry = ("chong", None, [], ["chong:" + "/".join(pair)])
                    break
            elif rule == "xing_po_hai":
                continue
            elif rule == "he_nontransform":
                continue
        five_he_info = self._check_five_he(ctx)
        extras["five_he"] = five_he_info
        extras["zixing"] = self._check_zixing(ctx)

        if priority_entry:
            hit, transform_to, boosts, notes = priority_entry
            return RelationResult(priority_hit=hit, transform_to=transform_to, boosts=boosts, notes=notes, extras=extras)

        return RelationResult(priority_hit=None, transform_to=None, boosts=[], notes=[], extras=extras)

    def _check_sanhe_transform(self, ctx: RelationContext) -> Optional[str]:
        sanhe_groups: Dict[str, List[str]] = self._definitions.get("sanhe_groups", {})
        for element, group in sanhe_groups.items():
            if all(branch in ctx.branches for branch in group):
                if ctx.month_branch not in group:
                    continue
                if self._has_conflict(ctx, group):
                    continue
                return element
        return None

    def _check_sanhui_boost(self, ctx: RelationContext) -> List[Dict[str, str]]:
        boosts: List[Dict[str, str]] = []
        sanhui_groups: Dict[str, List[str]] = self._definitions.get("sanhui_groups", {})
        for season, group in sanhui_groups.items():
            if all(branch in ctx.branches for branch in group):
                boosts.append({"season": season, "element": season})
        return boosts

    @staticmethod
    def _check_pairs(branches: Iterable[str], pairs: Iterable[Iterable[str]]) -> Optional[List[str]]:
        branch_set = set(branches)
        for pair in pairs:
            if set(pair).issubset(branch_set):
                return list(pair)
        return None

    def _has_conflict(self, ctx: RelationContext, group: Iterable[str]) -> bool:
        conflicts = ctx.conflicts or []
        if conflicts:
            return True
        chong_pair = self._check_pairs(ctx.branches, self._definitions.get("chong_pairs", []))
        return chong_pair is not None
