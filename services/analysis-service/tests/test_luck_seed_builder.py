from __future__ import annotations

import json
from pathlib import Path

from .luck_seed_builder import LuckSeedBuilder
from .ten_gods import TenGodsCalculator


def _ten_gods_calculator() -> TenGodsCalculator:
    root = Path(__file__).resolve().parents[3]
    policy_path = root / "saju_codex_batch_all_v2_6_signed" / "policies" / "branch_tengods_policy.json"
    with policy_path.open(encoding="utf-8") as fh:
        policy = json.load(fh)
    return TenGodsCalculator(policy, output_policy_version="test")


def test_compute_transit_pillars_returns_three_levels() -> None:
    calculator = _ten_gods_calculator()
    builder = LuckSeedBuilder(calculator)

    transits = builder.compute_transit_pillars(birth_context={"timezone": "Asia/Seoul"})

    assert {"year", "month", "day"}.issubset(transits.keys())
    assert transits["year"]["pillar"]


def test_transit_breakdown_uses_ten_gods_mapping() -> None:
    calculator = _ten_gods_calculator()
    builder = LuckSeedBuilder(calculator)

    breakdown = builder.build_transit_breakdown(day_stem="甲", pillar="甲子")

    assert breakdown.totals, "Transit breakdown should include primary exposure"
    assert "transit" in breakdown.per_pillar
