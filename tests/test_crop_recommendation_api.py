"""Tests for authentic Crop Recommendation API and inference engine."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.crop_service import crop_recommendation_service
from models.crop_recommendation.models import SoilClimateData, CropHistoryInput

client = TestClient(app)


def test_crop_recommendation_service_initialization():
    """Verify that CropRecommendationService initializes authentic RandomForest and KB."""
    crop_recommendation_service.initialize()
    status = crop_recommendation_service.get_status()

    assert status["loaded"] is True
    assert status["status"] == "ready"
    assert "RandomForestClassifier" in status["model_type"]
    assert status["metadata"]["supported_crops"] >= 22
    assert len(status["metadata"]["classes"]) == 22


def test_crop_recommendation_endpoint_valid_payload():
    """Verify POST /api/crop/recommend returns authentic recommendations with all score components."""
    payload = {
        "N": 90.0,
        "P": 42.0,
        "K": 43.0,
        "ph": 6.5,
        "temperature": 26.0,
        "humidity": 75.0,
        "rainfall": 800.0,
        "state": "Maharashtra",
        "district": "Nashik",
        "current_crop": "Cotton",
        "prev_crop_1": "Soybean",
        "top_k": 4,
    }

    response = client.post("/api/crop/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["model"] == "crop_recommendation"
    assert isinstance(data["prediction"], str)
    assert 0.0 <= data["final_score"] <= 1.0
    assert data["is_demo"] is False
    assert len(data["recommendations"]) == 4

    top_rec = data["recommendations"][0]
    assert "crop" in top_rec
    assert 0.0 <= top_rec["soil_climate_score"] <= 1.0
    assert 0.0 <= top_rec["regional_score"] <= 1.0
    assert 0.0 <= top_rec["history_rotation_score"] <= 1.0
    assert 0.0 <= top_rec["final_score"] <= 1.0
    assert len(top_rec["reason"]) > 10

    # Verify NPK status is derived
    assert "N" in data["soil_test_npk_status"]
    assert "P" in data["soil_test_npk_status"]
    assert "K" in data["soil_test_npk_status"]


def test_crop_recommendation_ad_contract_endpoint():
    """Verify POST /api/v1/recommend matches AD Handoff contract."""
    payload = {
        "N": 80.0,
        "P": 40.0,
        "K": 40.0,
        "ph": 6.8,
        "temperature": 24.0,
        "humidity": 80.0,
        "rainfall": 200.0,
        "state": "Punjab",
        "current_crop": "Wheat",
        "top_k": 3,
    }

    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) == 3


def test_crop_recommendation_validation_errors():
    """Verify that invalid inputs (e.g. negative values or out of range pH) produce 422 errors."""
    # Negative N
    resp_negative_n = client.post("/api/crop/recommend", json={"N": -10.0, "P": 40.0, "K": 40.0})
    assert resp_negative_n.status_code == 422

    # pH > 14
    resp_invalid_ph = client.post("/api/crop/recommend", json={"N": 50.0, "P": 40.0, "K": 40.0, "ph": 18.0})
    assert resp_invalid_ph.status_code == 422


def test_soil_test_primacy_invariant():
    """Verify Soil-Test Primacy Invariant: low soil nutrients restrict high-feeder crop ranking."""
    # Severe deficiency in N, P, K with Cotton history
    payload = {
        "N": 10.0,
        "P": 5.0,
        "K": 10.0,
        "ph": 6.5,
        "temperature": 25.0,
        "humidity": 60.0,
        "rainfall": 500.0,
        "state": "Maharashtra",
        "current_crop": "Cotton",
        "top_k": 5,
    }

    response = client.post("/api/crop/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["soil_test_npk_status"]["N"] == "Low"
    assert data["soil_test_npk_status"]["P"] == "Low"
    assert data["soil_test_npk_status"]["K"] == "Low"
