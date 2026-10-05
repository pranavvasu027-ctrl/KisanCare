"""Tests for Irrigation Prediction API endpoint."""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_valid_irrigation_prediction_stressed():
    """Test irrigation prediction when soil moisture is low (stress condition)."""
    payload = {
        "crop": "wheat",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 0.15,
        "rainfall": 0.0,
        "decision_date": "2026-10-05",
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["model"] == "irrigation"

    pred = data["prediction"]
    assert pred["irrigation_required"] is True
    assert pred["irrigation_quantity_mm"] > 0
    assert pred["irrigation_timing"] in ["today", "within_24h"]
    assert pred["crop"] == "wheat"
    assert pred["crop_stage"] == "mid"
    assert pred["soil_type"] == "loam"

    wb = pred["water_balance"]
    assert "soil_water_depletion_mm" in wb
    assert "total_available_water_mm" in wb
    assert "readily_available_water_mm" in wb
    assert "crop_evapotranspiration_mm" in wb
    assert "reference_eto_mm" in wb
    assert "net_irrigation_requirement_mm" in wb
    assert wb["total_available_water_mm"] > 0

    assert "units" in pred
    assert pred["units"]["irrigation_quantity"] == "mm"


def test_valid_irrigation_prediction_saturated():
    """Test irrigation prediction when soil is saturated (no irrigation needed)."""
    payload = {
        "crop": "wheat",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 0.35,  # above field capacity for loam (0.25)
        "rainfall": 10.0,
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    pred = data["prediction"]
    assert pred["irrigation_required"] is False
    assert pred["irrigation_quantity_mm"] == 0.0
    assert pred["irrigation_timing"] == "none"
    assert "SOIL_SATURATED_OR_ABOVE_FIELD_CAPACITY" in pred["decision_reason_codes"]


def test_invalid_soil_moisture_out_of_bounds():
    """Soil moisture above 1.0 or below 0.0 should be rejected with 422."""
    payload = {
        "crop": "wheat",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 1.5,
        "rainfall": 0.0,
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 422


def test_invalid_negative_rainfall():
    """Negative rainfall should be rejected with 422."""
    payload = {
        "crop": "wheat",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 0.20,
        "rainfall": -5.0,
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 422


def test_unsupported_crop():
    """Unsupported crop should return 422 with informative message."""
    payload = {
        "crop": "nonexistent_crop_xyz",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 0.20,
        "rainfall": 0.0,
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 422
    assert "Unsupported crop" in response.json()["detail"]


def test_unsupported_crop_stage():
    """Unsupported crop stage should return 422 with informative message."""
    payload = {
        "crop": "wheat",
        "crop_stage": "flowering_super_stage",
        "soil_type": "loam",
        "soil_moisture": 0.20,
        "rainfall": 0.0,
    }
    response = client.post("/api/irrigation/predict", json=payload)
    assert response.status_code == 422
    assert "Unsupported crop_stage" in response.json()["detail"]
