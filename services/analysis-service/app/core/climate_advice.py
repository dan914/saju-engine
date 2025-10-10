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
class ClimateAdvice:
    def __init__(self, policy_file: str = "climate_advice_policy_v1.json"):
        self.policy = json.loads(resolve_policy_path(policy_file).read_text(encoding="utf-8"))

    def _match(self, ctx: dict) -> Tuple[str, str]:
        season = _get(ctx, "context.season")
        phase  = _get(ctx, "strength.phase")
        bal    = _get(ctx, "strength.elements", {})
        flags  = _get(ctx, "climate.flags", [])
        for row in self.policy["advice_table"]:
            w = row["when"]
            if "season" in w and season not in w["season"]:
                continue
            if "strength_phase" in w and phase not in w["strength_phase"]:
                continue
            ok = True
            if "balance" in w:
                for k,v in w["balance"].items():
                    if bal.get(k) != v:
                        ok = False; break
            if not ok:
                continue
            if "imbalance_flags" in w:
                if not all(f in (flags or []) for f in w["imbalance_flags"]):
                    continue
            return row["id"], row["advice"]
        return None, self.policy["output"]["fallback"]

    def run(self, ctx: dict) -> dict:
        pid, advice = self._match(ctx)
        return {
            "engine": "climate_advice",
            "policy_version": self.policy["policy_version"],
            "matched_policy_id": pid,
            "advice": advice,
            "evidence_ref": f"climate_advice/{pid or 'fallback'}"
        }
