"""
Relation Weight Evaluator v1.0

Quantifies impact_weight and confidence for detected relationships (합/충/형/해 등).
Separates detection (RelationTransformer) from validation/weighting.

Policy: policy/relation_weight_policy_v1.0.json
"""

from __future__ import annotations

# Inline signature utilities (until infra/signatures.py is created)
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from canonicaljson import encode_canonical_json
except ImportError:
    import json as json_fallback

    def encode_canonical_json(obj):
        return json_fallback.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


POLICY_VERSION = "relation_weight_v1.0.0"
TWELVE_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TEN_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# Element mappings
BRANCH_TO_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

STEM_TO_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

# Generation/destruction cycles
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
DESTRUCTS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _canonical_json(obj: Any) -> bytes:
    """RFC-8785 approximate canonical JSON serialization"""
    if isinstance(obj, dict):
        cleaned = {k: v for k, v in obj.items() if k != "policy_signature"}
        return encode_canonical_json(cleaned)
    return encode_canonical_json(obj)


def _sign_data(obj: Any) -> str:
    """Generate SHA-256 signature for canonical JSON"""
    canonical = _canonical_json(obj)
    return hashlib.sha256(canonical).hexdigest()


class RelationWeightEvaluator:
    """
    Evaluates detected relationships and assigns impact_weight and confidence
    based on contextual conditions.
    """

    def __init__(self, policy_path: Optional[str] = None):
        """
        Args:
            policy_path: Path to relation_weight_policy JSON. Defaults to policy/ directory.
        """
        if policy_path is None:
            repo_root = (
                Path(__file__).resolve().parents[4]
            )  # services/analysis-service/app/core/ -> root
            policy_path = str(repo_root / "policy" / "relation_weight_policy_v1.0.json")

        self.policy = self._load_policy(policy_path)
        self.policy_map = {r["relation"]: r for r in self.policy["relations"]}

    @staticmethod
    def _load_policy(path: str) -> Dict[str, Any]:
        """Load and validate policy JSON"""
        with open(path, encoding="utf-8") as f:
            policy = json.load(f)

        # Validate version
        if policy.get("policy_version") != POLICY_VERSION:
            raise ValueError(
                f"Policy version mismatch: expected {POLICY_VERSION}, got {policy.get('policy_version')}"
            )

        return policy

    def evaluate(
        self, pairs_detected: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate detected relation pairs with contextual weighting.

        Args:
            pairs_detected: List of detected relations from RelationTransformer
                [{"type": "sanhe", "a": "申子辰", "b": "水", "formed": true, ...}, ...]
            context: Global context
                {
                    "heavenly": ["庚", "乙", "乙", "辛"],
                    "earthly": ["申", "子", "辰", "巳"],
                    "month_branch": "子",
                    "season_element": "水",  # optional, derived from month_branch if missing
                    "tonggen_support": {"木": true, "水": true, ...},  # optional
                    "strong_combos": [{"type": "sanhe", "branches": ["申", "子", "辰"]}]  # optional
                }

        Returns:
            {
                "policy_version": "1.0.0",
                "policy_signature": "<64hex>",
                "items": [...],
                "summary": {...}
            }
        """
        # Prepare context
        ctx = self._prepare_context(context)

        # Evaluate each detected pair
        items = []
        for pair in pairs_detected:
            evaluated = self._evaluate_single(pair, ctx)
            items.append(evaluated)

        # Generate summary
        summary = self._generate_summary(items)

        # Build output
        output = {
            "policy_version": POLICY_VERSION,
            "policy_signature": self.policy.get("policy_signature", "UNSIGNED"),
            "items": items,
            "summary": summary,
        }

        return output

    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and enrich context"""
        ctx = context.copy()

        # Derive season_element from month_branch if missing
        if "season_element" not in ctx and "month_branch" in ctx:
            ctx["season_element"] = BRANCH_TO_ELEMENT.get(ctx["month_branch"], "")

        # Build adjacent pairs if not provided
        if "adjacent_branch_pairs" not in ctx and "earthly" in ctx:
            earthly = ctx["earthly"]
            ctx["adjacent_branch_pairs"] = {
                (earthly[0], earthly[1]),  # year-month
                (earthly[1], earthly[2]),  # month-day
                (earthly[2], earthly[3]),  # day-hour
            }

        if "adjacent_stem_pairs" not in ctx and "heavenly" in ctx:
            heavenly = ctx["heavenly"]
            ctx["adjacent_stem_pairs"] = {
                (heavenly[0], heavenly[1]),
                (heavenly[1], heavenly[2]),
                (heavenly[2], heavenly[3]),
            }

        # Default empty strong combos
        if "strong_combos" not in ctx:
            ctx["strong_combos"] = []

        # Default empty tonggen support
        if "tonggen_support" not in ctx:
            ctx["tonggen_support"] = {}

        return ctx

    def _evaluate_single(self, pair: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single detected relation pair"""
        rel_type = pair.get("type", "")
        policy = self.policy_map.get(rel_type)

        if not policy:
            # Unknown relation type, return as-is with default weight
            return {
                **pair,
                "impact_weight": 0.0,
                "confidence": 0.0,
                "conditions_met": [],
                "missing_conditions": [],
                "explain": f"Unknown relation type: {rel_type}",
            }

        # Start with base weight and confidence
        weight = policy["base_weight"]
        confidence = policy["confidence"]
        conditions_met = []
        missing_conditions = []

        # Check strict mode
        if policy.get("strict_mode_required") and not pair.get("formed", True):
            # Strict mode violation - set weight to 0
            weight = 0.0
            missing_conditions.append("formed_incomplete")

        # Evaluate conditions based on relation type
        if rel_type == "sanhe":
            weight, conditions_met, missing_conditions = self._evaluate_sanhe(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "liuhe":
            weight, conditions_met, missing_conditions = self._evaluate_liuhe(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "ganhe":
            weight, conditions_met, missing_conditions = self._evaluate_ganhe(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "chong":
            weight, conditions_met, missing_conditions = self._evaluate_chong(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "xing":
            weight, conditions_met, missing_conditions = self._evaluate_xing(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "hai":
            weight, conditions_met, missing_conditions = self._evaluate_hai(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )
        elif rel_type == "yuanjin":
            weight, conditions_met, missing_conditions = self._evaluate_yuanjin(
                pair, ctx, policy, weight, conditions_met, missing_conditions
            )

        # Clamp weight to [0, 1]
        impact_weight = max(0.0, min(1.0, weight))

        # Adjust confidence based on conditions
        confidence_adj = confidence + 0.05 * len(conditions_met) - 0.05 * len(missing_conditions)
        confidence_final = max(0.0, min(1.0, confidence_adj))

        # Build output
        result = {
            **pair,
            "impact_weight": round(impact_weight, 2),
            "confidence": round(confidence_final, 2),
            "conditions_met": conditions_met,
            "missing_conditions": missing_conditions,
        }

        # Add hua field for ganhe if applicable
        if rel_type == "ganhe" and policy.get("flags", {}).get("emit_hua_field"):
            result["hua"] = "season_supports_result" in conditions_met

        return result

    def _evaluate_sanhe(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 삼합 (sanhe) conditions"""
        modifiers = policy["modifiers"]

        # pivot_month: 월지가 삼합 구성원
        if self._check_pivot_month_sanhe(pair, ctx):
            weight += modifiers["pivot_month"]
            met.append("pivot_month")
        else:
            miss.append("pivot_month")

        # month_adjacent: 월지와 다른 구성원이 인접
        if self._check_month_adjacent_branch(pair, ctx):
            weight += modifiers["month_adjacent"]
            met.append("month_adjacent")
        else:
            miss.append("month_adjacent")

        # tonggen_or_season_support
        if self._check_element_support(pair.get("b"), ctx):
            weight += modifiers["tonggen_or_season_support"]
            met.append("tonggen_or_season_support")

        # blocked_by_chong_hai
        if self._check_blocked_by_chong_hai(pair, ctx):
            weight += modifiers["blocked_by_chong_hai"]  # negative modifier
            miss.append("blocked_by_chong_hai")

        # incomplete_half_combo (already handled by strict mode, but record)
        if not pair.get("formed", True):
            weight += modifiers["incomplete_half_combo"]  # negative
            miss.append("incomplete_half_combo")

        return weight, met, miss

    def _evaluate_liuhe(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 육합 (liuhe) conditions"""
        modifiers = policy["modifiers"]

        # on_day_branch
        if self._check_on_day_branch(pair, ctx):
            weight += modifiers["on_day_branch"]
            met.append("on_day_branch")

        # broken_by_chong
        if self._check_broken_by_chong(pair, ctx):
            weight += modifiers["broken_by_chong"]  # negative
            miss.append("broken_by_chong")

        # inside_strong_combo
        if self._check_inside_strong_combo(pair, ctx):
            weight += modifiers["inside_strong_combo"]  # negative
            miss.append("inside_strong_combo")

        return weight, met, miss

    def _evaluate_ganhe(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 간합 (ganhe) conditions"""
        modifiers = policy["modifiers"]

        # adjacent_stems
        if self._check_adjacent_stems(pair, ctx):
            weight += modifiers["adjacent_stems"]
            met.append("adjacent_stems")
        else:
            # non_adjacent
            weight += modifiers["non_adjacent"]  # negative
            miss.append("non_adjacent")

        # season_supports_result
        if self._check_season_supports_result(pair, ctx):
            weight += modifiers["season_supports_result"]
            met.append("season_supports_result")
        else:
            # Check for season_conflict
            if self._check_season_conflict(pair, ctx):
                weight += modifiers["season_conflict"]  # negative
                miss.append("season_conflict")

        return weight, met, miss

    def _evaluate_chong(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 충 (chong) conditions"""
        modifiers = policy["modifiers"]

        # pivot_month
        if self._check_pivot_month_branch(pair, ctx):
            weight += modifiers["pivot_month"]
            met.append("pivot_month")

        # buffered_by_strong_combo
        if self._check_buffered_by_strong_combo(pair, ctx):
            weight += modifiers["buffered_by_strong_combo"]  # negative
            miss.append("buffered_by_strong_combo")

        # neutralized_by_he (simplified - check if any he exists on same branches)
        if self._check_neutralized_by_he(pair, ctx):
            weight += modifiers["neutralized_by_he"]  # negative
            miss.append("neutralized_by_he")

        return weight, met, miss

    def _evaluate_xing(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 형 (xing) conditions"""
        modifiers = policy["modifiers"]

        # Check if triplet xing (寅巳申 or 丑戌未)
        if self._check_full_triplet_strict(pair, ctx):
            weight += modifiers["full_triplet_strict"]
            met.append("full_triplet_strict")

        # inside_combo
        if self._check_inside_strong_combo(pair, ctx):
            weight += modifiers["inside_combo"]  # negative
            miss.append("inside_combo")

        return weight, met, miss

    def _evaluate_hai(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 해 (hai) conditions"""
        modifiers = policy["modifiers"]

        # inside_combo
        if self._check_inside_strong_combo(pair, ctx):
            weight += modifiers["inside_combo"]  # negative
            miss.append("inside_combo")

        return weight, met, miss

    def _evaluate_yuanjin(self, pair, ctx, policy, weight, met, miss):
        """Evaluate 원진 (yuanjin) conditions"""
        modifiers = policy["modifiers"]

        # on_spouse_palace (day branch)
        if self._check_on_day_branch(pair, ctx):
            weight += modifiers["on_spouse_palace"]
            met.append("on_spouse_palace")

        return weight, met, miss

    # Condition check helpers

    def _check_pivot_month_sanhe(self, pair: Dict, ctx: Dict) -> bool:
        """Check if month_branch is in sanhe triplet"""
        month_branch = ctx.get("month_branch", "")
        a = pair.get("a", "")
        # a should be triplet string like "申子辰"
        return month_branch in a

    def _check_pivot_month_branch(self, pair: Dict, ctx: Dict) -> bool:
        """Check if month_branch is in pair (for chong, etc.)"""
        month_branch = ctx.get("month_branch", "")
        a = pair.get("a", "")
        b = pair.get("b", "")
        return month_branch == a or month_branch == b

    def _check_month_adjacent_branch(self, pair: Dict, ctx: Dict) -> bool:
        """Check if month_branch and one of pair members are adjacent"""
        month_branch = ctx.get("month_branch", "")
        adjacent_pairs = ctx.get("adjacent_branch_pairs", set())

        a = pair.get("a", "")
        # For sanhe, a is triplet string - extract branches
        if len(a) == 3:
            branches = [a[0], a[1], a[2]]
        else:
            branches = [a, pair.get("b", "")]

        for b in branches:
            if (month_branch, b) in adjacent_pairs or (b, month_branch) in adjacent_pairs:
                return True
        return False

    def _check_element_support(self, element: Optional[str], ctx: Dict) -> bool:
        """Check if element has tonggen or season support"""
        if not element:
            return False

        # Check tonggen_support
        if ctx.get("tonggen_support", {}).get(element):
            return True

        # Check season support (season element generates target element)
        season_elem = ctx.get("season_element", "")
        if season_elem and GENERATES.get(season_elem) == element:
            return True
        if season_elem == element:
            return True

        return False

    def _check_blocked_by_chong_hai(self, pair: Dict, ctx: Dict) -> bool:
        """Check if any member of combo is blocked by chong/hai"""
        # Simplified - would need full pairs_detected to check
        # For now, return False (assume no blocking)
        return False

    def _check_on_day_branch(self, pair: Dict, ctx: Dict) -> bool:
        """Check if relation occurs on day branch"""
        earthly = ctx.get("earthly", [])
        if len(earthly) < 3:
            return False
        day_branch = earthly[2]

        a = pair.get("a", "")
        b = pair.get("b", "")
        return day_branch == a or day_branch == b

    def _check_broken_by_chong(self, pair: Dict, ctx: Dict) -> bool:
        """Check if liuhe is broken by chong"""
        # Simplified - would need chong pairs to check
        return False

    def _check_inside_strong_combo(self, pair: Dict, ctx: Dict) -> bool:
        """Check if relation occurs inside a strong combo (sanhe/fanghe)"""
        strong_combos = ctx.get("strong_combos", [])

        a = pair.get("a", "")
        b = pair.get("b", "")

        for combo in strong_combos:
            if combo.get("type") == "sanhe":
                branches = combo.get("branches", [])
                if a in branches or b in branches:
                    return True

        return False

    def _check_adjacent_stems(self, pair: Dict, ctx: Dict) -> bool:
        """Check if ganhe occurs between adjacent stems"""
        adjacent_pairs = ctx.get("adjacent_stem_pairs", set())
        a = pair.get("a", "")
        b = pair.get("b", "")

        return (a, b) in adjacent_pairs or (b, a) in adjacent_pairs

    def _check_season_supports_result(self, pair: Dict, ctx: Dict) -> bool:
        """Check if season supports ganhe result element"""
        result_elem = pair.get("element", "")
        season_elem = ctx.get("season_element", "")

        if not result_elem or not season_elem:
            return False

        # Same element or generates result
        if season_elem == result_elem:
            return True
        if GENERATES.get(season_elem) == result_elem:
            return True

        return False

    def _check_season_conflict(self, pair: Dict, ctx: Dict) -> bool:
        """Check if season conflicts with ganhe result"""
        result_elem = pair.get("element", "")
        season_elem = ctx.get("season_element", "")

        if not result_elem or not season_elem:
            return False

        # Season destructs result
        return DESTRUCTS.get(season_elem) == result_elem

    def _check_buffered_by_strong_combo(self, pair: Dict, ctx: Dict) -> bool:
        """Check if chong target is buffered by strong combo"""
        return self._check_inside_strong_combo(pair, ctx)

    def _check_neutralized_by_he(self, pair: Dict, ctx: Dict) -> bool:
        """Check if chong is neutralized by he"""
        # Simplified
        return False

    def _check_full_triplet_strict(self, pair: Dict, ctx: Dict) -> bool:
        """Check if xing is full triplet with month pivot + adjacent"""
        a = pair.get("a", "")

        # Check if triplet xing (寅巳申 or 丑戌未)
        if a not in ["寅巳申", "丑戌未"]:
            return False

        # Check month pivot
        if not self._check_pivot_month_sanhe(pair, ctx):
            return False

        # Check month adjacent
        if not self._check_month_adjacent_branch(pair, ctx):
            return False

        return True

    def _generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        by_type = {}

        for item in items:
            rel_type = item.get("type", "unknown")
            if rel_type not in by_type:
                by_type[rel_type] = {"count": 0, "total_weight": 0.0}

            by_type[rel_type]["count"] += 1
            by_type[rel_type]["total_weight"] += item.get("impact_weight", 0.0)

        # Calculate averages
        summary_by_type = {}
        for rel_type, stats in by_type.items():
            avg_weight = stats["total_weight"] / stats["count"] if stats["count"] > 0 else 0.0
            summary_by_type[rel_type] = {
                "count": stats["count"],
                "avg_weight": round(avg_weight, 2),
            }

        # Ensure all 7 types are in summary
        for rel_type in ["sanhe", "liuhe", "ganhe", "chong", "xing", "hai", "yuanjin"]:
            if rel_type not in summary_by_type:
                summary_by_type[rel_type] = {"count": 0, "avg_weight": 0.0}

        return {"total": len(items), "by_type": summary_by_type}


def evaluate_relation_weights(
    pairs_detected: List[Dict[str, Any]], context: Dict[str, Any], policy_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to evaluate relation weights.

    Args:
        pairs_detected: List of detected relations from RelationTransformer
        context: Global context (heavenly, earthly, month_branch, etc.)
        policy_path: Optional path to policy JSON

    Returns:
        Evaluation results with impact_weight, confidence, conditions for each relation
    """
    evaluator = RelationWeightEvaluator(policy_path)
    return evaluator.evaluate(pairs_detected, context)
