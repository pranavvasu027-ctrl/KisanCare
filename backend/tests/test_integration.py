import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_digital_twin():
    response = client.get("/api/v1/farms/F001/digital-twin")
    assert response.status_code == 200
    assert response.json()["farm_id"] == "F001"

def test_simulate():
    response = client.post("/api/v1/simulate", json={
        "farm_id": "F001",
        "changes": {"rainfall_change_percent": -20}
    })
    assert response.status_code == 200
    data = response.json()
    assert "baseline" in data
    assert "scenario" in data
