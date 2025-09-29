"""Root/seal strength scoring utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .constants import STEM_TO_ELEMENT
from .wang import WangStateMapper

ZANGGAN_PATH = Path(__file__).resolve().parents[4] / "rulesets" / "zanggan_table.json"
STRENGTH_CRITERIA_PATH = (
    Path(__file__).resolve().parents[4]
    / "saju_codex_bundle_v1"
    / "policy"
    / "strength_criteria_v1.json"
)
STRENGTH_SCALE_PATH = Path(__file__).resolve().parents[4] / "policies" / "strength_scale_v1_1.json"
ROOT_SEAL_POLICY_PATH = (
    Path(__file__).resolve().parents[4] / "policies" / "root_seal_policy_v2_3.json"
)
YUGI_POLICY_PATH = Path(__file__).resolve().parents[4] / "policies" / "yugi_policy_v1_1.json"


@dataclass(slots=True)
class RootSealScorer:
    """Score roots/seal strength based on criteria JSON."""

    zanggan: Dict[str, list[str]]
    weights: Dict[str, Dict[str, object]]
    thresholds: Dict[str, int]
    outputs: Iterable[str]
    wang_mapper: WangStateMapper
    state_points: Dict[str, int] | None = None
    month_stem_adjust: Dict[str, Dict[str, float]] | None = None
    seal_validity_checks: Dict[str, Dict[str, str]] | None = None
    wealth_policy: Dict[str, object] | None = None
    validity_rules: Dict[str, Dict[str, object]] | None = None
    yugi_policy: Dict[str, List[str]] | None = None
    policy_version: str | None = None

    @classmethod
    def from_files(cls) -> "RootSealScorer":
        with ZANGGAN_PATH.open("r", encoding="utf-8") as f:
            zanggan = json.load(f)
        with STRENGTH_CRITERIA_PATH.open("r", encoding="utf-8") as f:
            criteria = json.load(f)
        state_points = None
        month_stem_adjust = None
        seal_checks = None
        if STRENGTH_SCALE_PATH.exists():
            with STRENGTH_SCALE_PATH.open("r", encoding="utf-8") as sf:
                scale_data = json.load(sf)
            state_points = scale_data.get("state_points")
            month_stem_adjust = scale_data.get("month_stem_adjust")
            seal_checks = scale_data.get("seal_validity_checks")
        wealth_policy = {"enabled": False}
        validity_rules = {}
        policy_version = None
        if ROOT_SEAL_POLICY_PATH.exists():
            with ROOT_SEAL_POLICY_PATH.open("r", encoding="utf-8") as pf:
                root_policy = json.load(pf)
            wealth_policy = root_policy.get("wealth_location_bonus", {"enabled": False})
            validity_rules = root_policy.get("validity", {})
            policy_version = root_policy.get("version")
        yugi_policy = None
        if YUGI_POLICY_PATH.exists():
            with YUGI_POLICY_PATH.open("r", encoding="utf-8") as yf:
                yugi_policy = json.load(yf)
        return cls(
            zanggan=zanggan,
            weights=criteria["weights"],
            thresholds=criteria["thresholds"],
            outputs=criteria["outputs"],
            wang_mapper=WangStateMapper.from_file(),
            state_points=state_points,
            month_stem_adjust=month_stem_adjust,
            seal_validity_checks=seal_checks,
            wealth_policy=wealth_policy,
            validity_rules=validity_rules,
            yugi_policy=yugi_policy,
            policy_version=policy_version,
        )

    def score_month_state(self, month_branch: str, day_stem: str) -> int:
        day_element = STEM_TO_ELEMENT[day_stem]
        state = self.wang_mapper.state_for(month_branch, day_element)
        if self.state_points:
            return self.state_points.get(state, 0)
        return self.weights["month_state"][state]

    def score_roots(self, day_stem: str, day_branch: str, other_branches: Iterable[str]) -> int:
        weights = self.weights["branch_root"]
        total = 0
        hidden_stems = self.zanggan.get(day_branch, [])
        if hidden_stems:
            total += weights["day_branch_same"]
        for branch in other_branches:
            if branch == day_branch:
                continue
            if day_stem in self.zanggan.get(branch, []):
                total += weights["other_branch_root"]
        return total

    def score_visible_stems(self, counts: Dict[str, int]) -> int:
        weights = self.weights["stem_visible"]
        return sum(weights.get(category, 0) * counts.get(category, 0) for category in weights)

    def total_score(
        self,
        *,
        month_branch: str,
        day_pillar: str,
        branch_roots: Iterable[str],
        visible_counts: Dict[str, int],
    ) -> int:
        day_stem = day_pillar[0]
        day_branch = day_pillar[1]
        month_score = self.score_month_state(month_branch, day_stem)
        root_score = self.score_roots(day_stem, day_branch, branch_roots)
        visible_score = self.score_visible_stems(visible_counts)
        return month_score + root_score + visible_score

    def grade(self, total: int) -> str:
        thresholds = sorted(self.thresholds.items(), key=lambda item: item[1], reverse=True)
        for label, limit in thresholds:
            if total >= limit:
                return label
        return "極弱"

    def grade_info(self, total: int) -> tuple[str, str]:
        label = self.grade(total)
        thresholds = sorted(self.thresholds.items(), key=lambda item: item[1], reverse=True)
        labels = [name for name, _ in thresholds]
        level = label
        if self.outputs:
            try:
                index = labels.index(label)
                if index < len(self.outputs):
                    level = self.outputs[index]
            except ValueError:
                level = self.outputs[-1]
        return label, level

    def compute_wealth_location_bonus(
        self, hits: Iterable[Dict[str, str]] | None, month_stem_exposed: bool = False
    ) -> tuple[float, list[Dict[str, object]]]:
        policy = self.wealth_policy or {"enabled": False}
        if not policy.get("enabled", False):
            return 0.0, []
        min_level = policy.get("min_level", "sub")
        level_order = {"main": 2, "sub": 1, "minor": 0}
        min_rank = level_order.get(min_level, 1)
        weights = policy.get("weights", {})
        cap_total = policy.get("cap_total")
        total = 0.0
        log: list[Dict[str, object]] = []
        for item in hits or []:
            slot = item.get("slot")
            level = item.get("level", "minor")
            if level_order.get(level, 0) < min_rank:
                continue
            weight = weights.get(f"{slot}_branch") if slot else None
            if weight:
                total += weight
                log.append({"branch": slot, "level": level, "weight_applied": weight})
        if month_stem_exposed and policy.get("month_stem_exposed_bonus"):
            bonus = policy["month_stem_exposed_bonus"]
            total += bonus
            log.append({"month_stem_exposed": True, "bonus_applied": bonus})
        if cap_total is not None and total > cap_total:
            total = cap_total
        return total, log

    def evaluate_seal_validity(
        self,
        *,
        wealth_root_score: int,
        seal_root_score: int,
        wealth_bonus: float,
        wealth_month_state: str | None = None,
        wealth_seal_branch_conflict: bool = False,
        officer_root_score: int = 0,
        officer_stem_exposed: bool = False,
        no_output_counterbalance: bool = True,
    ) -> Dict[str, object]:
        validity = {
            "seal_level": "full",
            "broken_by_wealth": False,
            "suppressed_by_officer_killer": False,
            "wealth_location_bonus_total": wealth_bonus,
            "wealth_location_hits": [],
        }
        rules = self.validity_rules or {}
        wealth_rule = rules.get("wealth_breaks_seal")
        if wealth_rule:
            diff = (wealth_root_score + wealth_bonus) - seal_root_score
            threshold = 2
            if diff >= threshold:
                side_ok = True
                conditions = wealth_rule.get("and_also", [])
                for cond in conditions:
                    if "or" in cond:
                        side_ok = False
                        for option in cond["or"]:
                            if (
                                option.get("wealth_month_state_in")
                                and wealth_month_state in option["wealth_month_state_in"]
                            ):
                                side_ok = True
                            if (
                                option.get("wealth_seal_branch_conflict")
                                and wealth_seal_branch_conflict
                            ):
                                side_ok = True
                        if not side_ok:
                            break
                if side_ok:
                    validity["seal_level"] = "none"
                    validity["broken_by_wealth"] = True
        officer_rule = rules.get("officer_suppresses_seal")
        if officer_rule and validity["seal_level"] != "none":
            meets = officer_root_score >= 5 and officer_stem_exposed and no_output_counterbalance
            if meets:
                validity["seal_level"] = "partial"
                validity["suppressed_by_officer_killer"] = True
        return validity


@dataclass(slots=True)
class StrengthEvaluator:
    """Compute final strength grade with combo/clash adjustments."""

    scorer: RootSealScorer

    @classmethod
    def from_files(cls) -> "StrengthEvaluator":
        return cls(scorer=RootSealScorer.from_files())

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
    ) -> Dict[str, int | str | float | object]:
        day_stem = day_pillar[0]
        day_branch = day_pillar[1]
        month_score = self.scorer.score_month_state(month_branch, day_stem)
        root_score = self.scorer.score_roots(day_stem, day_branch, branch_roots)
        visible_score = self.scorer.score_visible_stems(visible_counts)
        combo_weights = self.scorer.weights.get("combo_clash", {})
        combo_score = sum(combo_weights.get(key, 0) * count for key, count in combos.items())
        season_adjust = 0
        month_stem_effect = 0
        if self.scorer.month_stem_adjust:
            assist = self.scorer.month_stem_adjust.get("assist_bonus_pct", 0)
            cap = self.scorer.month_stem_adjust.get("cap_pct", 0.15)
            base = abs(month_score) * assist
            month_stem_effect = int(min(base, abs(month_score) * cap))
            if month_score < 0:
                month_stem_effect *= -1
        wealth_bonus, wealth_hits_log = self.scorer.compute_wealth_location_bonus(
            wealth_hits, month_stem_exposed
        )
        total = (
            month_score
            + root_score
            + visible_score
            + combo_score
            + season_adjust
            + month_stem_effect
            + wealth_bonus
        )
        grade_code, grade_level = self.scorer.grade_info(total)
        seal_validity = self.scorer.evaluate_seal_validity(
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
        result: Dict[str, object] = {
            "month_state": month_score,
            "branch_root": root_score,
            "stem_visible": visible_score,
            "combo_clash": combo_score,
            "season_adjust": season_adjust,
            "month_stem_effect": month_stem_effect,
            "wealth_location_bonus_total": wealth_bonus,
            "wealth_location_hits": wealth_hits_log,
            "total": total,
            "grade_code": grade_code,
            "grade": grade_level,
            "seal_validity": seal_validity,
        }
        return result
