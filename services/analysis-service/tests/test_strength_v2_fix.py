#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression tests for StrengthEvaluator v2 fix
Tests the corrected _stem_visible_score and _month_stem_effect logic.

Bug fixed: stem_visible_score was giving positive weights to output/wealth/official,
causing systematic bias toward higher strength grades.

Fix: Only resource/companion strengthen the day stem (+),
     output is neutral (0), wealth/official weaken (-).
"""
import sys
from pathlib import Path

import pytest

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "common"))

from app.core.strength_v2 import StrengthEvaluator


class TestStrengthV2Fix:
    """Test cases for strength calculation fix."""

    @pytest.fixture
    def evaluator(self):
        return StrengthEvaluator()

    # -------------------------------------------------------------------------
    # Case 1: 1963-12-13 (Original bug case)
    # -------------------------------------------------------------------------
    def test_case_1963_12_13_weak_fix(self, evaluator):
        """
        1963-12-13 8:30 PM Seoul Male
        癸卯 / 甲子 / 庚寅 / 丙戌

        Day stem: 庚金
        Month branch: 子水

        天干 분석:
        - 癸(水): 식상(output) → 0 (중립)
        - 甲(木): 재성(wealth) → -4 (소모)
        - 丙(火): 관성(official) → -8 (극제)
        → stem_visible = 0 + (-4) + (-8) = -12

        Expected: 신약 (기존: 중화 ❌)
        """
        pillars = {"year": "癸卯", "month": "甲子", "day": "庚寅", "hour": "丙戌"}

        result = evaluator.evaluate(pillars, season="winter")
        strength = result["strength"]

        # Verify stem_visible calculation
        assert (
            strength["details"]["stem_visible"] == -12
        ), f"stem_visible should be -12 (癸=0, 甲=-4, 丙=-8), got {strength['details']['stem_visible']}"

        # Verify grade is 신약 (not 중화)
        assert (
            strength["grade_code"] == "신약"
        ), f"Grade should be 신약, got {strength['grade_code']}"

        # Verify normalized score is in weak range (20-39)
        assert (
            20 <= strength["score"] < 40
        ), f"Normalized score should be in weak range (20-39), got {strength['score']}"

        # Verify bin is weak
        assert strength["bin"] == "weak", f"Bin should be weak, got {strength['bin']}"

    # -------------------------------------------------------------------------
    # Case 2: Pure output/wealth/official (식·재·관만 투간)
    # -------------------------------------------------------------------------
    def test_pure_negative_stems(self, evaluator):
        """
        Test case where only output/wealth/official stems are visible.
        Should result in negative or zero stem_visible score.

        Example: 癸丙 / 甲子 / 庚申 / 丁巳
        - 癸(水): output → 0
        - 甲(木): wealth → -4
        - 丁(火): official → -8
        → stem_visible ≤ 0
        """
        pillars = {"year": "癸丙", "month": "甲子", "day": "庚申", "hour": "丁巳"}

        result = evaluator.evaluate(pillars, season="winter")
        strength = result["strength"]

        # stem_visible should be negative or zero
        assert (
            strength["details"]["stem_visible"] <= 0
        ), f"stem_visible for pure output/wealth/official should be ≤0, got {strength['details']['stem_visible']}"

    # -------------------------------------------------------------------------
    # Case 3: Pure resource/companion (印·比만 투간)
    # -------------------------------------------------------------------------
    def test_pure_positive_stems_with_cap(self, evaluator):
        """
        Test case where only resource/companion stems are visible.
        Should result in positive stem_visible with cap at +15.

        Example: 己土 / 庚申 / 庚申 / 辛酉
        - 己(土): resource → +10
        - 庚(금): companion → +8
        - 辛(금): companion → +8
        → stem_visible = 10 + 8 + 8 = 26 → capped at +15
        """
        pillars = {"year": "己巳", "month": "庚申", "day": "庚申", "hour": "辛酉"}

        result = evaluator.evaluate(pillars, season="autumn")
        strength = result["strength"]

        # stem_visible should be capped at +15
        assert (
            strength["details"]["stem_visible"] == 15
        ), f"stem_visible should be capped at +15, got {strength['details']['stem_visible']}"

        # Grade should be strong (신강 or 극신강)
        assert strength["grade_code"] in [
            "신강",
            "극신강",
        ], f"Grade should be 신강 or 극신강, got {strength['grade_code']}"

    # -------------------------------------------------------------------------
    # Case 4: Month stem effect - ke_to_other (日克月)
    # -------------------------------------------------------------------------
    def test_month_stem_ke_to_other(self, evaluator):
        """
        Test ke_to_other (日克月) case gets -5% penalty.

        Example: 庚(金) day stem vs 甲(木) month stem
        → 금극목 (日克月) → -5% adjustment
        """
        pillars = {
            "year": "癸卯",
            "month": "甲子",  # 甲 = 木
            "day": "庚寅",  # 庚 = 金
            "hour": "丙戌",
        }

        result = evaluator.evaluate(pillars, season="winter")
        strength = result["strength"]

        # Check that month_stem_effect was applied
        assert strength["details"]["month_stem_effect_applied"]

        # Raw score should be less than base (due to -5% adjustment)
        # base = -15 + 0 + (-12) + 4 = -23
        # total = -23 * 0.95 = -21.85
        expected_raw = -21.85
        assert (
            abs(strength["score_raw"] - expected_raw) < 0.1
        ), f"Raw score should be ~{expected_raw} (with -5% ke_to_other), got {strength['score_raw']}"

    # -------------------------------------------------------------------------
    # Case 5: Theoretical range validation
    # -------------------------------------------------------------------------
    def test_theoretical_range_preserved(self, evaluator):
        """
        Verify that stem_visible stays within theoretical bounds.
        With new weights:
        - Max positive: resource(+10) + companion(+8) + companion(+8) = +26 → capped at +15
        - Max negative: official(-8) + official(-8) + wealth(-4) = -20

        This should keep overall range within [-70, 120].
        """
        # Test extreme positive case
        pillars_max = {
            "year": "己巳",  # 己土 = resource (+10)
            "month": "庚申",  # 庚金 = companion (+8)
            "day": "庚申",
            "hour": "辛酉",  # 辛金 = companion (+8)
        }
        result_max = evaluator.evaluate(pillars_max, season="autumn")
        assert (
            result_max["strength"]["details"]["stem_visible"] == 15
        ), "Max stem_visible should be capped at +15"

        # Test extreme negative case
        pillars_min = {
            "year": "癸卯",  # 癸水 = output (0)
            "month": "甲子",  # 甲木 = wealth (-4)
            "day": "庚寅",  # 庚金
            "hour": "丙戌",  # 丙火 = official (-8)
        }
        result_min = evaluator.evaluate(pillars_min, season="winter")
        assert (
            result_min["strength"]["details"]["stem_visible"] <= 0
        ), "stem_visible with only output/wealth/official should be ≤0"

    # -------------------------------------------------------------------------
    # Case 6: Grade distribution sanity check
    # -------------------------------------------------------------------------
    def test_grade_distribution_sanity(self, evaluator):
        """
        Sanity check: Verify that various realistic charts produce
        reasonable grade distribution (not all 중화).
        """
        test_cases = [
            # Weak cases (계절에 맞게 설정)
            ({"year": "癸卯", "month": "甲子", "day": "庚寅", "hour": "丙戌"}, "winter", "신약"),
            ({"year": "壬寅", "month": "癸卯", "day": "庚午", "hour": "丁亥"}, "spring", "신약"),
            # Strong cases (금이 왕성한 계절)
            ({"year": "己巳", "month": "庚申", "day": "庚申", "hour": "辛酉"}, "autumn", "신강"),
            ({"year": "戊戌", "month": "己酉", "day": "庚子", "hour": "辛巳"}, "autumn", "신강"),
        ]

        results = []
        for pillars, season, expected_category in test_cases:
            result = evaluator.evaluate(pillars, season=season)
            grade = result["strength"]["grade_code"]
            results.append((pillars, grade, expected_category))

            # Verify grade is in expected category
            if expected_category == "신약":
                assert grade in [
                    "극신약",
                    "신약",
                ], f"Expected weak grade, got {grade} for {pillars} (season={season})"
            elif expected_category == "신강":
                assert grade in [
                    "신강",
                    "극신강",
                    "중화",
                ], f"Expected strong grade, got {grade} for {pillars} (season={season})"

        # Verify we got variety (not all same grade)
        grades = [r[1] for r in results]
        unique_grades = set(grades)
        assert len(unique_grades) >= 2, f"Should have variety in grades, got only: {unique_grades}"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
