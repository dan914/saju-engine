from fastapi.testclient import TestClient



def test_terms_endpoint_returns_sample_data(api_client: TestClient) -> None:
    response = api_client.post("/v2/terms", json={"year": 1992, "timezone": "Asia/Seoul"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 1992
    assert payload["timezone"] == "Asia/Seoul"
    assert len(payload["terms"]) > 0
    first = payload["terms"][0]
    assert first["term"] == "立春"
    assert first["lambda_deg"] == 315.0
    assert first["local_time"].endswith("+09:00")
    trace = payload["trace"]
    assert trace["rule_id"] == "KR_classic_v1.4"
    assert trace["tz"]["iana"] == "Asia/Seoul"



def test_meta_endpoints_available(api_client: TestClient) -> None:
    for endpoint in ("/", "/health"):
        response = api_client.get(endpoint)
        assert response.status_code == 200
