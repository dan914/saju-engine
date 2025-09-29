from app.core.strength import RootSealScorer, StrengthEvaluator


def test_total_score_and_grade():
    scorer = RootSealScorer.from_files()
    total = scorer.total_score(
        month_branch="未",
        day_pillar="丁丑",
        branch_roots=["丑", "未", "申"],
        visible_counts={"bi_jie": 1, "yin": 1},
    )
    grade = scorer.grade(total)
    assert isinstance(total, int)
    assert grade in scorer.thresholds


def test_strength_evaluator_combo_adjustment():
    evaluator = StrengthEvaluator.from_files()
    details = evaluator.evaluate(
        month_branch="未",
        day_pillar="丁丑",
        branch_roots=["丑", "未"],
        visible_counts={"bi_jie": 1},
        combos={"sanhe": 1, "chong": 1},
    )
    assert isinstance(details['total'], (int, float))
    assert details['grade_code'] in evaluator.scorer.thresholds
    assert isinstance(details['grade'], str)
    assert 'month_stem_effect' in details
    assert 'wealth_location_bonus_total' in details
    assert 'seal_validity' in details
