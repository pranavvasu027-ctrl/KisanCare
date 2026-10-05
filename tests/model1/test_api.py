import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.model1.service import model1_service
import math

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_model():
    # Ensure model is loaded before tests
    model1_service.load_artifacts()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "crop_recommendation"
    assert data["model_loaded"] is True

def test_valid_recommendation():
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    }
    response = client.post("/api/v1/model1/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "model" in data
    assert "recommendations" in data
    recs = data["recommendations"]
    
    # Check top 5
    assert len(recs) == 5
    
    # Check sorted by score descending
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    
    # Check numeric scores
    for r in recs:
        assert isinstance(r["score"], float)
        assert isinstance(r["crop"], str)
        assert isinstance(r["rank"], int)

def test_missing_field():
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "ph": 6.5,
        "rainfall": 200
    } # Missing humidity
    response = client.post("/api/v1/model1/crop-recommendation", json=payload)
    assert response.status_code == 422

def test_invalid_datatype():
    payload = {
        "nitrogen": "ninety", # Invalid
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    }
    response = client.post("/api/v1/model1/crop-recommendation", json=payload)
    assert response.status_code == 422

def test_nan_rejected():
    payload_str = '{"nitrogen": NaN, "phosphorus": 42, "potassium": 43, "temperature": 25.5, "humidity": 80, "ph": 6.5, "rainfall": 200}'
    response = client.post("/api/v1/model1/crop-recommendation", content=payload_str, headers={"Content-Type": "application/json"})
    assert response.status_code == 422

def test_infinity_rejected():
    payload_str = '{"nitrogen": Infinity, "phosphorus": 42, "potassium": 43, "temperature": 25.5, "humidity": 80, "ph": 6.5, "rainfall": 200}'
    response = client.post("/api/v1/model1/crop-recommendation", content=payload_str, headers={"Content-Type": "application/json"})
    assert response.status_code == 422

def test_model_loading_failure():
    # Temporarily unload model to test failure
    model1_service.is_loaded = False
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 25.5,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    }
    response = client.post("/api/v1/model1/crop-recommendation", json=payload)
    assert response.status_code == 503
    
    # Restore model for other tests
    model1_service.load_artifacts()
