from app.core.relations import RelationContext, RelationTransformer


def build_transformer() -> RelationTransformer:
    return RelationTransformer.from_file()


def test_sanhe_transform_priority() -> None:
    transformer = build_transformer()
    ctx = RelationContext(branches=["亥", "卯", "未"], month_branch="卯")
    result = transformer.evaluate(ctx)
    assert result.priority_hit == "sanhe_transform"
    assert result.transform_to == "wood"
    assert result.boosts == []


def test_banhe_priority_when_two_members_present() -> None:
    transformer = build_transformer()
    ctx = RelationContext(branches=["亥", "卯"], month_branch="卯")
    result = transformer.evaluate(ctx)
    assert result.priority_hit == "banhe_boost"
    assert result.transform_to is None
    assert result.boosts
    assert "banhe_boost" in result.notes[0]


def test_sanhui_boost_when_no_transform() -> None:
    transformer = build_transformer()
    ctx = RelationContext(branches=["寅", "卯", "辰"], month_branch="寅")
    result = transformer.evaluate(ctx)
    assert result.priority_hit == "sanhui_boost"
    assert result.transform_to is None
    assert result.boosts


def test_chong_detected_when_conflict() -> None:
    transformer = build_transformer()
    ctx = RelationContext(branches=["子", "午", "辰"], month_branch="子")
    result = transformer.evaluate(ctx)
    assert result.priority_hit == "chong"
    assert "子/午" in result.notes[0]


def test_five_he_and_zixing_extras() -> None:
    transformer = build_transformer()
    ctx = RelationContext(
        branches=["子", "丑", "辰"],
        month_branch="丑",
        five_he_pairs=[
            {"pair": "甲己", "month_support": True, "huashen_present": True, "has_conflict": False}
        ],
        zixing_counts={"丑": 2},
        branch_states={"丑": "旺"},
    )
    result = transformer.evaluate(ctx)
    assert "five_he" in result.extras
    assert "zixing" in result.extras
