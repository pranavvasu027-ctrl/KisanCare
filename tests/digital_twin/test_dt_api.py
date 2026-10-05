import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.model1.service import model1_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_model():
    model1_service.load_artifacts()

def test_health_endpoint_works():
    resp = client.get("/health")
    assert resp.status_code == 200

def test_direct_model1_endpoint_still_works():
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    }
    resp = client.post("/api/v1/model1/crop-recommendation", json=payload)
    assert resp.status_code == 200
    assert "recommendations" in resp.json()

def test_incomplete_twin_422():
    payload = {
        "farm_id": "F_INC",
        "farmer_id": "U123"
    }
    client.post("/api/v1/digital-twin", json=payload)
    
    resp = client.post("/api/v1/digital-twin/F_INC/predict/model1")
    assert resp.status_code == 422
    assert resp.json()["detail"]["status"] == "insufficient_data"

def test_complete_twin_and_persistence():
    payload = {
        "farm_id": "F_COMP",
        "farmer_id": "U123",
        "soil": {
            "nitrogen": 90,
            "phosphorus": 42,
            "potassium": 43,
            "ph": 6.5
        },
        "climate": {
            "temperature": 25.5,
            "humidity": 80,
            "rainfall": 200
        }
    }
    # Create twin
    client.post("/api/v1/digital-twin", json=payload)
    
    # Predict Model 1
    resp_pred = client.post("/api/v1/digital-twin/F_COMP/predict/model1")
    assert resp_pred.status_code == 200
    
    # Retrieve Updated Twin
    resp_get = client.get("/api/v1/digital-twin/F_COMP")
    assert resp_get.status_code == 200
    twin_data = resp_get.json()
    
    # Verify persistence
    assert "model1" in twin_data["model_outputs"]
    assert "recommendations" in twin_data["model_outputs"]["model1"]
    assert "timestamp" in twin_data["model_outputs"]["model1"]
