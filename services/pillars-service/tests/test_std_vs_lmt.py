from datetime import datetime

from app.core.engine import PillarsEngine
from app.models import PillarsComputeRequest


def test_std_time_basis_and_lmt_flag() -> None:
    engine = PillarsEngine()
    request = PillarsComputeRequest(
        localDateTime=datetime(1992, 7, 15, 10, 40),
        timezone="America/New_York",
        rules="KR_classic_v1.4",
    )
    response = engine.compute(request)
    evidence = response.trace.evidence
    assert evidence["time_basis"] == "STD"
    assert evidence["LMT"]["applied"] is False
