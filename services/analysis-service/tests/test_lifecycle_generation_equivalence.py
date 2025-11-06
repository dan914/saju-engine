"""
Test lifecycle stages generation equivalence.

Verifies that algorithmic generation of lifecycle stages matches the policy file.
This is a property test to ensure the 120 mappings were generated correctly.
"""

import json
from pathlib import Path
from typing import Dict

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


@pytest.fixture
def daystem_yinyang_policy() -> dict:
    """Load day stem yin/yang metadata."""
    policy_path = (
        Path(__file__).parents[3] / "saju_codex_batch_all_v2_6_signed/policies/daystem_yinyang.json"
    )
    with policy_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def lifecycle_starting_points() -> Dict[str, str]:
    """
    長生 (Birth) starting points for each stem.

    Based on classical texts (子平眞詮, 三命通會).
    """
    return {
        "甲": "亥",
        "乙": "午",
        "丙": "寅",
        "丁": "酉",
        "戊": "寅",
        "己": "酉",
        "庚": "巳",
        "辛": "子",
        "壬": "申",
        "癸": "卯",
    }


def generate_lifecycle_mappings(
    yang_stems: list, yin_stems: list, starting_points: Dict[str, str]
) -> Dict[str, Dict[str, str]]:
    """
    Algorithmically generate all 120 lifecycle stage mappings.

    Args:
        yang_stems: List of yang heavenly stems
        yin_stems: List of yin heavenly stems
        starting_points: 長生 branch for each stem

    Returns:
        Dict mapping stem -> branch -> stage
    """
    # 12 lifecycle stages in order
    stages = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"]

    # 12 earthly branches in order
    branches_forward = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    branches_backward = list(reversed(branches_forward))

    mappings = {}

    for stem in yang_stems + yin_stems:
        birth_branch = starting_points[stem]
        is_yang = stem in yang_stems

        # Choose direction
        branches = branches_forward if is_yang else branches_backward

        # Find starting index
        start_idx = branches.index(birth_branch)

        # Generate mappings
        stem_map = {}
        for i in range(12):
            branch_idx = (start_idx + i) % 12
            branch = branches[branch_idx]
            stage = stages[i]
            stem_map[branch] = stage

        mappings[stem] = stem_map

    return mappings


def test_algorithmic_generation_matches_policy(
    lifecycle_policy: dict, daystem_yinyang_policy: dict, lifecycle_starting_points: Dict[str, str]
):
    """
    Verify that algorithmic generation produces identical mappings to policy file.

    This ensures the policy was generated correctly using the classical rules.
    """
    yang_stems = daystem_yinyang_policy["yang_stems"]
    yin_stems = daystem_yinyang_policy["yin_stems"]

    # Generate mappings algorithmically
    generated = generate_lifecycle_mappings(yang_stems, yin_stems, lifecycle_starting_points)

    # Compare with policy
    policy_mappings = lifecycle_policy["mappings"]

    assert set(generated.keys()) == set(policy_mappings.keys()), "Stem sets don't match"

    for stem in generated:
        assert (
            generated[stem] == policy_mappings[stem]
        ), f"Stem {stem} mappings don't match\nGenerated: {generated[stem]}\nPolicy: {policy_mappings[stem]}"


def test_yang_stems_progress_forward(
    lifecycle_policy: dict, daystem_yinyang_policy: dict, lifecycle_starting_points: Dict[str, str]
):
    """Yang stems (甲丙戊庚壬) must progress forward from 長生 point."""
    yang_stems = daystem_yinyang_policy["yang_stems"]
    stages = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"]
    branches_forward = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    mappings = lifecycle_policy["mappings"]

    for stem in yang_stems:
        birth_branch = lifecycle_starting_points[stem]
        start_idx = branches_forward.index(birth_branch)

        # Verify progression
        for i in range(12):
            branch_idx = (start_idx + i) % 12
            branch = branches_forward[branch_idx]
            expected_stage = stages[i]
            actual_stage = mappings[stem][branch]

            assert (
                actual_stage == expected_stage
            ), f"Yang stem {stem}, branch {branch}: expected {expected_stage}, got {actual_stage}"


def test_yin_stems_progress_backward(
    lifecycle_policy: dict, daystem_yinyang_policy: dict, lifecycle_starting_points: Dict[str, str]
):
    """Yin stems (乙丁己辛癸) must progress backward from 長生 point."""
    yin_stems = daystem_yinyang_policy["yin_stems"]
    stages = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"]
    branches_backward = ["亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子"]

    mappings = lifecycle_policy["mappings"]

    for stem in yin_stems:
        birth_branch = lifecycle_starting_points[stem]
        start_idx = branches_backward.index(birth_branch)

        # Verify progression
        for i in range(12):
            branch_idx = (start_idx + i) % 12
            branch = branches_backward[branch_idx]
            expected_stage = stages[i]
            actual_stage = mappings[stem][branch]

            assert (
                actual_stage == expected_stage
            ), f"Yin stem {stem}, branch {branch}: expected {expected_stage}, got {actual_stage}"


def test_starting_points_correct(lifecycle_policy: dict, lifecycle_starting_points: Dict[str, str]):
    """Verify 長生 (Birth) starting points match classical texts."""
    mappings = lifecycle_policy["mappings"]

    for stem, birth_branch in lifecycle_starting_points.items():
        actual_stage = mappings[stem][birth_branch]
        assert (
            actual_stage == "長生"
        ), f"Stem {stem} should have 長生 at branch {birth_branch}, got {actual_stage}"


def test_all_stems_have_all_stages(lifecycle_policy: dict):
    """Each stem must use all 12 stages exactly once (property test)."""
    all_stages = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"]
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        stages_used = sorted(branch_map.values())
        expected_stages = sorted(all_stages)

        assert (
            stages_used == expected_stages
        ), f"Stem {stem} stages: {stages_used} != {expected_stages}"


def test_all_stems_have_12_branches(lifecycle_policy: dict):
    """Each stem must map all 12 branches (property test)."""
    all_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        branches_used = sorted(branch_map.keys())
        expected_branches = sorted(all_branches)

        assert (
            branches_used == expected_branches
        ), f"Stem {stem} branches: {branches_used} != {expected_branches}"


def test_no_duplicate_stages_per_stem(lifecycle_policy: dict):
    """Each stem must not have duplicate stages (property test)."""
    mappings = lifecycle_policy["mappings"]

    for stem, branch_map in mappings.items():
        stages = list(branch_map.values())
        unique_stages = set(stages)

        assert len(stages) == len(unique_stages), f"Stem {stem} has duplicate stages: {stages}"


@pytest.mark.parametrize(
    "stem,birth_branch",
    [
        ("甲", "亥"),
        ("乙", "午"),
        ("丙", "寅"),
        ("丁", "酉"),
        ("戊", "寅"),
        ("己", "酉"),
        ("庚", "巳"),
        ("辛", "子"),
        ("壬", "申"),
        ("癸", "卯"),
    ],
)
def test_each_stem_birth_point(lifecycle_policy: dict, stem: str, birth_branch: str):
    """Parametrized test: Each stem has correct 長生 starting point."""
    mappings = lifecycle_policy["mappings"]
    actual_stage = mappings[stem][birth_branch]

    assert (
        actual_stage == "長生"
    ), f"Stem {stem} should have 長生 at {birth_branch}, got {actual_stage}"


def test_generation_is_deterministic(
    daystem_yinyang_policy: dict, lifecycle_starting_points: Dict[str, str]
):
    """Generation algorithm must produce identical results on multiple runs."""
    yang_stems = daystem_yinyang_policy["yang_stems"]
    yin_stems = daystem_yinyang_policy["yin_stems"]

    # Generate twice
    result_1 = generate_lifecycle_mappings(yang_stems, yin_stems, lifecycle_starting_points)
    result_2 = generate_lifecycle_mappings(yang_stems, yin_stems, lifecycle_starting_points)

    assert result_1 == result_2, "Generation is non-deterministic"


def test_yin_yang_partition_complete(daystem_yinyang_policy: dict):
    """Yin and yang stems must partition all 10 stems."""
    yang_stems = set(daystem_yinyang_policy["yang_stems"])
    yin_stems = set(daystem_yinyang_policy["yin_stems"])

    all_stems = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}

    # No overlap
    assert len(yang_stems & yin_stems) == 0, "Yin and yang stems overlap"

    # Complete coverage
    assert yang_stems | yin_stems == all_stems, "Yin/yang stems don't cover all 10 stems"

    # Correct counts
    assert len(yang_stems) == 5, f"Expected 5 yang stems, got {len(yang_stems)}"
    assert len(yin_stems) == 5, f"Expected 5 yin stems, got {len(yin_stems)}"
