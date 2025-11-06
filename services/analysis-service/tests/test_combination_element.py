"""
Tests for combination element transformer (합화오행)
"""

import re
from math import isclose

import pytest
from app.core import combination_element as ce

EPS = 1e-9


def sum1(d):
    """Sum of all 5 elements"""
    return sum(d[e] for e in ce.ELEMENTS)


def test_sanhe_primary_move():
    """Test sanhe (局成) primary move increases target by 0.20"""
    rel = {"earth": {"sanhe": [{"formed": True, "element": "water"}]}}
    dist0 = {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    dist, trace = ce.transform_wuxing(rel, dist0)
    assert isclose(sum1(dist), 1.0, abs_tol=EPS)
    assert pytest.approx(0.4, abs=EPS) == dist["water"]
    assert trace and trace[0]["reason"] == "sanhe" and trace[0]["target"] == "water"
    assert pytest.approx(0.20, abs=EPS) == trace[0]["moved_ratio"]
    assert re.fullmatch(r"[0-9a-f]{64}", trace[0]["policy_signature"])


def test_liuhe_secondary_move():
    """Test liuhe (육합) secondary move increases target by 0.10"""
    rel = {"earth": {"liuhe": [{"element": "metal"}]}}
    dist0 = {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    dist, trace = ce.transform_wuxing(rel, dist0)
    assert isclose(sum1(dist), 1.0, abs_tol=EPS)
    assert pytest.approx(0.3, abs=EPS) == dist["metal"]
    assert trace and trace[0]["reason"] == "liuhe" and trace[0]["target"] == "metal"
    assert pytest.approx(0.10, abs=EPS) == trace[0]["moved_ratio"]


def test_clash_negative_move():
    """Test clash (충) negative move decreases target by 0.10"""
    rel = {"earth": {"clash": [{"element": "fire"}]}}
    dist0 = {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    dist, trace = ce.transform_wuxing(rel, dist0)
    assert isclose(sum1(dist), 1.0, abs_tol=EPS)
    # target에서 0.10 감소 → 0.10
    assert pytest.approx(0.10, abs=EPS) == dist["fire"]
    assert trace and trace[0]["reason"] == "clash" and trace[0]["target"] == "fire"
    assert pytest.approx(-0.10, abs=EPS) == trace[0]["moved_ratio"]


def test_normalization_sum_to_one_with_multiple_rules():
    """Test that sum stays 1.0 with multiple transformation rules"""
    rel = {
        "earth": {"sanhe": [{"formed": True, "element": "water"}], "liuhe": [{"element": "metal"}]},
        "heavenly": {"stem_combos": [{"element": "water"}]},
    }
    dist0 = {"wood": 0.21, "fire": 0.18, "earth": 0.22, "metal": 0.19, "water": 0.20}
    dist, trace = ce.transform_wuxing(rel, dist0)
    assert isclose(sum1(dist), 1.0, abs_tol=EPS)
    assert len(trace) >= 2  # sanhe, liuhe 최소 두 단계


def test_trace_schema_shape():
    """Test trace output matches expected schema shape"""
    # sanhe 하나로 트레이스 생성
    rel = {"earth": {"sanhe": [{"formed": True, "element": "water"}]}}
    dist, trace = ce.transform_wuxing(
        rel, {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    )
    # 스키마 간이 확인
    assert isinstance(trace, list) and len(trace) >= 1
    t0 = trace[0]
    for k in ["reason", "target", "moved_ratio", "weight", "order", "policy_signature"]:
        assert k in t0
    assert t0["reason"] in ["sanhe", "liuhe", "stem_combo", "clash"]
    assert t0["target"] in ce.ELEMENTS
    assert isinstance(t0["order"], int)
    assert re.fullmatch(r"[0-9a-f]{64}", t0["policy_signature"])


def test_policy_override_argument_changes_move_amount():
    """Test that policy override changes move amount"""
    rel = {"earth": {"sanhe": [{"formed": True, "element": "water"}]}}
    dist0 = {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    # 기본: water 0.4 (0.20 이동)
    dist_base, tr_base = ce.transform_wuxing(rel, dist0)
    assert pytest.approx(0.4, abs=EPS) == dist_base["water"]
    # 오버라이드: sanhe 비율 0.10
    override = {"sanhe": {"ratio": 0.10, "order": 1}}
    dist_over, tr_over = ce.transform_wuxing(rel, dist0, policy=override)
    assert pytest.approx(0.3, abs=EPS) == dist_over["water"]
    assert pytest.approx(0.10, abs=EPS) == tr_over[0]["moved_ratio"]


def test_multiple_targets_same_order_first_only():
    """Test that only first target is applied when multiple targets exist in same order"""
    # 동일 order(예: liuhe)에서 여러 대상이 있어도 첫 번째만 적용되는지
    rel = {"earth": {"liuhe": [{"element": "metal"}, {"element": "water"}]}}
    dist0 = {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}
    dist, trace = ce.transform_wuxing(rel, dist0)
    # 기본 정책상 liuhe ratio=0.10 → metal만 증가
    assert ce.ELEMENTS and dist["metal"] > 0.2
    # water는 metal 증가에 기여하므로 감소
    assert dist["water"] < 0.2
    # 트레이스는 metal만 (첫 번째 타겟)
    assert trace and trace[0]["reason"] == "liuhe" and trace[0]["target"] == "metal"
    # water는 트레이스에 없음 (두 번째 타겟은 무시됨)
    assert len(trace) == 1


def test_insufficient_mass_for_move_fair_residual():
    """Test fair residual distribution when one element dominates"""
    # 거의 한 요소에 쏠린 상태에서 음수 이동(clash)을 적용 → 잔차 분산이 편향을 키우지 않는지
    rel = {"earth": {"clash": [{"element": "fire"}]}}
    dist0 = {
        "wood": 0.000001,
        "fire": 0.999996,
        "earth": 0.000001,
        "metal": 0.000001,
        "water": 0.000001,
    }
    dist, trace = ce.transform_wuxing(rel, dist0)
    # 합은 1.0 유지
    assert isclose(sum1(dist), 1.0, abs_tol=EPS)
    # fire가 줄고 타 요소가 비례 증가(음수 이동 분배 후 정규화)
    assert dist["fire"] < 0.999996
    # 비례 분산 덕에 나머지 항목 간의 상대 순서는 크게 변하지 않음(약한 검증)
    others = ["wood", "earth", "metal", "water"]
    assert all(dist[x] > 0.0 for x in others)
