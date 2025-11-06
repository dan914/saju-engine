"""
Tests for void calculator (공망/旬空)
"""

import json
import re
from pathlib import Path

import pytest
from app.core import void as vc


@pytest.mark.parametrize(
    "pillar,expected",
    [
        ("乙丑", ["戌", "亥"]),  # 甲子旬(0..9)
        ("丙子", ["申", "酉"]),  # 甲戌旬(10..19)
        ("庚寅", ["午", "未"]),  # 甲申旬(20..29)
        ("癸卯", ["辰", "巳"]),  # 甲午旬(30..39)
        ("己酉", ["寅", "卯"]),  # 甲辰旬(40..49)
        ("甲寅", ["子", "丑"]),  # 甲寅旬(50..59)
    ],
)
def test_compute_void_goldenset(pillar, expected):
    assert vc.compute_void(pillar) == expected


@pytest.mark.parametrize(
    "bad",
    [
        "甲",  # 길이 < 2
        "甲子子",  # 길이 > 2
        "甲 子",  # 공백 포함
        "甲子 ",  # 후행 공백
        "AB",  # ASCII 혼입
        "甲甲",  # 미상 60갑자
    ],
)
def test_compute_void_invalid_inputs(bad):
    with pytest.raises(ValueError):
        vc.compute_void(bad)


def test_apply_void_flags_no_hit_and_multi_hit():
    # hit = 0
    res0 = vc.apply_void_flags(["子", "丑", "寅", "卯"], ["辰", "巳"])
    assert res0["flags"] == [False, False, False, False]
    assert res0["hit_branches"] == []
    # hit >= 1 (여기서는 2)
    res1 = vc.apply_void_flags(["戌", "亥", "寅", "卯"], ["戌", "亥"])
    assert res1["flags"] == [True, True, False, False]
    assert res1["hit_branches"] == ["戌", "亥"]


def test_explain_void_and_schema_shape():
    out = vc.explain_void("乙丑")
    assert set(["policy_version", "policy_signature", "day_index", "xun_start", "kong"]).issubset(
        out.keys()
    )
    # policy_version
    assert isinstance(out["policy_version"], str) and len(out["policy_version"]) > 0
    assert out["policy_version"] == vc.POLICY_VERSION
    # signature 형식 및 일치성
    assert re.fullmatch(r"[0-9a-f]{64}", out["policy_signature"])
    assert out["policy_signature"] == vc.POLICY_SIGNATURE
    # 인덱스/旬 시작 일관성
    idx = vc.JIAZI_60.index("乙丑")
    assert out["day_index"] == idx
    assert out["xun_start"] == (idx // 10) * 10
    # kong 형식
    assert isinstance(out["kong"], list) and len(out["kong"]) == 2
    assert all(k in vc.BRANCHES for k in out["kong"])
    # 스키마 기본 구조 확인(간이 검증)
    schema_path = Path(__file__).parent.parent / "schemas" / "void_result.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert set(schema["required"]) == {
        "policy_version",
        "policy_signature",
        "day_index",
        "xun_start",
        "kong",
    }
    # enum에 12지지가 들어있는지
    kong_enum = schema["properties"]["kong"]["items"]["enum"]
    assert set(kong_enum) == set(vc.BRANCHES)


def test_apply_void_flags_invalid_kong_raises():
    """Test that apply_void_flags raises ValueError for invalid kong input"""
    # 잘못된 kong 길이
    with pytest.raises(ValueError):
        vc.apply_void_flags(["子", "丑", "寅", "卯"], ["子"])
    # kong에 12지지가 아닌 값 포함
    with pytest.raises(ValueError):
        vc.apply_void_flags(["子", "丑", "寅", "卯"], ["子", "A"])
    # branches 길이가 4가 아니어도 에러
    with pytest.raises(ValueError):
        vc.apply_void_flags(["子", "丑", "寅"], ["子", "丑"])
