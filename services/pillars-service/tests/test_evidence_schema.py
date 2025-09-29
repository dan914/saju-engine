from datetime import datetime
import json
from pathlib import Path

from app.core.engine import PillarsEngine
from app.models import PillarsComputeRequest


def test_evidence_contains_addendum_fields() -> None:
    engine = PillarsEngine()
    request = PillarsComputeRequest(
        localDateTime=datetime(1992, 7, 15, 23, 40),
        timezone="Asia/Seoul",
        rules="KR_classic_v1.4",
    )
    response = engine.compute(request)
    evidence = response.trace.evidence
    assert evidence is not None
    schema = json.load(Path("schemas/evidence_log_addendum_v1_2.json").open())
    for key in (*schema["add_fields"].keys(), "luck_calc", "luck_direction", "shensha"):
        assert key in evidence
    add_fields = schema["add_fields"]
    for key, fields in add_fields.items():
        for field in fields.keys():
            assert field in evidence[key]
