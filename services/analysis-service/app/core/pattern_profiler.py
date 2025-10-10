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
class PatternProfiler:
    def __init__(self, policy_file: str = "pattern_profiler_policy_v1.json"):
        self.policy = json.loads(resolve_policy_path(policy_file).read_text(encoding="utf-8"))
        self.tags_catalog = set(self.policy["tags_catalog"])

    def _match_when(self, when: dict, ctx: dict) -> bool:
        if "strength.phase_in" in when:
            if _get(ctx, "strength.phase") not in set(when["strength.phase_in"]):
                return False
        if "strength.elements_any" in when:
            ok=False
            for token in when["strength.elements_any"]:
                lv, el = token.split(":")
                if el == "primary":
                    el = _get(ctx, "yongshin.primary")
                el = _map_elem(el)
                if _get(ctx, f"strength.elements.{el}") == lv:
                    ok=True; break
            if not ok: return False
        if "relation.flags_any" in when:
            if not set(when["relation.flags_any"]).intersection(set(_get(ctx,"relation.flags",[]) or [])):
                return False
        if "yongshin.primary_in" in when:
            if _get(ctx,"yongshin.primary") not in set(when["yongshin.primary_in"]):
                return False
        bi = _get(ctx,"climate.balance_index",0)
        if "climate.balance_index_gte" in when and not (bi >= when["climate.balance_index_gte"]):
            return False
        if "climate.balance_index_lte" in when and not (bi <= when["climate.balance_index_lte"]):
            return False
        if "climate.flags_any" in when:
            if not set(when["climate.flags_any"]).intersection(set(_get(ctx,"climate.flags",[]) or [])):
                return False
        if "luck_flow.trend_in" in when:
            if _get(ctx,"luck_flow.trend") not in set(when["luck_flow.trend_in"]):
                return False
        if "gyeokguk.type_in" in when:
            if _get(ctx,"gyeokguk.type") not in set(when["gyeokguk.type_in"]):
                return False
        return True

    def run(self, ctx: dict) -> dict:
        tags = []
        briefs = {"one_liner":"", "key_points":[]}
        for r in self.policy["rules"]:
            if self._match_when(r["when"], ctx):
                for t in r["emit"]["tags"]:
                    if t in self.tags_catalog and t not in tags:
                        tags.append(t)
                bt = r["emit"].get("brief_templates")
                if bt:
                    if "one_liner" in bt and not briefs["one_liner"]:
                        briefs["one_liner"] = bt["one_liner"]
                    if "key_points" in bt:
                        briefs["key_points"].extend(bt["key_points"])
        return {
            "engine": "pattern_profiler",
            "policy_version": self.policy["policy_version"],
            "patterns": tags[:10],
            "briefs": { "one_liner": briefs["one_liner"][:120].replace("\n"," "),
                        "key_points": [k[:80] for k in briefs["key_points"][:5]] },
            "evidence_ref": f"pattern_profiler/{_get(ctx,'luck_flow.trend','-')}/{_get(ctx,'gyeokguk.type','-')}"
        }
