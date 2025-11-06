"""
Tests for yuanjin (원진) detector
"""

import json
import re
from pathlib import Path

import pytest
from app.core import yuanjin as yj


@pytest.mark.parametrize(
    "b4,expected_pairs,expected_flags",
    [
        (["子", "丑", "寅", "未"], [["子", "未"]], [True, False, False, True]),
        (["酉", "戌", "辰", "卯"], [["卯", "辰"], ["酉", "戌"]], [True, True, True, True]),
    ],
)
def test_detect_and_flags_goldenset(b4, expected_pairs, expected_flags):
    pairs = yj.detect_yuanjin(b4)
    assert pairs == expected_pairs
    flags = yj.apply_yuanjin_flags(b4)["flags"]
    assert flags == expected_flags


@pytest.mark.parametrize(
    "b4,expected_pairs",
    [
        (["申", "申", "亥", "子"], [["申", "亥"]]),  # 중복 지지 포함, 1쌍만 히트
        (["午", "丑", "未", "巳"], [["丑", "午"]]),  # 未-子는 미존재
    ],
)
def test_detect_with_duplicates_and_partials(b4, expected_pairs):
    assert yj.detect_yuanjin(b4) == expected_pairs


@pytest.mark.parametrize(
    "bad",
    [
        ["子", "丑", "寅"],  # 길이 < 4
        ["子", "丑", "寅", "卯", "辰"],  # 길이 > 4
        ["子", "A", "寅", "卯"],  # ASCII 혼입
        ["子", "丑", "寅", "甲"],  # 미상 문자(천간)
        ["子", "丑", "寅", "卯 "],  # 공백 포함(길이 1 아님)
    ],
)
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        yj.detect_yuanjin(bad)


def test_explain_trace_and_signature_shape():
    out = yj.explain_yuanjin(["子", "丑", "寅", "未"])
    # 필수 필드 존재
    assert set(out.keys()) == {
        "policy_version",
        "policy_signature",
        "present_branches",
        "hits",
        "pair_count",
    }
    # 시그니처 64hex
    assert re.fullmatch(r"[0-9a-f]{64}", out["policy_signature"])
    # pair_count 일치
    assert out["pair_count"] == len(out["hits"])
    # 결정적 정렬 규칙(내부/목록)
    for a, b in out["hits"]:
        assert yj._BR_INDEX[a] <= yj._BR_INDEX[b]
    sorted_hits = sorted(out["hits"], key=lambda ab: (yj._BR_INDEX[ab[0]], yj._BR_INDEX[ab[1]]))
    assert out["hits"] == sorted_hits
    # 스키마 간이 검증
    schema_path = Path(__file__).parent.parent / "schemas" / "yuanjin_result.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert set(schema["required"]) == {
        "policy_version",
        "policy_signature",
        "present_branches",
        "hits",
        "pair_count",
    }
    assert re.fullmatch(r"^[0-9a-f]{64}$", out["policy_signature"])
    enum12 = schema["properties"]["present_branches"]["items"]["enum"]
    assert set(enum12) == set(yj.BRANCHES)
