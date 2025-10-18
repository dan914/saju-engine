from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_convert_endpoint_returns_payload() -> None:
    body = {
        "instant": "1992-07-15T14:40:00Z",
        "source_tz": "UTC",
        "target_tz": "Asia/Seoul",
    }
    response = client.post("/v2/time/convert", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["input"]["target_tz"] == "Asia/Seoul"
    assert payload["converted"].endswith("+09:00")
    # tzdb_version is dynamically detected - just verify it's a non-empty string
    assert isinstance(payload["tzdb_version"], str)
    assert len(payload["tzdb_version"]) > 0
    assert any(event["iana"] == "Asia/Seoul" for event in payload["events"])
    trace = payload["trace"]
    assert trace["rule_id"] == "KR_classic_v1.4"
    assert trace["tz"]["target"] == "Asia/Seoul"


def test_meta_endpoints_available() -> None:
    for endpoint in ("/", "/health"):
        response = client.get(endpoint)
        assert response.status_code == 200
