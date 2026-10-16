from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_and_mock_digital_twin_contract():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    response = client.get("/api/v1/digital-twin/F001")
    assert response.status_code == 200
    data = response.json()
    assert data["farm_id"] == "F001"
    assert data["is_mock"] is True
    assert data["data_provenance"] == "backend_mock"


def test_simulate_uses_backend_route_prefix():
    response = client.post("/api/v1/simulate", json={"farm_id": "F001", "changes": {"rainfall_change_percent": -20}})
    assert response.status_code == 200
    assert "baseline" in response.json()
    assert "scenario" in response.json()


@patch("backend.app.api.endpoints.requests.post")
def test_crop_proxy_forwards_contract_with_timeout(mock_post):
    mock_post.return_value = Mock(status_code=200, json=lambda: {"status": "SUCCESS", "recommendations": []})
    payload = {"district": "NASHIK", "season": "Kharif", "water_availability": "Medium", "top_k": 3}
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert mock_post.call_args.kwargs["json"] == payload
    assert mock_post.call_args.kwargs["timeout"] > 0


@patch("backend.app.api.endpoints.requests.post", side_effect=requests.ConnectionError())
def test_ml_connection_failure_is_explicit(mock_post):
    response = client.post("/api/v1/market-price", json={"crop": "onion", "market": "Pune(Pimpri)", "date": "2024-07-29"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ml_service_unavailable"


@patch("backend.app.api.endpoints.requests.post", side_effect=requests.Timeout())
def test_ml_timeout_is_explicit(mock_post):
    response = client.post("/api/v1/market-price", json={"crop": "onion", "market": "Pune(Pimpri)", "date": "2024-07-29"})
    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "ml_service_timeout"


def test_invalid_request_is_rejected_before_ml_call():
    response = client.post("/api/v1/crop-recommendation", json={"district": "", "season": "Kharif", "water_availability": "Medium"})
    assert response.status_code == 422
