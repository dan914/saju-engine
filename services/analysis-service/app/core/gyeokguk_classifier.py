# -*- coding: utf-8 -*-
try:
    from saju_common.policy_loader import load_policy_json, resolve_policy_path  # noqa: F401
except ImportError:
    from policy_loader import load_policy_json, resolve_policy_path  # noqa: F401


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
    m = {
        "목": "wood",
        "화": "fire",
        "토": "earth",
        "금": "metal",
        "수": "water",
        "wood": "wood",
        "fire": "fire",
        "earth": "earth",
        "metal": "metal",
        "water": "water",
    }
    return m.get(x, x)


def _any_flag(need, have):
    return bool(set(need).intersection(set(have or [])))


class GyeokgukClassifier:
    def __init__(self, policy_file: str = "gyeokguk_policy_v1.json"):
        self.policy = load_policy_json(policy_file)

    def _match(self, ctx: dict):
        for rule in self.policy["rules"]:
            w = rule["when"]
            if "strength.phase_in" in w and _get(ctx, "strength.phase") not in set(
                w["strength.phase_in"]
            ):
                continue
            if "strength.elements_any" in w:
                ok = False
                for token in w["strength.elements_any"]:
                    lv, el = token.split(":")
                    if el == "primary":
                        el = _get(ctx, "yongshin.primary")
                    el = _map_elem(el)
                    if _get(ctx, f"strength.elements.{el}") == lv:
                        ok = True
                        break
                if not ok:
                    continue
            if "relation.flags_any" in w:
                if not set(w["relation.flags_any"]).intersection(
                    set(_get(ctx, "relation.flags", []) or [])
                ):
                    continue
            if "yongshin.primary_in" in w and _get(ctx, "yongshin.primary") not in set(
                w["yongshin.primary_in"]
            ):
                continue
            bi = _get(ctx, "climate.balance_index", 0)
            if "climate.balance_index_gte" in w and not (bi >= w["climate.balance_index_gte"]):
                continue
            if "climate.balance_index_lte" in w and not (bi <= w["climate.balance_index_lte"]):
                continue
            return rule["emit"]
        return None

    def run(self, ctx: dict) -> dict:
        emit = self._match(ctx) or {
            "type": "정격",
            "basis": ["월령득기"],
            "confidence": 0.6,
            "notes": "기본 규칙 적용(디폴트).",
        }
        return {
            "engine": "gyeokguk_classifier",
            "policy_version": self.policy["policy_version"],
            "type": emit["type"],
            "basis": emit["basis"],
            "confidence": emit["confidence"],
            "notes": emit["notes"],
            "evidence_ref": f"gyeokguk/{emit['type']}",
        }
