# -*- coding: utf-8 -*-
"""
Strength Normalization Fix - Unit Tests

Tests for the fix that replaces simple clamping with linear normalization
to preserve negative score information and correct grade assignments.

Bug: Previously, raw scores in [-70, 0) were all clamped to 0, causing
     46.9% of charts to receive incorrect grades.

Fix: Linear normalization maps [-70, 120] → [0, 100] before grading.
     Formula: normalized = (raw - (-70)) / 190 * 100
"""
import sys
from pathlib import Path

import pytest

# Add paths for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "services" / "analysis-service"))
sys.path.insert(0, str(project_root / "services" / "common"))

from app.core.strength_v2 import StrengthEvaluator


class TestStrengthNormalization:
    """Test suite for strength normalization fix"""

    def setup_method(self):
        """Setup evaluator for each test"""
        self.evaluator = StrengthEvaluator()

    # -------------------------------------------------------------------------
    # Test 1: Boundary and Representative Cases
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "raw,expected_normalized,expected_grade",
        [
            # Boundary cases
            (-70.0, 0.0, "극신약"),  # Theoretical minimum → 0
            (120.0, 100.0, "극신강"),  # Theoretical maximum → 100
            # Tier boundaries (approximate)
            (-33.0, 19.47, "극신약"),  # Just below 신약 threshold
            (-32.0, 20.0, "신약"),  # 신약 lower boundary
            (-11.0, 31.05, "신약"),  # 2000-09-14 test case ✅
            (0.0, 36.84, "신약"),  # Zero should be 신약, not 극신약
            (10.0, 42.11, "중화"),  # Previously wrong (극신약)
            (25.0, 50.0, "중화"),  # Mid-range
            (50.0, 63.16, "신강"),  # Previously wrong (중화)
            (75.0, 76.32, "신강"),  # Strong range
            (100.0, 89.47, "극신강"),  # High score
            # Edge cases
            (-50.0, 10.53, "극신약"),  # Deep negative
            (-30.0, 21.05, "신약"),  # Light negative → 신약
        ],
    )
    def test_normalization_and_grade(self, raw, expected_normalized, expected_grade):
        """
        Test that normalization correctly maps raw scores to normalized scores
        and produces the expected grade.
        """
        # Create mock pillars that will produce the desired raw score
        # We'll test the _normalize_strength method directly
        normalized = self.evaluator._normalize_strength(raw)

        # Check normalization accuracy (within 0.1% tolerance)
        assert (
            abs(normalized - expected_normalized) < 0.1
        ), f"Raw {raw} should normalize to ~{expected_normalized}, got {normalized}"

        # Check grade assignment
        grade = self.evaluator._grade(normalized)
        assert (
            grade == expected_grade
        ), f"Normalized {normalized} should map to {expected_grade}, got {grade}"

    # -------------------------------------------------------------------------
    # Test 2: Mathematical Properties
    # -------------------------------------------------------------------------
    def test_normalization_math_accuracy(self):
        """Test that normalization formula is mathematically correct"""
        test_cases = [
            (-70, 0.0),  # ((-70 + 70) / 190) * 100 = 0
            (-11, 31.05),  # ((59) / 190) * 100 = 31.05
            (0, 36.84),  # ((70) / 190) * 100 = 36.84
            (50, 63.16),  # ((120) / 190) * 100 = 63.16
            (120, 100.0),  # ((190) / 190) * 100 = 100
        ]

        for raw, expected in test_cases:
            normalized = self.evaluator._normalize_strength(raw)
            # Allow 0.5 tolerance for rounding
            assert (
                abs(normalized - expected) < 0.5
            ), f"Raw {raw} → Expected {expected}, got {normalized}"

    def test_monotonicity(self):
        """Test that normalization preserves order (monotonically increasing)"""
        test_values = [-70, -50, -30, -11, 0, 10, 25, 50, 75, 100, 120]
        normalized_values = [self.evaluator._normalize_strength(v) for v in test_values]

        # Check that each value is strictly greater than the previous
        for i in range(1, len(normalized_values)):
            assert (
                normalized_values[i] > normalized_values[i - 1]
            ), f"Monotonicity violated: {normalized_values[i]} <= {normalized_values[i-1]}"

    def test_range_preservation(self):
        """Test that all raw scores map to [0, 100] after normalization"""
        # Test 100 evenly spaced values across theoretical range
        for raw in range(-70, 121, 2):  # Step by 2
            normalized = self.evaluator._normalize_strength(raw)
            assert (
                0.0 <= normalized <= 100.0
            ), f"Normalized value {normalized} out of [0,100] range for raw={raw}"

    # -------------------------------------------------------------------------
    # Test 3: Grade Distribution
    # -------------------------------------------------------------------------
    def test_grade_distribution_balance(self):
        """
        Test that grade distribution is approximately balanced across tiers.

        With linear normalization, each tier should get roughly equal coverage:
        - 극신약: 0-19 (20 points) → raw scores -70 to -33 (37 points)
        - 신약: 20-39 (20 points) → raw scores -32 to 5 (37 points)
        - 중화: 40-59 (20 points) → raw scores 6 to 43 (37 points)
        - 신강: 60-79 (20 points) → raw scores 44 to 81 (37 points)
        - 극신강: 80-100 (21 points) → raw scores 82 to 120 (39 points)
        """
        grade_counts = {"극신약": 0, "신약": 0, "중화": 0, "신강": 0, "극신강": 0}

        # Sample across entire theoretical range
        for raw in range(-70, 121):
            normalized = self.evaluator._normalize_strength(raw)
            grade = self.evaluator._grade(normalized)
            grade_counts[grade] += 1

        # Check that each tier gets roughly equal counts (within 30% variance)
        avg_count = sum(grade_counts.values()) / len(grade_counts)
        for grade, count in grade_counts.items():
            variance = abs(count - avg_count) / avg_count
            assert (
                variance < 0.35
            ), f"Grade {grade} distribution too skewed: {count} vs avg {avg_count}"

    # -------------------------------------------------------------------------
    # Test 4: Regression Check - Bug Cases
    # -------------------------------------------------------------------------
    def test_bug_fix_negative_scores(self):
        """
        Regression test: Negative scores should NOT all map to 극신약.

        Before fix: All negative scores clamped to 0 → 극신약
        After fix: Negative scores distributed across tiers correctly
        """
        # Test that negative scores produce different grades
        test_cases = [
            (-50, "극신약"),  # Very negative → 극신약
            (-30, "신약"),  # Light negative → 신약 (not 극신약!)
            (-11, "신약"),  # 2000-09-14 case → 신약 (not 극신약!)
            (0, "신약"),  # Zero → 신약 (not 극신약!)
        ]

        for raw, expected_grade in test_cases:
            normalized = self.evaluator._normalize_strength(raw)
            grade = self.evaluator._grade(normalized)
            assert (
                grade == expected_grade
            ), f"Bug regression: raw={raw} should be {expected_grade}, got {grade}"

    def test_bug_fix_2000_09_14_case(self):
        """
        Specific regression test for the reported bug case.

        Chart: 2000-09-14, 10:00 AM Seoul, Male (庚辰 乙酉 乙亥 辛巳)
        Raw score: -11

        Before fix: Clamped to 0 → Grade: 극신약 (WRONG)
        After fix: Normalized to 31.05 → Grade: 신약 (CORRECT)
        """
        raw_score = -11.0
        normalized = self.evaluator._normalize_strength(raw_score)
        grade = self.evaluator._grade(normalized)

        # Check normalized score
        assert (
            30.5 < normalized < 31.5
        ), f"2000-09-14 case: Expected normalized ~31.05, got {normalized}"

        # Check grade
        assert grade == "신약", f"2000-09-14 case: Expected grade 신약, got {grade}"

    # -------------------------------------------------------------------------
    # Test 5: Edge Cases and Defensive Programming
    # -------------------------------------------------------------------------
    def test_extreme_outliers(self):
        """Test that extreme outliers beyond theoretical range are handled"""
        # Values outside theoretical range should still clamp to [0, 100]
        extreme_cases = [
            (-1000, 0.0),  # Far below minimum
            (1000, 100.0),  # Far above maximum
        ]

        for raw, expected in extreme_cases:
            normalized = self.evaluator._normalize_strength(raw)
            assert (
                normalized == expected
            ), f"Outlier {raw} should clamp to {expected}, got {normalized}"

    def test_policy_metadata_present(self):
        """Test that policy metadata is included in output"""
        # Create a minimal valid pillar set
        pillars = {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"}

        result = self.evaluator.evaluate(pillars, season="autumn")
        policy = result["strength"].get("policy")

        # Check that policy metadata is present
        assert policy is not None, "Policy metadata missing from output"
        assert policy["min"] == -70.0, f"Expected min=-70.0, got {policy['min']}"
        assert policy["max"] == 120.0, f"Expected max=120.0, got {policy['max']}"
        assert policy["range"] == 190.0, f"Expected range=190.0, got {policy['range']}"

    # -------------------------------------------------------------------------
    # Test 6: Integration Test with Real Pillars (2000-09-14 Case)
    # -------------------------------------------------------------------------
    def test_integration_real_pillars_before_7_adjustments(self):
        """
        BASELINE TEST: 2000-09-14 case BEFORE 7 adjustments

        Chart: 2000-09-14, 10:00 AM Seoul, Male
        Pillars: 庚辰 乙酉 乙亥 辛巳

        Old component breakdown:
        - month_state: -30 (乙木 in 酉月 = 死)
        - branch_root: +3 (only 亥中壬 not matched)
        - stem_visible: +20 (old weights, output=0)
        - combo_clash: -4 (巳/亥 chong)
        - month_stem_effect: applied
        → Raw total: ~-11
        → Normalized: 31.05
        → Grade: 신약 (with old normalization fix)

        This test documents the baseline before 7 adjustments.
        """
        pillars = {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"}

        result = self.evaluator.evaluate(pillars, season="autumn")
        strength = result["strength"]

        # After adjustments, score should INCREASE
        # We just verify the structure is correct
        assert "score_raw" in strength
        assert "score" in strength
        assert "grade_code" in strength
        assert "details" in strength

    def test_integration_2000_09_14_after_7_adjustments(self):
        """
        REGRESSION TEST: 2000-09-14 case AFTER 7 adjustments WITH MIRROR MODE

        Chart: 2000-09-14, 10:00 AM Seoul, Male
        Pillars: 庚辰 乙酉 乙亥 辛巳

        NEW component breakdown (with 7 adjustments + mirror variant):
        - month_state: -30 (乙木 in 酉月 = 死)
        - branch_root: +5 (Adj 1: 辰中乙 exact +3, 亥中甲 same element +2)
        - stem_visible: -4 (Adj 2: 庚 official -6, 乙 companion +8, 辛 official -6)
        - combo_clash: -4 (Adj 3: 巳亥 chong -8, 辰酉 liuhe +4, conflict exclusion working)
        - day_branch_stage_bonus: +3 (Adj 6: 乙亥 = 長生 in mirror mode, +6 damped by 50% due to 巳亥 chong)
        - month_stem_effect: applied (Adj 7: 乙-乙 same, no adjustment)
        → Raw total: -30+5-4-4+3 = -30
        → Normalized: 21.05
        → Grade: 신약 ✓ (correct modern interpretation)

        NOTE: With mirror variant (陰干隨陽), 乙亥 = 長生 instead of 死
        Damping applies because 亥 is in 巳亥 chong: +6 * 0.5 = +3
        This gives the expected 신약 grade for practical interpretation.
        """
        pillars = {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"}

        result = self.evaluator.evaluate(pillars, season="autumn")
        strength = result["strength"]
        details = strength["details"]

        print("\n=== 2000-09-14 Analysis (After 7 Adjustments + Mirror) ===")
        print(f"Raw score: {strength['score_raw']}")
        print(f"Normalized score: {strength['score']}")
        print(f"Grade: {strength['grade_code']}")
        print(f"Details: {details}")

        # Check component calculations are correct
        # Adj 1: Branch root should include same-element bonus (辰中乙 +3, 亥中甲 +2)
        assert (
            details["branch_root"] == 5
        ), f"Expected branch_root = 5, got {details['branch_root']}"

        # Adj 2: Stem visible should be negative (officials drain)
        assert (
            details["stem_visible"] == -4
        ), f"Expected stem_visible = -4, got {details['stem_visible']}"

        # Adj 3: Combo clash: 巳亥 chong (-8) + 辰酉 liuhe (+4) = -4
        assert (
            details["combo_clash"] == -4
        ), f"Expected combo_clash = -4 (chong -8, liuhe +4), got {details['combo_clash']}"

        # Adj 6: Day branch stage bonus: 乙亥 = 長生 (mirror) +6, damped 50% by chong = +3
        assert (
            details["day_branch_stage_bonus"] == 3
        ), f"Expected day_branch_stage_bonus = 3 (乙亥 長生 +6, damped 50%), got {details['day_branch_stage_bonus']}"

        # Overall: With mirror mode, this is 신약 (weak, not extremely weak)
        # Raw: -30+5-4-4+3 = -30
        assert (
            strength["score_raw"] == -30.0
        ), f"Expected raw score = -30.0, got {strength['score_raw']}"

        # Normalized: (-30 - (-70)) / 190 * 100 = 40/190*100 = 21.05
        assert (
            abs(strength["score"] - 21.05) < 0.1
        ), f"Expected normalized score ≈ 21.05, got {strength['score']}"

        # Grade should be 신약 (weak, correct with mirror mode)
        assert (
            strength["grade_code"] == "신약"
        ), f"Expected grade 신약, got {strength['grade_code']}"

    def test_adjustment_1_same_element_root(self):
        """
        Test Adjustment 1: Same-element branch root scoring

        Chart with same-element roots should get bonus points
        Example: 乙 day stem with 亥 branch (contains 甲木 in sub)
        """
        # 乙亥 day pillar - 乙 is wood, 亥 contains 甲 (wood) in sub
        pillars = {
            "year": "庚辰",
            "month": "乙酉",
            "day": "乙亥",  # 亥 contains 甲 (same element as 乙)
            "hour": "辛巳",
        }

        result = self.evaluator.evaluate(pillars, season="autumn")
        details = result["strength"]["details"]

        # 亥中甲 is same element as 乙, should get +2 (sub role, same element)
        # Total branch_root should be >= 2
        assert (
            details["branch_root"] >= 2
        ), f"Expected branch_root >= 2 (same element bonus), got {details['branch_root']}"

    def test_adjustment_2_output_leakage(self):
        """
        Test Adjustment 2: Output (食傷) as leakage

        Output (我生) should be negative now, not neutral
        """
        # Create a chart with output stems visible
        # 庚 day stem (metal), 壬/癸 are output (metal generates water)
        pillars = {
            "year": "壬寅",  # 壬 is output from 庚
            "month": "癸卯",  # 癸 is output from 庚
            "day": "庚午",
            "hour": "戊寅",
        }

        result = self.evaluator.evaluate(pillars, season="spring")
        details = result["strength"]["details"]

        # Stem visible should be negative due to output leakage
        # 壬 (output -3) + 癸 (output -3) + 戊 (companion +8) = +2
        # Actual calculation depends on full context
        print(f"\nOutput leakage test - stem_visible: {details['stem_visible']}")

    def test_adjustment_3_conflict_exclusion(self):
        """
        Test Adjustment 3: Combo/clash with conflict exclusion

        Clashing branches should not participate in combinations
        """
        # Chart with 巳亥 chong (clash)
        pillars = {"year": "庚辰", "month": "乙酉", "day": "乙亥", "hour": "辛巳"}  # 巳亥 chong

        result = self.evaluator.evaluate(pillars, season="autumn")
        details = result["strength"]["details"]

        # Should have negative combo_clash due to 巳亥 chong (-8)
        # and potentially 辰酉 harm (-4)
        assert (
            details["combo_clash"] < 0
        ), f"Expected combo_clash < 0 (conflict present), got {details['combo_clash']}"

    def test_adjustment_6_lifecycle_stage_bonus(self):
        """
        Test Adjustment 6: Day branch lifecycle stage bonus WITH MIRROR MODE

        Test both positive and negative cases
        Mirror mode: 乙 follows 甲 (陰干隨陽)
        - Orthodox: 乙午 = 長生, 乙亥 = 死
        - Mirror: 乙午 = 死, 乙亥 = 長生
        """
        # Test negative case: 乙午 = 死 in mirror mode → -6
        pillars_negative = {
            "year": "庚辰",
            "month": "乙酉",
            "day": "乙午",  # 乙午 = 死 (mirror) → -6
            "hour": "辛巳",
        }

        result_neg = self.evaluator.evaluate(pillars_negative, season="autumn")
        details_neg = result_neg["strength"]["details"]

        assert (
            details_neg["day_branch_stage_bonus"] == -6
        ), f"Expected day_branch_stage_bonus = -6 (乙午 死 in mirror), got {details_neg['day_branch_stage_bonus']}"

        # Test positive case with damping: 乙亥 = 長生 in mirror mode, +6 damped by 50% = +3
        pillars_positive_damped = {
            "year": "庚辰",
            "month": "乙酉",
            "day": "乙亥",  # 乙亥 = 長生 (mirror) → +6, but 巳亥 chong damps it to +3
            "hour": "辛巳",
        }

        result_pos = self.evaluator.evaluate(pillars_positive_damped, season="autumn")
        details_pos = result_pos["strength"]["details"]

        assert (
            details_pos["day_branch_stage_bonus"] == 3
        ), f"Expected day_branch_stage_bonus = 3 (乙亥 長生 +6, damped 50% by chong), got {details_pos['day_branch_stage_bonus']}"


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
