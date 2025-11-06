from fastapi.testclient import TestClient



def test_convert_endpoint_returns_payload(api_client: TestClient) -> None:
    """Test timezone conversion endpoint returns proper structure."""
    body = {
        "instant": "1992-07-15T14:40:00Z",
        "source_tz": "UTC",
        "target_tz": "Asia/Seoul",
    }
    response = api_client.post("/v2/time/convert", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["input"]["target_tz"] == "Asia/Seoul"
    assert payload["converted"].endswith("+09:00")
    assert isinstance(payload["tzdb_version"], str)
    assert len(payload["tzdb_version"]) > 0
    # Events list exists (may be empty if no transitions detected)
    assert isinstance(payload["events"], list)
    trace = payload["trace"]
    assert trace["rule_id"] == "KR_classic_v1.4"
    assert trace["tz"]["target"] == "Asia/Seoul"



def test_meta_endpoints_available(api_client: TestClient) -> None:
    for endpoint in ("/", "/health"):
        response = api_client.get(endpoint)
        assert response.status_code == 200
