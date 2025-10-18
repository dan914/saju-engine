"""
Test lifecycle stages with concrete examples for all 10 stems.

Parametrized test cases using known correct mappings from classical texts.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def lifecycle_policy() -> dict:
    """Load lifecycle stages policy."""
    policy_path = (
        Path(__file__).parents[3]
        / "saju_codex_batch_all_v2_6_signed/policies/lifecycle_stages.json"
    )
    with policy_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Test cases: (day_stem, branch, expected_stage)
# Based on 子平眞詮 and 三命通會
LIFECYCLE_EXAMPLES = [
    # 甲 (Yang Wood) - Starting from 亥 (長生), forward direction
    ("甲", "亥", "長生"),
    ("甲", "子", "沐浴"),
    ("甲", "丑", "冠帶"),
    ("甲", "寅", "臨官"),
    ("甲", "卯", "帝旺"),
    ("甲", "辰", "衰"),
    ("甲", "巳", "病"),
    ("甲", "午", "死"),
    ("甲", "未", "墓"),
    ("甲", "申", "絕"),
    ("甲", "酉", "胎"),
    ("甲", "戌", "養"),
    # 乙 (Yin Wood) - Starting from 午 (長生), backward direction
    ("乙", "午", "長生"),
    ("乙", "巳", "沐浴"),
    ("乙", "辰", "冠帶"),
    ("乙", "卯", "臨官"),
    ("乙", "寅", "帝旺"),
    ("乙", "丑", "衰"),
    ("乙", "子", "病"),
    ("乙", "亥", "死"),
    ("乙", "戌", "墓"),
    ("乙", "酉", "絕"),
    ("乙", "申", "胎"),
    ("乙", "未", "養"),
    # 丙 (Yang Fire) - Starting from 寅 (長生), forward direction
    ("丙", "寅", "長生"),
    ("丙", "卯", "沐浴"),
    ("丙", "辰", "冠帶"),
    ("丙", "巳", "臨官"),
    ("丙", "午", "帝旺"),
    ("丙", "未", "衰"),
    ("丙", "申", "病"),
    ("丙", "酉", "死"),
    ("丙", "戌", "墓"),
    ("丙", "亥", "絕"),
    ("丙", "子", "胎"),
    ("丙", "丑", "養"),
    # 丁 (Yin Fire) - Starting from 酉 (長生), backward direction
    ("丁", "酉", "長生"),
    ("丁", "申", "沐浴"),
    ("丁", "未", "冠帶"),
    ("丁", "午", "臨官"),
    ("丁", "巳", "帝旺"),
    ("丁", "辰", "衰"),
    ("丁", "卯", "病"),
    ("丁", "寅", "死"),
    ("丁", "丑", "墓"),
    ("丁", "子", "絕"),
    ("丁", "亥", "胎"),
    ("丁", "戌", "養"),
    # 戊 (Yang Earth) - Starting from 寅 (長生), forward direction
    ("戊", "寅", "長生"),
    ("戊", "卯", "沐浴"),
    ("戊", "辰", "冠帶"),
    ("戊", "巳", "臨官"),
    ("戊", "午", "帝旺"),
    ("戊", "未", "衰"),
    ("戊", "申", "病"),
    ("戊", "酉", "死"),
    ("戊", "戌", "墓"),
    ("戊", "亥", "絕"),
    ("戊", "子", "胎"),
    ("戊", "丑", "養"),
    # 己 (Yin Earth) - Starting from 酉 (長生), backward direction
    ("己", "酉", "長生"),
    ("己", "申", "沐浴"),
    ("己", "未", "冠帶"),
    ("己", "午", "臨官"),
    ("己", "巳", "帝旺"),
    ("己", "辰", "衰"),
    ("己", "卯", "病"),
    ("己", "寅", "死"),
    ("己", "丑", "墓"),
    ("己", "子", "絕"),
    ("己", "亥", "胎"),
    ("己", "戌", "養"),
    # 庚 (Yang Metal) - Starting from 巳 (長生), forward direction
    ("庚", "巳", "長生"),
    ("庚", "午", "沐浴"),
    ("庚", "未", "冠帶"),
    ("庚", "申", "臨官"),
    ("庚", "酉", "帝旺"),
    ("庚", "戌", "衰"),
    ("庚", "亥", "病"),
    ("庚", "子", "死"),
    ("庚", "丑", "墓"),
    ("庚", "寅", "絕"),
    ("庚", "卯", "胎"),
    ("庚", "辰", "養"),
    # 辛 (Yin Metal) - Starting from 子 (長生), backward direction
    ("辛", "子", "長生"),
    ("辛", "亥", "沐浴"),
    ("辛", "戌", "冠帶"),
    ("辛", "酉", "臨官"),
    ("辛", "申", "帝旺"),
    ("辛", "未", "衰"),
    ("辛", "午", "病"),
    ("辛", "巳", "死"),
    ("辛", "辰", "墓"),
    ("辛", "卯", "絕"),
    ("辛", "寅", "胎"),
    ("辛", "丑", "養"),
    # 壬 (Yang Water) - Starting from 申 (長生), forward direction
    ("壬", "申", "長生"),
    ("壬", "酉", "沐浴"),
    ("壬", "戌", "冠帶"),
    ("壬", "亥", "臨官"),
    ("壬", "子", "帝旺"),
    ("壬", "丑", "衰"),
    ("壬", "寅", "病"),
    ("壬", "卯", "死"),
    ("壬", "辰", "墓"),
    ("壬", "巳", "絕"),
    ("壬", "午", "胎"),
    ("壬", "未", "養"),
    # 癸 (Yin Water) - Starting from 卯 (長生), backward direction
    ("癸", "卯", "長生"),
    ("癸", "寅", "沐浴"),
    ("癸", "丑", "冠帶"),
    ("癸", "子", "臨官"),
    ("癸", "亥", "帝旺"),
    ("癸", "戌", "衰"),
    ("癸", "酉", "病"),
    ("癸", "申", "死"),
    ("癸", "未", "墓"),
    ("癸", "午", "絕"),
    ("癸", "巳", "胎"),
    ("癸", "辰", "養"),
]


@pytest.mark.parametrize("day_stem,branch,expected_stage", LIFECYCLE_EXAMPLES)
def test_lifecycle_stage_examples(
    lifecycle_policy: dict, day_stem: str, branch: str, expected_stage: str
):
    """
    Test individual lifecycle stage mappings against known examples.

    All 120 combinations (10 stems × 12 branches) are tested.
    """
    mappings = lifecycle_policy["mappings"]
    actual_stage = mappings[day_stem][branch]

    assert (
        actual_stage == expected_stage
    ), f"Day stem {day_stem} + branch {branch}: expected {expected_stage}, got {actual_stage}"


def test_all_120_combinations_covered():
    """Verify test cases cover all 120 stem-branch combinations."""
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # Expected: 10 stems × 12 branches = 120
    expected_count = 10 * 12

    assert (
        len(LIFECYCLE_EXAMPLES) == expected_count
    ), f"Test cases should cover all 120 combinations, got {len(LIFECYCLE_EXAMPLES)}"

    # Check uniqueness
    combinations = {(stem, branch) for stem, branch, _ in LIFECYCLE_EXAMPLES}
    assert len(combinations) == expected_count, "Test cases have duplicates"

    # Check completeness
    for stem in stems:
        for branch in branches:
            assert (stem, branch) in combinations, f"Missing test case for {stem}-{branch}"


# Group tests by stem for clarity
class TestStemJia:
    """Tests for 甲 (Yang Wood)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("亥", "長生"),
            ("子", "沐浴"),
            ("丑", "冠帶"),
            ("寅", "臨官"),
            ("卯", "帝旺"),
            ("辰", "衰"),
            ("巳", "病"),
            ("午", "死"),
            ("未", "墓"),
            ("申", "絕"),
            ("酉", "胎"),
            ("戌", "養"),
        ],
    )
    def test_jia_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """甲 lifecycle stages (forward from 亥)."""
        assert lifecycle_policy["mappings"]["甲"][branch] == expected_stage


class TestStemYi:
    """Tests for 乙 (Yin Wood)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("午", "長生"),
            ("巳", "沐浴"),
            ("辰", "冠帶"),
            ("卯", "臨官"),
            ("寅", "帝旺"),
            ("丑", "衰"),
            ("子", "病"),
            ("亥", "死"),
            ("戌", "墓"),
            ("酉", "絕"),
            ("申", "胎"),
            ("未", "養"),
        ],
    )
    def test_yi_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """乙 lifecycle stages (backward from 午)."""
        assert lifecycle_policy["mappings"]["乙"][branch] == expected_stage


class TestStemBing:
    """Tests for 丙 (Yang Fire)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("寅", "長生"),
            ("卯", "沐浴"),
            ("辰", "冠帶"),
            ("巳", "臨官"),
            ("午", "帝旺"),
            ("未", "衰"),
            ("申", "病"),
            ("酉", "死"),
            ("戌", "墓"),
            ("亥", "絕"),
            ("子", "胎"),
            ("丑", "養"),
        ],
    )
    def test_bing_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """丙 lifecycle stages (forward from 寅)."""
        assert lifecycle_policy["mappings"]["丙"][branch] == expected_stage


class TestStemDing:
    """Tests for 丁 (Yin Fire)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("酉", "長生"),
            ("申", "沐浴"),
            ("未", "冠帶"),
            ("午", "臨官"),
            ("巳", "帝旺"),
            ("辰", "衰"),
            ("卯", "病"),
            ("寅", "死"),
            ("丑", "墓"),
            ("子", "絕"),
            ("亥", "胎"),
            ("戌", "養"),
        ],
    )
    def test_ding_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """丁 lifecycle stages (backward from 酉)."""
        assert lifecycle_policy["mappings"]["丁"][branch] == expected_stage


class TestStemWu:
    """Tests for 戊 (Yang Earth)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("寅", "長生"),
            ("卯", "沐浴"),
            ("辰", "冠帶"),
            ("巳", "臨官"),
            ("午", "帝旺"),
            ("未", "衰"),
            ("申", "病"),
            ("酉", "死"),
            ("戌", "墓"),
            ("亥", "絕"),
            ("子", "胎"),
            ("丑", "養"),
        ],
    )
    def test_wu_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """戊 lifecycle stages (forward from 寅)."""
        assert lifecycle_policy["mappings"]["戊"][branch] == expected_stage


class TestStemJi:
    """Tests for 己 (Yin Earth)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("酉", "長生"),
            ("申", "沐浴"),
            ("未", "冠帶"),
            ("午", "臨官"),
            ("巳", "帝旺"),
            ("辰", "衰"),
            ("卯", "病"),
            ("寅", "死"),
            ("丑", "墓"),
            ("子", "絕"),
            ("亥", "胎"),
            ("戌", "養"),
        ],
    )
    def test_ji_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """己 lifecycle stages (backward from 酉)."""
        assert lifecycle_policy["mappings"]["己"][branch] == expected_stage


class TestStemGeng:
    """Tests for 庚 (Yang Metal)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("巳", "長生"),
            ("午", "沐浴"),
            ("未", "冠帶"),
            ("申", "臨官"),
            ("酉", "帝旺"),
            ("戌", "衰"),
            ("亥", "病"),
            ("子", "死"),
            ("丑", "墓"),
            ("寅", "絕"),
            ("卯", "胎"),
            ("辰", "養"),
        ],
    )
    def test_geng_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """庚 lifecycle stages (forward from 巳)."""
        assert lifecycle_policy["mappings"]["庚"][branch] == expected_stage


class TestStemXin:
    """Tests for 辛 (Yin Metal)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("子", "長生"),
            ("亥", "沐浴"),
            ("戌", "冠帶"),
            ("酉", "臨官"),
            ("申", "帝旺"),
            ("未", "衰"),
            ("午", "病"),
            ("巳", "死"),
            ("辰", "墓"),
            ("卯", "絕"),
            ("寅", "胎"),
            ("丑", "養"),
        ],
    )
    def test_xin_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """辛 lifecycle stages (backward from 子)."""
        assert lifecycle_policy["mappings"]["辛"][branch] == expected_stage


class TestStemRen:
    """Tests for 壬 (Yang Water)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("申", "長生"),
            ("酉", "沐浴"),
            ("戌", "冠帶"),
            ("亥", "臨官"),
            ("子", "帝旺"),
            ("丑", "衰"),
            ("寅", "病"),
            ("卯", "死"),
            ("辰", "墓"),
            ("巳", "絕"),
            ("午", "胎"),
            ("未", "養"),
        ],
    )
    def test_ren_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """壬 lifecycle stages (forward from 申)."""
        assert lifecycle_policy["mappings"]["壬"][branch] == expected_stage


class TestStemGui:
    """Tests for 癸 (Yin Water)."""

    @pytest.mark.parametrize(
        "branch,expected_stage",
        [
            ("卯", "長生"),
            ("寅", "沐浴"),
            ("丑", "冠帶"),
            ("子", "臨官"),
            ("亥", "帝旺"),
            ("戌", "衰"),
            ("酉", "病"),
            ("申", "死"),
            ("未", "墓"),
            ("午", "絕"),
            ("巳", "胎"),
            ("辰", "養"),
        ],
    )
    def test_gui_lifecycle(self, lifecycle_policy: dict, branch: str, expected_stage: str):
        """癸 lifecycle stages (backward from 卯)."""
        assert lifecycle_policy["mappings"]["癸"][branch] == expected_stage


# Edge case tests
def test_peak_stages_for_all_stems(lifecycle_policy: dict):
    """Verify each stem has exactly one 帝旺 (Peak) stage."""
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        peak_branches = [branch for branch, stage in branch_map.items() if stage == "帝旺"]

        assert (
            len(peak_branches) == 1
        ), f"Stem {stem} should have exactly one 帝旺, found {len(peak_branches)}: {peak_branches}"


def test_extinction_stages_for_all_stems(lifecycle_policy: dict):
    """Verify each stem has exactly one 絕 (Extinction) stage."""
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        extinction_branches = [branch for branch, stage in branch_map.items() if stage == "絕"]

        assert (
            len(extinction_branches) == 1
        ), f"Stem {stem} should have exactly one 絕, found {len(extinction_branches)}: {extinction_branches}"


def test_tomb_stages_for_all_stems(lifecycle_policy: dict):
    """Verify each stem has exactly one 墓 (Tomb) stage."""
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        tomb_branches = [branch for branch, stage in branch_map.items() if stage == "墓"]

        assert (
            len(tomb_branches) == 1
        ), f"Stem {stem} should have exactly one 墓, found {len(tomb_branches)}: {tomb_branches}"
