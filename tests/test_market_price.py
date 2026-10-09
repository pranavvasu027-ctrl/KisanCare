import os
import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/market-price/health")
    assert response.status_code == 200
    assert response.json()["status"] == "up"

def test_valid_prediction():
    payload = {
        "crop": "onion",
        "market": "Pune(Pimpri)",
        "date": "2024-07-29",
        "horizon_days": 7
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "onion"
    assert data["market"] == "Pune(Pimpri)"
    assert data["forecast_horizon_days"] == 7
    assert "current_price" in data
    assert "forecast_price" in data
    assert "trend" in data

def test_invalid_crop():
    payload = {
        "crop": "unknown_crop",
        "market": "Pune(Pimpri)",
        "date": "2024-07-29",
        "horizon_days": 7
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 404
    assert "No trained model found" in response.text

def test_invalid_market():
    payload = {
        "crop": "onion",
        "market": "unknown_market",
        "date": "2024-07-29",
        "horizon_days": 7
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 404
    assert "No trained model found" in response.text

def test_invalid_horizon():
    payload = {
        "crop": "onion",
        "market": "Pune(Pimpri)",
        "date": "2024-07-29",
        "horizon_days": 10
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 400
    assert "Unsupported horizon_days" in response.text

def test_missing_date():
    payload = {
        "crop": "onion",
        "market": "Pune(Pimpri)",
        "horizon_days": 7
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 422 # Pydantic validation error

def test_missing_artifact():
    payload = {
        "crop": "onion",
        "market": "baramati", # Missing artifact
        "date": "2024-07-29",
        "horizon_days": 7
    }
    response = client.post("/api/market-price/", json=payload)
    assert response.status_code == 404
