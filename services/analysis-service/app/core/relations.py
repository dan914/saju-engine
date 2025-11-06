"""Advanced relation transformations based on addendum v2 policies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from saju_common.policy_loader import resolve_policy_path


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


# Note: v2_5 has incompatible schema (matrix-based), skip to v1_1
RELATION_POLICY_PATH = _resolve_with_fallback(
    "relation_transform_rules_v1_1.json", "relation_transform_rules.json"
)

# Optional policy files - may not exist
try:
    FIVE_HE_POLICY_PATH = _resolve_with_fallback(
        "five_he_policy_v1_2.json", "five_he_policy_v1.json"
    )
except FileNotFoundError:
    FIVE_HE_POLICY_PATH = None

try:
    ZIXING_POLICY_PATH = resolve_policy_path("zixing_rules_v1.json")
except FileNotFoundError:
    ZIXING_POLICY_PATH = None


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
        if FIVE_HE_POLICY_PATH is not None:
            with FIVE_HE_POLICY_PATH.open("r", encoding="utf-8") as f:
                self._five_he_policy = json.load(f)
        self._zixing_policy: Dict[str, object] = {}
        if ZIXING_POLICY_PATH is not None:
            with ZIXING_POLICY_PATH.open("r", encoding="utf-8") as f:
                self._zixing_policy = json.load(f)

    @classmethod
    def from_file(cls, path: Optional[Path] = None) -> "RelationTransformer":
        policy_path = path or RELATION_POLICY_PATH
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
            return RelationResult(
                priority_hit=hit,
                transform_to=transform_to,
                boosts=boosts,
                notes=notes,
                extras=extras,
            )

        return RelationResult(
            priority_hit=None, transform_to=None, boosts=[], notes=[], extras=extras
        )

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
    def _check_pairs(
        branches: Iterable[str], pairs: Iterable[Iterable[str]]
    ) -> Optional[List[str]]:
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

    def _check_five_he(self, ctx: RelationContext) -> Dict[str, object]:
        """
        Check five-he (五合) transformation conditions.

        Returns dict with transformation info based on five_he_policy.
        If ctx.five_he_pairs is provided, validates against policy conditions.
        """
        if not self._five_he_policy:
            return {}

        five_he_pairs = ctx.five_he_pairs or []
        if not five_he_pairs:
            return {}

        conditions = self._five_he_policy.get("conditions", {})
        results = []

        for pair_info in five_he_pairs:
            pair = pair_info.get("pair", "")
            month_support = pair_info.get("month_support", False)
            huashen_present = pair_info.get("huashen_present", False)
            has_conflict = pair_info.get("has_conflict", False)

            # Check policy conditions
            valid = True
            if conditions.get("require_month_support") and not month_support:
                valid = False
            if conditions.get("require_huashen_stem") and not huashen_present:
                valid = False
            if conditions.get("deny_if_conflict") and has_conflict:
                valid = False

            results.append(
                {
                    "pair": pair,
                    "valid": valid,
                    "month_support": month_support,
                    "huashen_present": huashen_present,
                }
            )

        return {"pairs": results, "scope": self._five_he_policy.get("transform_scope", "none")}

    def _check_zixing(self, ctx: RelationContext) -> Dict[str, object]:
        """
        Check zixing (自刑, self-punishment) conditions.

        Returns dict with zixing counts and severity based on zixing_policy.
        If ctx.zixing_counts is provided, validates against policy rules.
        """
        if not self._zixing_policy:
            return {}

        zixing_counts = ctx.zixing_counts or {}
        if not zixing_counts:
            return {}

        results = []

        for branch, count in zixing_counts.items():
            # Zixing typically requires 2+ of same branch
            if count >= 2:
                severity = "high" if count >= 3 else "medium"
                results.append({"branch": branch, "count": count, "severity": severity})

        return {"zixing_detected": results, "total_branches": len(results)}

    def _check_banhe_boost(self, ctx: RelationContext) -> List[Dict[str, str]]:
        """
        Check banhe (半合, directional combination) boost conditions.

        Banhe requires 2 of 3 branches from a directional group.
        E.g., 申子 (2 of 申子辰 water trio) boosts water element.

        Falls back to sanhe_groups if banhe_groups not defined.
        Blocked if chong (conflict) exists.
        """
        # If there's a chong, don't apply banhe
        if self._has_conflict(ctx, []):
            return []

        boosts: List[Dict[str, str]] = []

        # Try banhe_groups first, fall back to sanhe_groups
        banhe_groups = self._definitions.get("banhe_groups")
        if not banhe_groups:
            banhe_groups = self._definitions.get("sanhe_groups", {})

        for element, group in banhe_groups.items():
            # Check if exactly 2 branches present (not all 3 = that's sanhe)
            present = [b for b in group if b in ctx.branches]
            if len(present) == 2:
                boosts.append({"element": element, "branches": "/".join(present), "type": "banhe"})

        return boosts
