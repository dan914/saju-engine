# -*- coding: utf-8 -*-
from tests._analysis_loader import get_core_attr

RelationAnalyzer = get_core_attr("relations_extras", "RelationAnalyzer")
RelationContext = get_core_attr("relations_extras", "RelationContext")


def test_five_he_conditions_and_conflict():
    ra = RelationAnalyzer()
    ctx = RelationContext(
        branches=["丑", "巳", "酉", "子"],
        five_he_pairs=[
            {"pair": "甲己", "month_support": True, "huashen_stem": False, "conflict_flags": []},
            {"pair": "乙庚", "month_support": False, "huashen_stem": True, "conflict_flags": []},
            {
                "pair": "丙辛",
                "month_support": True,
                "huashen_stem": True,
                "conflict_flags": ["chong"],
            },
        ],
        conflicts=[],
    )
    out = ra.check_five_he(ctx)
    # require_month_support=True, deny_if_conflict=True → valid only first (True), third denied by conflict
    assert out["valid_count"] == 1


def test_zixing_detection_levels():
    ra = RelationAnalyzer()
    ctx = RelationContext(branches=["子", "子", "子", "午"], zixing_counts={"子": 3, "午": 1})
    out = ra.check_zixing(ctx)
    assert out["total"] == 1 and out["zixing_detected"][0]["severity"] == "high"


def test_banhe_without_conflict():
    ra = RelationAnalyzer()
    ctx = RelationContext(branches=["寅", "午", "申"], conflicts=[])
    out = ra.check_banhe_boost(ctx)
    # fire group has 寅/午 present → banhe boost
    assert any(b["element"] == "fire" for b in out)
