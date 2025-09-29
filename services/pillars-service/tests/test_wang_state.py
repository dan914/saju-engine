import pytest

from app.core.wang import WangStateMapper


def test_wang_state_lookup() -> None:
    mapper = WangStateMapper.from_file()
    assert mapper.state_for("寅", "木") == "旺"
    assert mapper.state_for("未", "火") == "休"


def test_unknown_branch_raises() -> None:
    mapper = WangStateMapper(mapping={"子": {"木": "囚"}})
    with pytest.raises(KeyError):
        mapper.state_for("辰", "火")
