"""Strength evaluation for analysis service using strength_adjust_v1_3.json policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

# Policy file paths
ZANGGAN_PATH = Path(__file__).resolve().parents[4] / "rulesets" / "zanggan_table.json"
STRENGTH_ADJUST_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_batch_all_v2_6_signed"
    / "policies"
    / "strength_adjust_v1_3.json"
)
SEASONS_WANG_MAP_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_batch_all_v2_6_signed"
    / "policies"
    / "seasons_wang_map_v2.json"
)
ROOT_SEAL_POLICY_PATH = (
    Path(__file__).resolve().parents[4] / "policies" / "root_seal_policy_v2_3.json"
)

# Element mapping for stems
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


@dataclass(slots=True)
class WangStateMapper:
    """Map branch and element to wang state (旺/相/休/囚/死)."""

    mapping: Dict[str, Dict[str, str]]

    @classmethod
    def from_file(cls, path: Path = SEASONS_WANG_MAP_PATH) -> "WangStateMapper":
        """Load seasons wang map from JSON file."""
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(mapping=data.get("map", {}))

    def state_for(self, branch: str, element: str) -> str:
        """Get wang state for given branch and element."""
        if branch in self.mapping:
            return self.mapping[branch].get(element, "休")
        raise KeyError(f"Branch {branch} not found in seasons_wang_map")


@dataclass(slots=True)
class StrengthEvaluator:
    """Evaluate day master strength using strength_adjust_v1_3.json policy."""

    seasonal_state_weights: Dict[str, int]
    month_stem_adjust: Dict[str, float]
    grading_tiers: List[Dict[str, object]]
    root_norm: Dict[str, int]
    seal_norm: Dict[str, int]
    zanggan: Dict[str, List[str]]
    wang_mapper: WangStateMapper
    root_seal_policy: Dict[str, object]

    @classmethod
    def from_files(cls) -> "StrengthEvaluator":
        """Load all policy files and create evaluator instance."""
        # Load strength_adjust_v1_3.json
        with STRENGTH_ADJUST_PATH.open("r", encoding="utf-8") as f:
            strength_policy = json.load(f)

        # Load zanggan table
        with ZANGGAN_PATH.open("r", encoding="utf-8") as f:
            zanggan_data = json.load(f)

        # Load root/seal policy
        with ROOT_SEAL_POLICY_PATH.open("r", encoding="utf-8") as f:
            root_seal_policy = json.load(f)

        # Create wang mapper
        wang_mapper = WangStateMapper.from_file()

        return cls(
            seasonal_state_weights=strength_policy["seasonal_state_weights"],
            month_stem_adjust=strength_policy["month_stem_adjust"],
            grading_tiers=strength_policy["grading"]["tiers"],
            root_norm=strength_policy["root_norm"],
            seal_norm=strength_policy["seal_norm"],
            zanggan=zanggan_data["data"],
            wang_mapper=wang_mapper,
            root_seal_policy=root_seal_policy,
        )

    def score_month_state(self, month_branch: str, day_stem: str) -> int:
        """Calculate score based on day stem's state in month branch."""
        day_element = STEM_TO_ELEMENT[day_stem]
        state = self.wang_mapper.state_for(month_branch, day_element)
        return self.seasonal_state_weights.get(state, 0)

    def score_branch_roots(
        self, day_stem: str, day_branch: str, other_branches: Iterable[str]
    ) -> int:
        """Score root strength from hidden stems in branches.

        Uses root_seal_policy_v2_3.json scoring:
        - main (primary hidden stem): 5 points
        - sub (secondary hidden stem): 3 points
        - minor (tertiary hidden stem): 0 points
        - month_bonus: +2 if in month branch
        - sub_cap_per_branch: max 1 sub-level root per branch
        """
        scoring = self.root_seal_policy["root_scoring"]
        total = 0

        # Score day branch
        day_hidden = self.zanggan.get(day_branch, [])
        if day_stem in day_hidden:
            idx = day_hidden.index(day_stem)
            if idx == 0:  # main
                total += scoring["main"]
            elif idx == 1:  # sub
                total += scoring["sub"]
            # minor (idx >= 2) gets 0 points

        # Score other branches
        for branch in other_branches:
            if branch == day_branch:
                continue
            hidden = self.zanggan.get(branch, [])
            if day_stem in hidden:
                idx = hidden.index(day_stem)
                if idx == 0:  # main
                    total += scoring["main"]
                    # Month bonus if this is the month branch
                    # (caller should ensure month branch is in other_branches)
                    total += scoring.get("month_bonus", 0)
                elif idx == 1:  # sub
                    # Apply sub_cap_per_branch limit
                    total += min(scoring["sub"], scoring.get("sub_cap_per_branch", 1))
                # minor gets 0

        return total

    def score_stem_visible(self, visible_counts: Dict[str, int]) -> int:
        """Score visible stems that support day master.

        visible_counts keys: bi_jie (比劫), yin (印), shi_shang (食伤), etc.
        """
        # Based on strength_criteria_v1.json weights
        weights = {
            "bi_jie": 8,  # Same element stems (support)
            "yin": 10,  # Seal stems (strong support)
            "shi_shang": 6,  # Output stems (weak drain)
            "cai": 6,  # Wealth stems (drain)
            "guan": 6,  # Officer stems (counter)
        }
        total = 0
        for category, count in visible_counts.items():
            weight = weights.get(category, 0)
            total += weight * count
        return total

    def score_combo_clash(self, combos: Dict[str, int]) -> int:
        """Score combinations and clashes affecting strength.

        combos keys: sanhe, liuhe, chong, xing, po, hai
        """
        # Based on strength_criteria_v1.json
        weights = {
            "sanhe": 6,  # Three harmony (boost)
            "liuhe": 4,  # Six harmony (small boost)
            "chong": -8,  # Clash (weakening)
            "xing": -4,  # Punishment (weakening)
            "po": -4,  # Breaking (weakening)
            "hai": -4,  # Harm (weakening)
        }
        total = 0
        for combo_type, count in combos.items():
            weight = weights.get(combo_type, 0)
            total += weight * count
        return total

    def calculate_month_stem_effect(self, month_stem_relation: str, base_score: int) -> int:
        """Calculate month stem adjustment based on its relation to day master.

        month_stem_relation: 'counter', 'leak', 'assist', or 'none'
        """
        adjust = self.month_stem_adjust
        cap = adjust.get("cap_abs", 0.15)

        relation_pct = {
            "counter": adjust.get("counter", -0.15),
            "leak": adjust.get("leak", -0.1),
            "assist": adjust.get("assist", 0.1),
            "none": adjust.get("none", 0.0),
        }

        pct = relation_pct.get(month_stem_relation, 0.0)
        # Clamp to cap
        pct = max(-cap, min(cap, pct))

        return int(abs(base_score) * pct)

    def compute_wealth_location_bonus(
        self, wealth_hits: Iterable[Dict[str, str]] | None, month_stem_exposed: bool = False
    ) -> tuple[float, List[Dict[str, object]]]:
        """Calculate wealth location bonus from root_seal_policy_v2_3.json."""
        policy = self.root_seal_policy.get("wealth_location_bonus", {})
        if not policy.get("enabled", False):
            return 0.0, []

        min_level = policy.get("min_level", "sub")
        level_order = {"main": 2, "sub": 1, "minor": 0}
        min_rank = level_order.get(min_level, 1)
        weights = policy.get("weights", {})
        cap_total = policy.get("cap_total", 2.0)

        total = 0.0
        log: List[Dict[str, object]] = []

        for item in wealth_hits or []:
            slot = item.get("slot")  # month_branch, day_branch, hour_branch, etc.
            level = item.get("level", "minor")

            if level_order.get(level, 0) < min_rank:
                continue

            weight_key = f"{slot}_branch"
            weight = weights.get(weight_key)
            if weight:
                total += weight
                log.append({"branch": slot, "level": level, "weight_applied": weight})

        # Add month stem exposed bonus
        if month_stem_exposed and policy.get("month_stem_exposed_bonus"):
            bonus = policy["month_stem_exposed_bonus"]
            total += bonus
            log.append({"month_stem_exposed": True, "bonus_applied": bonus})

        # Apply cap
        if total > cap_total:
            total = cap_total

        return total, log

    def evaluate_seal_validity(
        self,
        wealth_root_score: int,
        seal_root_score: int,
        wealth_bonus: float,
        wealth_month_state: str | None = None,
        wealth_seal_branch_conflict: bool = False,
        officer_root_score: int = 0,
        officer_stem_exposed: bool = False,
        no_output_counterbalance: bool = True,
    ) -> Dict[str, object]:
        """Check if seal is broken by wealth or suppressed by officer."""
        validity = {
            "seal_level": "full",
            "broken_by_wealth": False,
            "suppressed_by_officer_killer": False,
        }

        rules = self.root_seal_policy.get("validity", {})

        # Check wealth breaks seal
        wealth_rule = rules.get("wealth_breaks_seal")
        if wealth_rule:
            diff = (wealth_root_score + wealth_bonus) - seal_root_score
            if diff >= 2:
                # Check additional conditions
                conditions_met = True
                for cond in wealth_rule.get("and_also", []):
                    if "or" in cond:
                        or_met = False
                        for option in cond["or"]:
                            if (
                                "wealth_month_state_in" in option
                                and wealth_month_state in option["wealth_month_state_in"]
                            ):
                                or_met = True
                            if (
                                option.get("wealth_seal_branch_conflict")
                                and wealth_seal_branch_conflict
                            ):
                                or_met = True
                        conditions_met = or_met
                        if not conditions_met:
                            break

                if conditions_met:
                    validity["seal_level"] = "none"
                    validity["broken_by_wealth"] = True

        # Check officer suppresses seal
        officer_rule = rules.get("officer_suppresses_seal")
        if officer_rule and validity["seal_level"] != "none":
            if officer_root_score >= 5 and officer_stem_exposed and no_output_counterbalance:
                validity["seal_level"] = "partial"
                validity["suppressed_by_officer_killer"] = True

        return validity

    def determine_grade(self, total: float) -> tuple[str, str]:
        """Determine grade code and grade name from total score.

        Returns: (grade_code, grade_name)
        grade_code: one of "신강", "편강", "중화", "편약", "신약"
        grade_name: same as grade_code (Korean names)
        """
        # Clamp total to [0, 100]
        clamped = max(0, min(100, total))

        # Find matching tier (sorted by min descending)
        for tier in self.grading_tiers:
            if clamped >= tier["min"]:
                grade_name = tier["name"]
                return grade_name, grade_name

        # Default to weakest
        return "신약", "신약"

    def evaluate(
        self,
        *,
        month_branch: str,
        day_pillar: str,
        branch_roots: Iterable[str],
        visible_counts: Dict[str, int],
        combos: Dict[str, int],
        wealth_hits: Iterable[Dict[str, str]] | None = None,
        month_stem_exposed: bool = False,
        wealth_root_score: int = 0,
        seal_root_score: int = 0,
        wealth_month_state: str | None = None,
        wealth_seal_branch_conflict: bool = False,
        officer_root_score: int = 0,
        officer_stem_exposed: bool = False,
        no_output_counterbalance: bool = True,
    ) -> Dict[str, object]:
        """Evaluate day master strength and return all score components.

        Returns dict matching StrengthDetails model with fields:
        - month_state: int
        - branch_root: int
        - stem_visible: int
        - combo_clash: int
        - season_adjust: int
        - month_stem_effect: int
        - wealth_location_bonus_total: float
        - wealth_location_hits: List[Dict]
        - total: float
        - grade_code: str
        - grade: str
        - seal_validity: Dict
        """
        day_stem = day_pillar[0]
        day_branch = day_pillar[1]

        # Calculate each component
        month_state = self.score_month_state(month_branch, day_stem)
        branch_root = self.score_branch_roots(day_stem, day_branch, branch_roots)
        stem_visible = self.score_stem_visible(visible_counts)
        combo_clash = self.score_combo_clash(combos)

        # Season adjust based on day stem element and month branch season
        season_adjust = self._compute_season_adjust(day_stem, month_branch)

        # Month stem effect based on ten gods relation (if month_stem provided)
        month_stem = locals().get("month_stem")  # Get from parameters if added
        month_stem_effect = (
            self._compute_month_stem_effect(day_stem, month_stem) if month_stem else 0
        )

        # Wealth location bonus
        wealth_bonus, wealth_hits_log = self.compute_wealth_location_bonus(
            wealth_hits, month_stem_exposed
        )

        # Calculate total
        total = float(
            month_state
            + branch_root
            + stem_visible
            + combo_clash
            + season_adjust
            + month_stem_effect
            + wealth_bonus
        )

        # Determine grade
        grade_code, grade = self.determine_grade(total)

        # Evaluate seal validity
        seal_validity = self.evaluate_seal_validity(
            wealth_root_score=wealth_root_score,
            seal_root_score=seal_root_score,
            wealth_bonus=wealth_bonus,
            wealth_month_state=wealth_month_state,
            wealth_seal_branch_conflict=wealth_seal_branch_conflict,
            officer_root_score=officer_root_score,
            officer_stem_exposed=officer_stem_exposed,
            no_output_counterbalance=no_output_counterbalance,
        )
        seal_validity["wealth_location_hits"] = wealth_hits_log

        return {
            "month_state": month_state,
            "branch_root": branch_root,
            "stem_visible": stem_visible,
            "combo_clash": combo_clash,
            "season_adjust": season_adjust,
            "month_stem_effect": month_stem_effect,
            "wealth_location_bonus_total": wealth_bonus,
            "wealth_location_hits": wealth_hits_log,
            "total": total,
            "grade_code": grade_code,
            "grade": grade,
            "seal_validity": seal_validity,
        }

    def _compute_season_adjust(self, day_stem: str, month_branch: str) -> int:
        """
        Compute season adjustment based on day stem element and month branch season.

        Uses common package's SEASON_ELEMENT_BOOST mapping.
        """
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "common"))
        from saju_common import BRANCH_TO_SEASON, SEASON_ELEMENT_BOOST, STEM_TO_ELEMENT

        # Get season from month branch
        season = BRANCH_TO_SEASON.get(month_branch)
        if not season:
            return 0

        # Get element from day stem
        element = STEM_TO_ELEMENT.get(day_stem)
        if not element:
            return 0

        # Get boost value
        boost = SEASON_ELEMENT_BOOST.get(season, {}).get(element, 0)
        return int(boost)

    def _compute_month_stem_effect(self, day_stem: str, month_stem: str | None) -> int:
        """
        Compute month stem effect based on ten gods relation.

        Month stem 透出 (visible) bonus/penalty based on relation type:
        - 比劫 (peer/rob): +6/+4 (strengthens)
        - 印 (seal): +5/+3 (strengthens)
        - 官殺 (officer/killer): -4/-6 (weakens)
        - 財 (wealth): -2/-3 (mild weaken)
        - 食傷 (food/harm): -1/-2 (mild weaken)
        """
        if not month_stem:
            return 0

        # Calculate ten gods relation
        relation = self._get_ten_gods_relation(day_stem, month_stem)

        # Apply bonus/penalty based on relation
        STEM_EFFECT_MAP = {
            "비견": +6,
            "겁재": +4,
            "정인": +5,
            "편인": +3,
            "정관": -4,
            "편관": -6,
            "정재": -2,
            "편재": -3,
            "식신": -1,
            "상관": -2,
        }

        return STEM_EFFECT_MAP.get(relation, 0)

    def _get_ten_gods_relation(self, day_stem: str, other_stem: str) -> str:
        """
        Calculate ten gods relation between day stem and another stem.

        Returns Korean label (비견, 겁재, 정인, etc.)
        """
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "common"))
        from saju_common import ELEMENT_CONTROLS, ELEMENT_GENERATES, STEM_TO_ELEMENT

        day_elem = STEM_TO_ELEMENT.get(day_stem)
        other_elem = STEM_TO_ELEMENT.get(other_stem)

        if not day_elem or not other_elem:
            return "unknown"

        # Same element
        if day_elem == other_elem:
            # Check yin/yang
            if self._same_yinyang(day_stem, other_stem):
                return "비견"  # 比肩 (same polarity)
            else:
                return "겁재"  # 劫財 (opposite polarity)

        # Generates day master (seal)
        if ELEMENT_GENERATES.get(other_elem) == day_elem:
            if self._same_yinyang(day_stem, other_stem):
                return "정인"  # 正印
            else:
                return "편인"  # 偏印

        # Day master generates (food/harm)
        if ELEMENT_GENERATES.get(day_elem) == other_elem:
            if self._same_yinyang(day_stem, other_stem):
                return "식신"  # 食神
            else:
                return "상관"  # 傷官

        # Day master controls (wealth)
        if ELEMENT_CONTROLS.get(day_elem) == other_elem:
            if self._same_yinyang(day_stem, other_stem):
                return "편재"  # 偏財
            else:
                return "정재"  # 正財

        # Controls day master (officer/killer)
        if ELEMENT_CONTROLS.get(other_elem) == day_elem:
            if self._same_yinyang(day_stem, other_stem):
                return "편관"  # 偏官 (七殺)
            else:
                return "정관"  # 正官

        return "unknown"

    def _same_yinyang(self, stem1: str, stem2: str) -> bool:
        """Check if two stems have same yin/yang polarity"""
        YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}
        YIN_STEMS = {"乙", "丁", "己", "辛", "癸"}

        return (stem1 in YANG_STEMS and stem2 in YANG_STEMS) or (
            stem1 in YIN_STEMS and stem2 in YIN_STEMS
        )
