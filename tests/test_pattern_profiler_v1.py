# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

POLICY = json.loads(Path("policy/pattern_profiler_policy_v1.json").read_text(encoding="utf-8"))
IO_DATA = json.loads(Path("docs/engines/pattern_profiler.io.json").read_text(encoding="utf-8"))
TAGS = set(POLICY["tags_catalog"])
RULES = POLICY["rules"]
EXAMPLES = IO_DATA["cases"]

ALLOWED_TEMPLATE_VARS = {
    "yongshin.primary",
    "luck_flow.trend",
    "climate.balance_index",
    "strength.phase",
    "gyeokguk.type",
}


def _get(ctx, path, default=None):
    cur = ctx
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _primary(ctx):
    return _get(ctx, "yongshin.primary")


def _elem_level(ctx, elem):
    elems = _get(ctx, "strength.elements", {})
    return elems.get(elem)


def _match_when(when, ctx):
    # strength.phase_in
    if "strength.phase_in" in when:
        if _get(ctx, "strength.phase") not in set(when["strength.phase_in"]):
            return False
    # strength.elements_any
    if "strength.elements_any" in when:
        ok = False
        for token in when["strength.elements_any"]:
            lv, el = token.split(":")
            if el == "primary":
                el = _primary(ctx)
            # map korean to english element keys
            mapping = {"목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water"}
            el = mapping.get(el, el)
            if _elem_level(ctx, el) == lv:
                ok = True
                break
        if not ok:
            return False
    # relation.flags_any
    if "relation.flags_any" in when:
        flags = set(_get(ctx, "relation.flags", []) or [])
        if flags.isdisjoint(set(when["relation.flags_any"])):
            return False
    # yongshin.primary_in
    if "yongshin.primary_in" in when:
        if _primary(ctx) not in set(when["yongshin.primary_in"]):
            return False
    # climate.balance_index gte/lte
    bi = _get(ctx, "climate.balance_index", 0)
    if "climate.balance_index_gte" in when:
        if not (bi >= when["climate.balance_index_gte"]):
            return False
    if "climate.balance_index_lte" in when:
        if not (bi <= when["climate.balance_index_lte"]):
            return False
    # climate.flags_any
    if "climate.flags_any" in when:
        cflags = set(_get(ctx, "climate.flags", []) or [])
        if cflags.isdisjoint(set(when["climate.flags_any"])):
            return False
    # luck_flow.trend_in
    if "luck_flow.trend_in" in when:
        if _get(ctx, "luck_flow.trend") not in set(when["luck_flow.trend_in"]):
            return False
    # gyeokguk.type_in
    if "gyeokguk.type_in" in when:
        if _get(ctx, "gyeokguk.type") not in set(when["gyeokguk.type_in"]):
            return False
    return True


def emit_patterns(policy, ctx):
    tags = []
    briefs = {"one_liner": "", "key_points": []}
    for rule in RULES:
        if _match_when(rule["when"], ctx):
            emitted = rule["emit"]["tags"]
            for t in emitted:
                if t not in tags:
                    tags.append(t)
            bt = rule["emit"].get("brief_templates")
            if bt:
                # simple last-wins for one_liner; accumulate key_points
                if "one_liner" in bt and not briefs["one_liner"]:
                    briefs["one_liner"] = bt["one_liner"]
                if "key_points" in bt:
                    briefs["key_points"].extend(bt["key_points"])
    return tags, briefs


def test_examples_emit_expected_patterns():
    for ex in EXAMPLES:
        tags, _briefs = emit_patterns(POLICY, ex["input"])
        assert set(ex["expected_patterns"]).issubset(set(tags))
        assert set(tags).issubset(TAGS)


def test_one_liner_template_variables_are_allowed():
    # Collect all one_liner templates
    templs = []
    for r in RULES:
        bt = r["emit"].get("brief_templates") if "emit" in r else None
        if bt and "one_liner" in bt:
            templs.append(bt["one_liner"])
    assert templs, "No one_liner templates found"
    for t in templs:
        vars_found = re.findall(r"\{([^}]+)\}", t)
        for v in vars_found:
            assert v in ALLOWED_TEMPLATE_VARS, f"Template var not allowed: {v}"


def test_guard_limits_templates_comply():
    for r in RULES:
        bt = r["emit"].get("brief_templates") if "emit" in r else None
        if not bt:
            continue
        if "one_liner" in bt:
            s = bt["one_liner"]
            assert "\n" not in s and len(s) <= 120
        if "key_points" in bt:
            kps = bt["key_points"]
            assert len(kps) <= 5
            for k in kps:
                assert len(k) <= 80


def test_tags_catalog_unique():
    assert len(TAGS) == len(POLICY["tags_catalog"])
