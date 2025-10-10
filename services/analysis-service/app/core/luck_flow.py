# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Any, Dict, Tuple
from services.common.policy_loader import resolve_policy_path

def _get(d, path, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict):
            return default
        if p not in cur:
            return default
        cur = cur[p]
    return cur

def _map_elem(x):
    m = {"목":"wood","화":"fire","토":"earth","금":"metal","수":"water",
         "wood":"wood","fire":"fire","earth":"earth","metal":"metal","water":"water"}
    return m.get(x, x)

def _any_flag(flags_need, flags_have):
    return bool(set(flags_need).intersection(set(flags_have or [])))
class LuckFlow:
    def __init__(self, policy_file: str = "luck_flow_policy_v1.json"):
        self.policy = json.loads(resolve_policy_path(policy_file).read_text(encoding="utf-8"))
        self.weights = self.policy["scoring"]["weights"]
        self.thresh  = self.policy["scoring"]["trend_thresholds"]
        self.min_clamp, self.max_clamp = self.policy["scoring"]["clamp_range"]

    def _check_when(self, when: dict, ctx: dict) -> bool:
        # primary
        if "yongshin.primary_in" in when:
            if _get(ctx, "yongshin.primary") not in set(when["yongshin.primary_in"]):
                return False
        # climate index
        bi = _get(ctx, "climate.balance_index", 0)
        if "climate.balance_index_gte" in when and not (bi >= when["climate.balance_index_gte"]):
            return False
        if "climate.balance_index_lte" in when and not (bi <= when["climate.balance_index_lte"]):
            return False
        # elements_any
        if "strength.elements_any" in when:
            ok = False
            for token in when["strength.elements_any"]:
                lv, el = token.split(":")
                if el == "primary":
                    el = _get(ctx, "yongshin.primary")
                el = _map_elem(el)
                if _get(ctx, f"strength.elements.{el}") == lv:
                    ok = True
                    break
            if not ok:
                return False
        # relation flags
        if "relation.flags_any" in when:
            if not _any_flag(when["relation.flags_any"], _get(ctx, "relation.flags", [])):
                return False
        # transit booleans
        for b in [
            "daewoon.turning_to_support_primary",
            "daewoon.turning_to_counter_primary",
            "sewoon.supports_primary",
            "sewoon.counters_primary"
        ]:
            if b in when:
                parts = b.split(".")
                if not bool(_get(ctx, b)) == bool(when[b]):
                    return False
        return True

    def run(self, ctx: dict) -> dict:
        delta_raw = 0.0
        drivers, detractors = [], []
        for name, sig in self.policy["signals"].items():
            if self._check_when(sig["when"], ctx):
                w = self.weights[sig["eval"]]
                delta_raw += w
                (drivers if w > 0 else detractors).append(name)
        delta = max(self.min_clamp, min(self.max_clamp, delta_raw))
        if delta >= self.thresh["rising"]:
            trend = "rising"
        elif delta <= self.thresh["declining"]:
            trend = "declining"
        else:
            trend = "stable"
        score = abs(delta)
        confidence = min(1.0, (len(drivers) + len(detractors))/4.0)
        return {
            "engine": "luck_flow",
            "policy_version": self.policy["policy_version"],
            "trend": trend,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "drivers": drivers,
            "detractors": detractors,
            "evidence_ref": f"luck_flow/{_get(ctx,'context.year','-')}/{_get(ctx,'daewoon.current','-')}/{_get(ctx,'sewoon.current','-')}"
        }
