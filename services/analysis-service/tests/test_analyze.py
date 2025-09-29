from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_analyze_returns_sample_response() -> None:
    payload = {
        "pillars": {
            "year": {"pillar": "壬申"},
            "month": {"pillar": "辛未"},
            "day": {"pillar": "丁丑"},
            "hour": {"pillar": "庚子"},
        },
        "options": {"include_trace": True},
    }
    response = client.post("/v2/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ten_gods"]["summary"]["day"] == "日主"
    assert data["relations"]["he6"] == [["子", "丑"]]
    assert data["relation_extras"]["priority_hit"] is not None
    assert data["strength"]["level"] == "중강"
    assert data["strength_details"]["grade_code"] in ("極強", "太強", "中和", "偏弱", "極弱")
    assert data["structure"]["primary"] is not None
    assert data["luck"]["start_age"] is not None
    assert data["luck_direction"]["direction"] is not None
    assert "recommendation" in data
    assert data["trace"]["rule_id"] == "KR_classic_v1.4"
