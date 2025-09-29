from app.main import APP_META, app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    for key, value in APP_META.items():
        assert payload[key] == value


def test_root_returns_metadata() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == APP_META
