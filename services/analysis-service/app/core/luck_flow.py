# -*- coding: utf-8 -*-
try:
    from services.common.policy_loader import load_policy_json, resolve_policy_path  # noqa: F401
except ImportError:
    from policy_loader import load_policy_json, resolve_policy_path  # noqa: F401

def _get(d, path, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict): return default
        if p not in cur: return default
        cur = cur[p]
    return cur

def _map_elem(x):
    m = {"목":"wood","화":"fire","토":"earth","금":"metal","수":"water",
         "wood":"wood","fire":"fire","earth":"earth","metal":"metal","water":"water"}
    return m.get(x, x)

def _any_flag(need, have):
    return bool(set(need).intersection(set(have or [])))
class LuckFlow:
    def __init__(self, policy_file: str = "luck_flow_policy_v1.json"):
        self.policy = load_policy_json(policy_file)
        sc = self.policy["scoring"]
        self.weights = sc["weights"]
        self.thresh  = sc["trend_thresholds"]
        self.min_clamp, self.max_clamp = sc["clamp_range"]

    def _check_when(self, when: dict, ctx: dict) -> bool:
        if "yongshin.primary_in" in when:
            if _get(ctx,"yongshin.primary") not in set(when["yongshin.primary_in"]): return False
        bi = _get(ctx,"climate.balance_index",0)
        if "climate.balance_index_gte" in when and not (bi >= when["climate.balance_index_gte"]): return False
        if "climate.balance_index_lte" in when and not (bi <= when["climate.balance_index_lte"]): return False
        if "strength.elements_any" in when:
            ok=False
            for token in when["strength.elements_any"]:
                lv, el = token.split(":")
                if el == "primary": el = _get(ctx,"yongshin.primary")
                el = _map_elem(el)
                if _get(ctx,f"strength.elements.{el}") == lv: ok=True; break
            if not ok: return False
        if "relation.flags_any" in when:
            if not _any_flag(when["relation.flags_any"], _get(ctx,"relation.flags",[])): return False
        for b in ["daewoon.turning_to_support_primary","daewoon.turning_to_counter_primary","sewoon.supports_primary","sewoon.counters_primary"]:
            if b in when and bool(_get(ctx,b)) is not bool(when[b]): return False
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
        if delta >= self.thresh["rising"]: trend = "rising"
        elif delta <= self.thresh["declining"]: trend = "declining"
        else: trend = "stable"
        score = abs(delta)
        confidence = min(1.0, (len(drivers)+len(detractors))/4.0)
        return {
            "engine": "luck_flow",
            "policy_version": self.policy["policy_version"],
            "trend": trend,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "drivers": drivers,
            "detractors": detractors,
            "evidence_ref": f"luck_flow/{_get(ctx,'context.year') or _get(ctx,'year','-')}/{_get(ctx,'daewoon.current','-')}/{_get(ctx,'sewoon.current','-')}"
        }
