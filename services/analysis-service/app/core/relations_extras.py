# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.common.policy_loader import load_policy_json


@dataclass
class RelationContext:
    branches: List[str]
    five_he_pairs: Optional[List[Dict[str, Any]]] = None  # [{pair:"甲己", month_support:bool, huashen_stem:bool, conflict_flags:["chong"]}]
    zixing_counts: Optional[Dict[str, int]] = None        # {"子": 2, "午": 3}
    conflicts: Optional[List[str]] = None                 # global conflict flags

class RelationAnalyzer:
    def __init__(self, policy_file: str = "relation_policy_v1.json"):
        p = load_policy_json(policy_file)
        self.policy = p
        self.five_he_cfg = p.get("five_he_policy", {})
        self.sanhe_groups = p.get("sanhe_groups", {})
        self.banhe_groups = p.get("banhe_groups", self.sanhe_groups)
        self.zx = p.get("zixing", {"min_count_medium":2, "min_count_high":3})

    def _has_conflict(self, ctx: RelationContext, extra_flags: List[str]) -> bool:
        all_flags = set(extra_flags or [])
        if ctx.conflicts: all_flags |= set(ctx.conflicts)
        # very simple: if "chong" present then conflict
        return "chong" in all_flags

    def check_five_he(self, ctx: RelationContext) -> Dict[str, Any]:
        """Validate five-he (五合) transformations using policy conditions."""
        results = []
        if not ctx.five_he_pairs:
            return {"pairs": [], "valid_count": 0}
        for info in ctx.five_he_pairs:
            cond = self.five_he_cfg
            valid = True
            if cond.get("require_month_support", False) and not info.get("month_support", False):
                valid = False
            if valid and cond.get("require_huashen_stem", False) and not info.get("huashen_stem", False):
                valid = False
            if valid and cond.get("deny_if_conflict", True) and self._has_conflict(ctx, info.get("conflict_flags", [])):
                valid = False
            results.append({"pair": info.get("pair"), "valid": bool(valid), "month_support": info.get("month_support", False)})
        return {"pairs": results, "valid_count": sum(1 for r in results if r["valid"])}

    def check_zixing(self, ctx: RelationContext) -> Dict[str, Any]:
        """Detect self-punishment (自刑): repeated same branches."""
        out = []
        counts = ctx.zixing_counts or {}
        for br, cnt in counts.items():
            if cnt >= self.zx["min_count_medium"]:
                sev = "high" if cnt >= self.zx["min_count_high"] else "medium"
                out.append({"branch": br, "count": int(cnt), "severity": sev})
        return {"zixing_detected": out, "total": len(out)}

    def check_banhe_boost(self, ctx: RelationContext) -> List[Dict[str, str]]:
        """Partial combination (半合): exactly 2 of 3 sanhe group present (blocked if conflict)."""
        if self._has_conflict(ctx, []):
            return []
        boosts = []
        for elem, group in (self.banhe_groups or {}).items():
            present = [b for b in group if b in (ctx.branches or [])]
            if len(present) == 2:
                boosts.append({"element": elem, "branches": "/".join(present)})
        return boosts

    def run(self, ctx: RelationContext) -> Dict[str, Any]:
        return {
            "five_he": self.check_five_he(ctx),
            "zixing": self.check_zixing(ctx),
            "banhe": self.check_banhe_boost(ctx)
        }
