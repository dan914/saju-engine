"""
Regression test for strength score normalization issue.

Issue: YongshinSelector was receiving raw strength scores (-100~+100)
but expected normalized scores (0.0~1.0), causing misclassification.

Example: -22.0 (신약/weak) was being classified as "strong"
because it didn't match any bin ranges and fell into else clause.

Fix: Multi-layer defense in both Orchestrator and YongshinSelector
- Orchestrator passes comprehensive payload: {bin, score_raw, score_normalized, type}
- YongshinSelector prioritizes: bin → score_normalized → score_raw (auto-normalize)
"""

import pytest
from app.core.saju_orchestrator import SajuOrchestrator


class TestStrengthNormalizationRegression:
    """Regression tests for strength score normalization bug fix."""

    def test_negative_strength_score_classification(self):
        """
        Test that negative strength scores are correctly classified as weak.

        Regression for: 2000-09-14 case where -22.0 was classified as "strong"
        """
        orchestrator = SajuOrchestrator()

        # Case: 신약 (weak) with negative score
        pillars = {
            'year': '庚辰',
            'month': '乙酉',
            'day': '乙亥',
            'hour': '辛巳'
        }

        birth_context = {
            'birth_dt': '2000-09-14T10:00:00',
            'gender': 'M',
            'timezone': 'Asia/Seoul'
        }

        result = orchestrator.analyze(pillars, birth_context)

        # Verify strength
        strength = result['strength']
        assert strength['grade_code'] == '신약', "Expected 신약 (weak) grade"
        assert strength['total'] == pytest.approx(-22.0, abs=1.0), "Expected negative score around -22"

        # Verify yongshin rationale reflects correct strength
        yongshin = result['yongshin']
        rationale = yongshin.get('rationale', [])

        assert len(rationale) > 0, "Should have rationale"
        first_rationale = rationale[0]

        # Should mention 신약 (weak), NOT 신강 (strong)
        assert '신약' in first_rationale, f"Expected '신약' in rationale, got: {first_rationale}"
        assert '신강' not in first_rationale, f"Should NOT mention '신강', got: {first_rationale}"

        # Should prefer 인성·비겁 (resource/companion) for weak chart
        assert '인성' in first_rationale or '비겁' in first_rationale, \
            f"Expected weak strategy (인성·비겁), got: {first_rationale}"

    def test_orchestrator_normalization_functions(self):
        """Test that orchestrator normalization helper functions work correctly."""
        orchestrator = SajuOrchestrator()

        # Test _normalize_strength_score
        assert orchestrator._normalize_strength_score(-100) == pytest.approx(0.0), \
            "극신약 (-100) should normalize to 0.0"
        assert orchestrator._normalize_strength_score(-22) == pytest.approx(0.39), \
            "신약 (-22) should normalize to 0.39"
        assert orchestrator._normalize_strength_score(0) == pytest.approx(0.5), \
            "중화 (0) should normalize to 0.5"
        assert orchestrator._normalize_strength_score(50) == pytest.approx(0.75), \
            "신강 (50) should normalize to 0.75"
        assert orchestrator._normalize_strength_score(100) == pytest.approx(1.0), \
            "극신강 (100) should normalize to 1.0"

        # Test _bin_from_grade
        assert orchestrator._bin_from_grade('태강') == 'strong'
        assert orchestrator._bin_from_grade('극신강') == 'strong'
        assert orchestrator._bin_from_grade('신강') == 'strong'
        assert orchestrator._bin_from_grade('중화') == 'balanced'
        assert orchestrator._bin_from_grade('신약') == 'weak'
        assert orchestrator._bin_from_grade('태약') == 'weak'
        assert orchestrator._bin_from_grade('극신약') == 'weak'

        # Test unknown grade defaults to balanced
        assert orchestrator._bin_from_grade('unknown') == 'balanced'

    def test_boundary_cases(self):
        """Test edge cases at bin boundaries."""
        orchestrator = SajuOrchestrator()

        # Test boundary values
        assert orchestrator._normalize_strength_score(-80) == pytest.approx(0.1)  # weak
        assert orchestrator._normalize_strength_score(-20) == pytest.approx(0.4)  # boundary
        assert orchestrator._normalize_strength_score(20) == pytest.approx(0.6)   # boundary
        assert orchestrator._normalize_strength_score(80) == pytest.approx(0.9)   # strong

        # Test clamping
        assert orchestrator._normalize_strength_score(-200) == pytest.approx(0.0), \
            "Should clamp to 0.0"
        assert orchestrator._normalize_strength_score(200) == pytest.approx(1.0), \
            "Should clamp to 1.0"

    def test_yongshin_selector_multi_layer_defense(self):
        """Test YongshinSelector's multi-layer defense with different payload formats."""
        from app.core.yongshin_selector import YongshinSelector

        # Initialize with default policy
        selector = YongshinSelector()

        # Test Priority 1: bin (Source of Truth)
        strength_with_bin = {
            "bin": "weak",
            "score_normalized": 0.8,  # This should be IGNORED
            "score_raw": 80,          # This should be IGNORED
            "type": "신강"             # This should be IGNORED
        }
        assert selector._get_strength_bin(strength_with_bin) == "weak", \
            "bin should take priority"

        # Test Priority 2: score_normalized
        strength_normalized_only = {
            "score_normalized": 0.3,  # weak range
            "score_raw": 80,          # This should be IGNORED
            "type": "신강"
        }
        assert selector._get_strength_bin(strength_normalized_only) == "weak", \
            "score_normalized should be used if bin missing"

        # Test Priority 3: auto-normalize score_raw
        strength_raw_only = {
            "score_raw": -22.0,  # Should auto-normalize to 0.39 (weak)
            "type": "신약"
        }
        assert selector._get_strength_bin(strength_raw_only) == "weak", \
            "score_raw should be auto-normalized if score_normalized missing"

        # Test backward compatibility with deprecated "score" field
        strength_legacy = {
            "score": -22.0,  # Old format
            "type": "신약"
        }
        assert selector._get_strength_bin(strength_legacy) == "weak", \
            "Legacy 'score' field should still work"

    def test_grade_bin_mismatch_guard(self):
        """
        Test that bin (from grade_code) takes precedence even if scores suggest otherwise.

        This guards against potential bugs where grade_code says "신약" but
        strength calculation error produces positive score.
        """
        orchestrator = SajuOrchestrator()

        # Simulate a hypothetical bug where grade is "신약" but score is positive
        # The bin mapping should still use grade_code as Source of Truth

        grade = "신약"  # weak
        # bin_from_grade should use grade_code, NOT score
        bin_from_grade = orchestrator._bin_from_grade(grade)
        assert bin_from_grade == "weak", \
            "bin should come from grade_code (신약), not buggy score"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
