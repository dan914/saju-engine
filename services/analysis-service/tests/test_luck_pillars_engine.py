# -*- coding: utf-8 -*-
import json

from .luck_pillars import LuckCalculator, index_to_pillar, pillar_to_index
from jsonschema import validate

# 제공된 Policy(JSON)의 핵심 필드만 사용 (그대로 주입)
POLICY = {
    "direction": {
        "rule": "year_stem_yinyang_x_gender",
        "matrix": {
            "male": {"yang": "forward", "yin": "backward"},
            "female": {"yang": "backward", "yin": "forward"},
        },
        "labels": {},
    },
    "start_age": {
        "method": "solar_term_interval",
        "reference": {"type": "jie", "forward": "next", "backward": "prev"},
        "conversion": {"days_per_year": 3.0, "hours_per_day": 24.0},
        "rounding": {"decimals": 1, "mode": "half_up"},
    },
    "generation": {
        "start_from_next_after_month": True,
        "age_series": {
            "step_years": 10,
            "count": 10,
            "display_decimals": 0,
            "display_round": "floor",
        },
        "emit": {"ten_god_for_stem": True, "lifecycle_for_branch": True},
    },
}

SCHEMA = json.loads(
    r"""
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["policy_version","direction","start_age","method","pillars","current_luck","policy_signature"]
}
"""
)


def test_forward_sequence_month_anchor_and_lengths():
    calc = LuckCalculator(POLICY)
    pillars = {
        "year": {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day": {"stem": "乙", "branch": "亥"},
        "hour": {"stem": "辛", "branch": "巳"},
    }
    birth_ctx = {
        "sex": "male",
        "birth_ts": "2000-09-14T10:00:00+09:00",
        "age_years_decimal": 25.1,
        "luck": {"method": "solar_term_interval", "start_age": 7.98},  # ctx 제공값 우선
    }
    out = calc.evaluate(birth_ctx, pillars)
    validate(out, SCHEMA)

    # 1) 첫 대운: 월주(乙酉) 다음 갑자(순행)
    month_pillar = "乙酉"
    expected_first = index_to_pillar(pillar_to_index(month_pillar) + 1)
    assert out["pillars"][0]["pillar"] == expected_first

    # 2) 10개/10년 간격
    assert len(out["pillars"]) == 10
    for it in out["pillars"]:
        assert it["end_age"] - it["start_age"] == 10

    # 3) 현재 대운: age≈25.1, start≈7.98 → 통상 decade=2
    assert out["current_luck"]["decade"] in (2, 3)


def test_direction_from_policy_when_missing_in_ctx():
    # ctx에 direction 미제공 → male x 庚(陽) = forward
    calc = LuckCalculator(POLICY)
    pillars = {
        "year": {"stem": "庚", "branch": "辰"},
        "month": {"stem": "乙", "branch": "酉"},
        "day": {"stem": "乙", "branch": "亥"},
        "hour": {"stem": "辛", "branch": "巳"},
    }
    birth_ctx = {
        "sex": "male",
        "birth_ts": "2000-09-14T10:00:00+09:00",
        "age_years_decimal": 20.0,
        "luck": {},
    }
    out = calc.evaluate(birth_ctx, pillars)
    assert out["direction"] == "forward"


def test_reverse_sequence_by_ctx_flag():
    # ctx에 reverse 지정 → 첫 pillar = 월주 이전 갑자
    calc = LuckCalculator(POLICY)
    pillars = {
        "year": {"stem": "辛", "branch": "巳"},
        "month": {"stem": "乙", "branch": "酉"},
        "day": {"stem": "乙", "branch": "亥"},
        "hour": {"stem": "辛", "branch": "巳"},
    }
    birth_ctx = {
        "sex": "female",
        "birth_ts": "2000-09-14T10:00:00+09:00",
        "age_years_decimal": 25.1,
        "luck": {"direction": "reverse", "method": "solar_term_interval", "start_age": 8.0},
    }
    out = calc.evaluate(birth_ctx, pillars)
    month_pillar = "乙酉"
    expected_first = index_to_pillar(pillar_to_index(month_pillar) - 1)
    assert out["pillars"][0]["pillar"] == expected_first


def test_backward_start_age_calculation_positive():
    """
    역행(backward) 대운 시작 나이 계산 버그 수정 검증

    출생: 1963-12-13 20:30 KST
    월지: 子 (11월, 입동~대설)
    이전 절기: 立冬 2020-11-07 (가정)

    역행 시: (birth - prev_jie) / 3 = 양수여야 함
    """
    calc = LuckCalculator(POLICY)
    pillars = {
        "year": {"stem": "癸", "branch": "卯"},
        "month": {"stem": "甲", "branch": "子"},
        "day": {"stem": "庚", "branch": "寅"},
        "hour": {"stem": "丙", "branch": "戌"},
    }

    # 역행 케이스: 陰男 (癸卯년, 음간)
    birth_ctx = {
        "sex": "male",
        "birth_ts": "1963-12-13T20:30:00+09:00",
        "age_years_decimal": 61.8,
        "luck": {"method": "solar_term_interval"},  # start_age 미제공
        "solar_terms": {
            "next_jie_ts": "1964-01-06T06:37:00+09:00",  # 小寒
            "prev_jie_ts": "1963-12-07T07:38:00+09:00",  # 大雪 (출생 6일 전)
        },
    }

    out = calc.evaluate(birth_ctx, pillars)

    # 1) 방향은 역행 (陰男)
    assert out["direction"] == "reverse", f"Expected reverse, got {out['direction']}"

    # 2) start_age는 양수여야 함 (버그 수정 전: -1.9, 수정 후: 1.9)
    assert out["start_age"] > 0, f"start_age must be positive, got {out['start_age']}"

    # 3) 계산 검증: (1963-12-13 20:30 - 1963-12-07 07:38) ≈ 6.54일 ≈ 2.2년
    # 정밀한 시간 계산이므로 tolerance를 0.3으로 설정
    expected_start = 2.0
    assert (
        abs(out["start_age"] - expected_start) < 0.3
    ), f"Expected ~{expected_start}, got {out['start_age']}"

    # 4) 첫 대운은 월주(甲子) 이전 간지
    month_pillar = "甲子"
    expected_first = index_to_pillar(pillar_to_index(month_pillar) - 1)
    assert out["pillars"][0]["pillar"] == expected_first
