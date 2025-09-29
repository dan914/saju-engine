from datetime import datetime

from app.core.month import (
    DEFAULT_DATA_PATH,
    MonthBranchResolver,
    SimpleSolarTermLoader,
    default_month_resolver,
)
from app.core.resolve import TimeResolver


def test_default_month_branch_resolver_returns_branch() -> None:
    resolver = default_month_resolver()
    branch, term = resolver.resolve(datetime(1992, 7, 15, 23, 40), "Asia/Seoul")
    assert branch == "未"
    assert term.term == "小暑"


def test_month_branch_raises_without_data() -> None:
    resolver = MonthBranchResolver(
        loader=SimpleSolarTermLoader(table_path=DEFAULT_DATA_PATH.parent / "missing"),
        time_resolver=TimeResolver(),
    )
    try:
        resolver.resolve(datetime(1992, 1, 20, 10, 0), "Asia/Seoul")
    except ValueError as exc:
        assert "No solar term data" in str(exc)
    else:
        raise AssertionError("Expected ValueError when dataset missing")
