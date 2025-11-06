from fastapi.testclient import TestClient



def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"



def test_root_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "saju-analysis-service"
