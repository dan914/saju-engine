from datetime import datetime

from fastapi.testclient import TestClient



def test_compute_returns_sample_payload(api_client: TestClient) -> None:
    payload = {
        "localDateTime": "1992-07-15T23:40:00",
        "timezone": "Asia/Seoul",
        "rules": "KR_classic_v1.4",
    }
    response = api_client.post("/v2/pillars/compute", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["pillars"]["year"]["pillar"] == "壬申"
    assert data["pillars"]["day"]["policy"] == "zi-start-23"
    trace = data["trace"]
    assert trace["rule_id"] == "KR_classic_v1.4"
    assert trace["tz"]["iana"] == "Asia/Seoul"
    assert trace["flags"]["edge"] is False



def test_day_start_respects_policy(api_client: TestClient) -> None:
    """Test that day boundary uses midnight (00:00) - zi-hour conversion handled upstream."""
    payload = {
        "localDateTime": "1992-07-15T21:10:00",
        "timezone": "Asia/Seoul",
        "rules": "KR_classic_v1.4",
    }
    response = api_client.post("/v2/pillars/compute", json=payload)
    assert response.status_code == 200
    day_start = response.json()["pillars"]["day"]["dayStartLocal"]

    dt = datetime.fromisoformat(day_start)
    assert (dt.hour, dt.minute, dt.second) == (0, 0, 0)  # Midnight boundary
