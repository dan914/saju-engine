# -*- coding: utf-8 -*-
"""YongshinSelector v2.0 - Dualized Yongshin
Implements both traditional dual approach (조후/억부) and integrated recommendation.
"""
import sys
from pathlib import Path
from typing import Any, Dict

# Add common to path for policy loader
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "common"))
from policy_loader import load_policy_json

from .utils_strength_yongshin import ELEM_TO_KO, GEN, KE, STEM_TO_ELEM


class YongshinSelector:
    """Dualized Yongshin:
    - split outputs: climate_yongshin (조후), eokbu_yongshin (억부)
    - integrated recommendation: weighted fusion of signals

    Expects:
      strength: { bin, score_normalized?, grade_code?, elements? }
      climate: { season, flags?, balance_index? }
      relations: { flags? }
      (optional) elements_dist: {'wood':ratio,...} (0~1)
    """

    def __init__(self):
        self.policy = load_policy_json("yongshin_dual_policy_v1.json")

    # --- helpers ---------------------------------------------------------
    def _day_elem(self, day_stem: str) -> str:
        return STEM_TO_ELEM.get(day_stem)

    def _resource_elem(self, day_elem: str) -> str:
        # 生我
        for k, v in GEN.items():
            if v == day_elem:
                return k
        return None

    def _output_elem(self, day_elem: str) -> str:
        # 我生
        return GEN[day_elem]

    def _wealth_elem(self, day_elem: str) -> str:
        # 我克
        return KE[day_elem]

    def _official_elem(self, day_elem: str) -> str:
        # 克我
        for k, v in KE.items():
            if v == day_elem:
                return k
        return None

    def _climate_yongshin(self, season: str) -> Dict[str, Any]:
        rule = self.policy["climate_rules"].get(season) or {"candidates": [], "primary_weight": 0.2}
        primary = rule["candidates"][0] if rule["candidates"] else None
        return {
            "primary": primary,
            "candidates": rule["candidates"],
            "weight": rule["primary_weight"],
            "rule_id": f"climate_{season}",
        }

    def _eokbu_yongshin(
        self, day_elem: str, strength_bin: str, elements_dist: Dict[str, float] = None
    ) -> Dict[str, Any]:
        weights = self.policy["bin_base_weights"][strength_bin]
        # Define candidate order by bin
        if strength_bin == "weak":
            order = ["resource", "companion", "output", "wealth", "official"]
        elif strength_bin == "strong":
            order = ["output", "wealth", "official", "resource", "companion"]
        else:
            order = ["resource", "output", "official", "companion", "wealth"]

        mapping = {
            "resource": self._resource_elem(day_elem),
            "companion": day_elem,
            "output": self._output_elem(day_elem),
            "wealth": self._wealth_elem(day_elem),
            "official": self._official_elem(day_elem),
        }

        # Pick primary/secondary by base weights + deficit
        def deficit_gain(elem_en: str) -> float:
            if not elements_dist:
                return 0.0
            target = self.policy["distribution"]["target_ratio"]
            deficit = max(0.0, target - (elements_dist.get(elem_en, 0.0)))
            return min(self.policy["distribution"]["deficit_gain_max"], deficit)

        scored = []
        for cat in order:
            el = mapping.get(cat)
            if not el:
                continue
            base = weights.get(cat, 0.0)
            dg = deficit_gain(el)
            scored.append((el, base + dg, cat))
        scored.sort(key=lambda x: x[1], reverse=True)
        primary = scored[0][0] if scored else None
        secondary = scored[1][0] if len(scored) > 1 else None
        rationale = [f"{c}:{round(s,3)}" for (e, s, c) in scored[:3]]
        return {"primary": primary, "secondary": secondary, "basis": order, "scored": rationale}

    def _integrated_scores(
        self,
        day_elem: str,
        season: str,
        strength_bin: str,
        elements_dist: Dict[str, float],
        climate_elem: str,
    ) -> Dict[str, float]:
        # start at 0
        scores = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
        # climate weight
        c_rule = self.policy["climate_rules"].get(season) or {"primary_weight": 0.2}
        c_w = c_rule["primary_weight"]
        if climate_elem:
            scores[climate_elem] += c_w

        # base weights by bin
        W = self.policy["bin_base_weights"][strength_bin]
        res = self._resource_elem(day_elem)
        comp = day_elem
        out = self._output_elem(day_elem)
        wea = self._wealth_elem(day_elem)
        off = self._official_elem(day_elem)
        if res:
            scores[res] += W["resource"]
        if comp:
            scores[comp] += W["companion"]
        if out:
            scores[out] += W["output"]
        if wea:
            scores[wea] += W["wealth"]
        if off:
            scores[off] += W["official"]

        # distribution adjustment
        if elements_dist:
            target = self.policy["distribution"]["target_ratio"]
            gmax = self.policy["distribution"]["deficit_gain_max"]
            pmax = self.policy["distribution"]["excess_penalty_max"]
            for el, r in elements_dist.items():
                if r < target:
                    scores[el] += min(gmax, target - r)
                elif r > target:
                    scores[el] -= min(pmax, r - target)

        return scores

    # --- public ----------------------------------------------------------
    def select(
        self,
        day_master: str,
        strength: Dict[str, Any],
        relations: Dict[str, Any],
        climate: Dict[str, Any],
        elements_dist: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        day_elem = STEM_TO_ELEM.get(day_master)
        season = climate.get("season")
        strength_bin = strength.get("bin") or (
            "weak"
            if (strength.get("score_normalized", 0.5) < 0.4)
            else ("strong" if strength.get("score_normalized", 0.5) >= 0.6 else "balanced")
        )

        # split
        c_part = self._climate_yongshin(season)
        e_part = self._eokbu_yongshin(day_elem, strength_bin, elements_dist)

        # integrated
        climate_elem_en = (
            {"목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water"}.get(
                c_part["primary"]
            )
            if c_part["primary"]
            else None
        )
        scores = self._integrated_scores(
            day_elem, season, strength_bin, elements_dist or {}, climate_elem_en
        )
        rank = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        primary_en, primary_sc = rank[0]
        secondary_en, secondary_sc = rank[1]
        margin = primary_sc - secondary_sc
        conf = max(0.5, min(0.95, 0.6 + margin))  # heuristic

        # package
        integrated = {
            "primary": {
                "elem_ko": ELEM_TO_KO[primary_en],
                "elem": primary_en,
                "score": round(primary_sc, 3),
            },
            "secondary": {
                "elem_ko": ELEM_TO_KO[secondary_en],
                "elem": secondary_en,
                "score": round(secondary_sc, 3),
            },
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "confidence": round(conf, 3),
        }
        split = {
            "climate": {
                "primary": c_part["primary"],
                "candidates": c_part["candidates"],
                "rule_id": c_part["rule_id"],
            },
            "eokbu": {
                "primary": ELEM_TO_KO.get(e_part["primary"], e_part["primary"]),
                "secondary": ELEM_TO_KO.get(e_part["secondary"], e_part["secondary"]),
                "basis": e_part["basis"],
                "scored": e_part["scored"],
                "bin": strength_bin,
                "day_elem": ELEM_TO_KO[day_elem],
            },
        }
        return {
            "policy_version": self.policy["policy_version"],
            "integrated": integrated,
            "split": split,
            "rationale": [
                f"season={season}, climate→{split['climate']['primary']}",
                f"bin={strength_bin}, eokbu→{split['eokbu']['primary']}/{split['eokbu']['secondary']}",
            ],
        }
