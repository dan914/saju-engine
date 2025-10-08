import json
from datetime import datetime
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
    # 리포지토리 루트 기준이 아닌, 테스트 파일 기준으로 스키마 경로를 해석한다.
    schema_path = (Path(__file__).resolve().parents[1] /
                   "schemas" / "evidence_log_addendum_v1_2.json")
    assert schema_path.exists(), f"Missing schema file: {schema_path}"
    schema = json.load(schema_path.open())
    for key in (*schema.get("add_fields", {}).keys(), "luck_calc", "luck_direction", "shensha"):
        assert key in evidence
    add_fields = schema.get("add_fields", {})
    for key, fields in add_fields.items():
        for field in fields.keys():
            assert field in evidence[key]
