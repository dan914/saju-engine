from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_compute_returns_sample_payload() -> None:
    payload = {
        "localDateTime": "1992-07-15T23:40:00",
        "timezone": "Asia/Seoul",
        "rules": "KR_classic_v1.4",
    }
    response = client.post("/v2/pillars/compute", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["pillars"]["year"]["pillar"] == "壬申"
    assert data["pillars"]["day"]["policy"] == "zi-start-23"
    trace = data["trace"]
    assert trace["rule_id"] == "KR_classic_v1.4"
    assert trace["tz"]["iana"] == "Asia/Seoul"
    assert trace["flags"]["edge"] is False


def test_day_start_respects_policy() -> None:
    payload = {
        "localDateTime": "1992-07-15T21:10:00",
        "timezone": "Asia/Seoul",
        "rules": "KR_classic_v1.4",
    }
    response = client.post("/v2/pillars/compute", json=payload)
    assert response.status_code == 200
    day_start = response.json()["pillars"]["day"]["dayStartLocal"]
    # ISO8601(+오프셋) 문자열이므로 접미사 비교가 아니라 파싱으로 검증한다.
    from datetime import datetime

    dt = datetime.fromisoformat(day_start)
    assert (dt.hour, dt.minute, dt.second) == (23, 0, 0)
