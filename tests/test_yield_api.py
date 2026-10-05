"""Tests for Crop Yield Prediction API endpoint."""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_valid_yield_prediction():
    """Test standard crop yield prediction with valid agronomic features."""
    payload = {
        "state": "Punjab",
        "crop": "Wheat",
        "season": "Rabi",
        "soil_type": "Alluvial",
        "area": 10.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 65.0,
        "nitrogen": 120.0,
        "phosphorus": 50.0,
        "potassium": 40.0,
    }
    response = client.post("/api/yield/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["model"] == "yield"

    pred = data["prediction"]
    assert pred["predicted_yield"] > 0
    assert pred["yield_unit"] == "quintal/hectare"
    assert pred["production_unit"] == "quintal"
    assert pred["cultivated_area_hectares"] == 10.0

    # Production must equal predicted_yield * area
    expected_prod = pred["predicted_yield"] * pred["cultivated_area_hectares"]
    assert abs(pred["estimated_production"] - expected_prod) < 1e-4

    assert "model_source" in pred
    assert pred["input_summary"]["state"] == "Punjab"
    assert pred["input_summary"]["crop"] == "Wheat"


def test_invalid_area_zero_or_negative():
    """Area <= 0 must be rejected with 422."""
    payload = {
        "state": "Punjab",
        "crop": "Wheat",
        "season": "Rabi",
        "soil_type": "Loamy",
        "area": 0.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 65.0,
        "nitrogen": 120.0,
        "phosphorus": 50.0,
        "potassium": 40.0,
    }
    response = client.post("/api/yield/predict", json=payload)
    assert response.status_code == 422


def test_invalid_humidity_out_of_bounds():
    """Humidity outside [0, 100] must be rejected with 422."""
    payload = {
        "state": "Punjab",
        "crop": "Wheat",
        "season": "Rabi",
        "soil_type": "Loamy",
        "area": 5.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 150.0,
        "nitrogen": 120.0,
        "phosphorus": 50.0,
        "potassium": 40.0,
    }
    response = client.post("/api/yield/predict", json=payload)
    assert response.status_code == 422


def test_unseen_state_rejection():
    """Unseen Indian state should return 422 with clear category validation error."""
    payload = {
        "state": "Atlantis",
        "crop": "Wheat",
        "season": "Rabi",
        "soil_type": "Loamy",
        "area": 5.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 60.0,
        "nitrogen": 100.0,
        "phosphorus": 50.0,
        "potassium": 50.0,
    }
    response = client.post("/api/yield/predict", json=payload)
    assert response.status_code == 422
    assert "Unsupported State" in response.json()["detail"]


def test_unseen_crop_rejection():
    """Unseen crop should return 422 with clear category validation error."""
    payload = {
        "state": "Punjab",
        "crop": "Kryptonite",
        "season": "Rabi",
        "soil_type": "Loamy",
        "area": 5.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 60.0,
        "nitrogen": 100.0,
        "phosphorus": 50.0,
        "potassium": 50.0,
    }
    response = client.post("/api/yield/predict", json=payload)
    assert response.status_code == 422
    assert "Unsupported Crop" in response.json()["detail"]
