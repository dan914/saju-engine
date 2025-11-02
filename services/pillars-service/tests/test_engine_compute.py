from datetime import datetime

from app.core.engine import PillarsEngine
from app.models import PillarsComputeRequest


def test_engine_returns_expected_sample_pillars() -> None:
    engine = PillarsEngine()
    request = PillarsComputeRequest(
        localDateTime=datetime(1992, 7, 15, 23, 40),
        timezone="Asia/Seoul",
        rules="KR_classic_v1.4",
    )
    response = engine.compute(request)
    pillars = response.pillars
    assert pillars.year.pillar.startswith("壬")
    assert pillars.month.pillar.endswith("未")
    # KR_classic_v1.4 은 子正(23:00) 기준. 1992-07-15 23:40은
    # 07-15 23:00에 시작하는 사주-일에 포함되므로 일주는 '庚寅'이어야 한다.
    # 과거 레퍼런스 스크립트(잘못된 앵커)로 생성한 기대값 '己丑'은 오류였다.
    assert pillars.day.pillar.endswith("寅")
    assert pillars.hour.pillar.endswith("子")
    assert pillars.hour.rangeLocal == ("23:00:00", "01:00:00")
    assert response.trace.rule_id == "KR_classic_v1.4"
    evidence = response.trace.evidence
    assert evidence is not None
    for key in ("engine", "inputs", "pillars", "policy_refs"):
        assert key in evidence
    assert evidence["LMT"]["applied"] is False
    assert evidence["climate"]["segment"] == "중"
    assert evidence["time_basis"] == "STD"
    assert evidence["day_boundary_policy"] == "LCRO"
    assert "luck_calc" in evidence
    assert evidence["luck_calc"]["start_age"] is not None
    assert "luck_direction" in evidence
    assert "shensha" in evidence
    assert "strength_scoring" in evidence
    assert "seal_validity" in evidence["strength_scoring"]
