from datetime import datetime

from .luck import LuckCalculator, LuckContext, ShenshaCatalog


def test_compute_luck_start_age() -> None:
    calc = LuckCalculator()
    ctx = LuckContext(local_dt=datetime(1992, 7, 15, 23, 40), timezone="Asia/Seoul")
    result = calc.compute_start_age(ctx)
    assert "start_age" in result
    assert result["start_age"] is not None


def test_luck_direction_default() -> None:
    calc = LuckCalculator()
    ctx = LuckContext(
        local_dt=datetime(1992, 7, 15, 23, 40), timezone="Asia/Seoul", gender="female"
    )
    direction = calc.luck_direction(ctx)
    assert "direction" in direction


def test_shensha_catalog() -> None:
    catalog = ShenshaCatalog()
    result = catalog.list_enabled()
    assert "enabled" in result
    assert "list" in result
