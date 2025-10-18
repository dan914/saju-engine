
# -*- coding: utf-8 -*-
"""
정책 기반 모의평가로 격국 type만 검증합니다. 엔진 런타임 구현은 필요 없습니다.
"""
import json
from pathlib import Path

POLICY = json.loads(Path("policy/gyeokguk_policy_v1.json").read_text(encoding="utf-8"))

ALLOWED_TYPES = {"정격","종격","화격","특수격"}

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
    return _get(ctx, f"strength.elements.{elem}")

def _map_korean_elem(x):
    m = {"목":"wood","화":"fire","토":"earth","금":"metal","수":"water",
         "wood":"wood","fire":"fire","earth":"earth","metal":"metal","water":"water"}
    return m.get(x, x)

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
            el = _map_korean_elem(el)
            if _elem_level(ctx, el) == lv:
                ok = True
                break
        if not ok:
            return False
    # relation.flags_any
    if "relation.flags_any" in when:
        flags = set(_get(ctx, "relation.flags", []) or [])
        cond = set(when["relation.flags_any"])
        if flags.isdisjoint(cond):
            return False
    # yongshin.primary_in
    if "yongshin.primary_in" in when:
        if _primary(ctx) not in set(when["yongshin.primary_in"]):
            return False
    # climate.balance_index gte/lte
    bi = _get(ctx, "climate.balance_index", 0)
    if "climate.balance_index_gte" in when and not (bi >= when["climate.balance_index_gte"]):
        return False
    if "climate.balance_index_lte" in when and not (bi <= when["climate.balance_index_lte"]):
        return False
    return True

def evaluate(ctx):
    for rule in POLICY["rules"]:
        if _match_when(rule["when"], ctx):
            e = rule["emit"]
            return e["type"], e["basis"], e["confidence"], e["notes"]
    return None, [], 0.0, ""

def test_examples_match_expected_types():
    for ex in POLICY["examples"]:
        t, basis, conf, notes = evaluate(ex)
        assert t == ex["expect_type"], f"{ex['id']}: expected {ex['expect_type']}, got {t}"
        assert t in ALLOWED_TYPES

def test_basis_subset_and_confidence_range():
    catalog = set(POLICY["criteria_catalog"])
    for rule in POLICY["rules"]:
        basis = rule["emit"]["basis"]
        conf = rule["emit"]["confidence"]
        notes = rule["emit"]["notes"]
        assert set(basis).issubset(catalog)
        assert 0.0 <= conf <= 1.0
        assert "\n" not in notes and len(notes) <= 200

def test_policy_minimum_structure():
    assert POLICY.get("policy_version") == "gyeokguk_policy_v1"
    assert "rules" in POLICY and len(POLICY["rules"]) >= 4
    assert "examples" in POLICY and len(POLICY["examples"]) >= 4
