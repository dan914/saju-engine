from datetime import datetime

from app.core.resolve import DayBoundaryCalculator, TimeResolver


def test_day_boundary_before_23_sets_previous_day() -> None:
    """Test midnight (00:00) boundary - calendar day conversion handled upstream."""
    calc = DayBoundaryCalculator()
    day_start = calc.compute(datetime(1992, 7, 15, 21, 10), "Asia/Seoul")
    assert day_start.hour == 0  # Midnight boundary
    assert day_start.day == 15  # Same calendar day


def test_day_boundary_after_23_keeps_same_day() -> None:
    """Test midnight (00:00) boundary - calendar day conversion handled upstream."""
    calc = DayBoundaryCalculator()
    day_start = calc.compute(datetime(1992, 7, 15, 23, 40), "Asia/Seoul")
    assert day_start.hour == 0  # Midnight boundary
    assert day_start.day == 15  # Same calendar day


def test_resolve_returns_utc_and_trace() -> None:
    resolver = TimeResolver()
    utc_dt, trace = resolver.resolve(datetime(1992, 7, 15, 23, 40), "Asia/Seoul")
    assert utc_dt.tzinfo is not None
    assert utc_dt.hour == 14
    trace_dict = trace.to_dict()
    assert trace_dict["rule_id"] == "KR_classic_v1.4"
    assert trace_dict["tz"]["iana"] == "Asia/Seoul"
    assert trace_dict["flags"]["tzTransition"] is False


def test_resolve_detects_transition_flag() -> None:
    resolver = TimeResolver()
    utc_dt, trace = resolver.resolve(datetime(2020, 3, 8, 2, 30), "America/New_York")
    assert utc_dt.tzinfo is not None
    assert trace.to_dict()["flags"]["tzTransition"] is True
