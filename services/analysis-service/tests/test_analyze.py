from fastapi.testclient import TestClient



def test_analyze_returns_sample_response(api_client: TestClient) -> None:
    payload = {
        "pillars": {
            "year": {"pillar": "壬申"},
            "month": {"pillar": "辛未"},
            "day": {"pillar": "丁丑"},
            "hour": {"pillar": "庚子"},
        },
        "options": {
            "include_trace": True,
            "birth_dt": "1992-07-14T10:30:00+09:00",
            "gender": "M",
            "timezone": "Asia/Seoul",
        },
    }
    response = api_client.post("/v2/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    ten_gods = data["ten_gods"]
    assert "by_pillar" in ten_gods and "day" in ten_gods["by_pillar"]
    assert ten_gods["summary"]

    relations = data["relations"]
    assert relations.get("priority_hit") is not None
    assert data["relations_weighted"]["summary"] is not None

    extras = data["relations_extras"].get("banhe_groups")
    assert extras is not None

    assert data["strength"]["grade_code"] is not None
    assert data["strength_details"] is not None

    luck = data["luck"]
    assert luck["start_age"] is not None
    if data.get("luck_direction"):
        assert data["luck_direction"]["direction"] is not None

    luck_v112 = data.get("luck_v1_1_2")
    assert luck_v112 is not None
    assert luck_v112["annual"], "annual frames should be present"
    assert luck_v112["transits"]["year"]["pillar"]

    assert "recommendation" in data
    assert data.get("void") is not None
    assert data.get("yuanjin") is not None
    assert data["trace"]["rule_id"] == "KR_classic_v1.4"
