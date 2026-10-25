"""Tests for Crop Recommendation Endpoint Dual-Model Routing and Agronomic Safeguards."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_crop_recommendation_with_full_soil_and_climate():
    """Verify endpoint runs Hugging Face dual model when soil and climate are provided."""
    payload = {
        "district": "Nashik",
        "season": "Kharif",
        "water_availability": "Medium",
        "N": 90.0,
        "P": 42.0,
        "K": 43.0,
        "ph": 6.5,
        "temperature": 26.0,
        "humidity": 70.0,
        "rainfall": 720.0,
        "top_k": 5,
    }
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "SUCCESS"
    assert "prediction" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 5
    assert len(data["recommendations"]) > 0

    top_item = data["recommendations"][0]
    assert "crop" in top_item
    assert "combined_score" in top_item
    assert "npk_score" in top_item
    assert "region_score" in top_item
    assert "region_suitability" in top_item
    assert "evidence_tier" in top_item
    assert "reason" in top_item
    assert "rank" in top_item
    assert top_item["rank"] == 1

    # Soil status and input summary
    assert "soil_test_npk_status" in data
    assert "warnings" in data
    # High rainfall (720mm) should trigger the scientific extrapolation warning
    assert any("exceeds Model 1 training maximum" in w for w in data["warnings"])


def test_crop_recommendation_legacy_apy_contract():
    """Verify endpoint preserves backward compatibility for legacy 3-field requests."""
    payload = {
        "district": "NASHIK",
        "season": "Rabi",
        "water_availability": "Medium",
        "top_k": 3,
    }
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data.get("status") == "SUCCESS"
    assert data.get("district") == "NASHIK"
    assert data.get("season") == "Rabi"
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3
    if len(data["recommendations"]) > 0:
        assert data["recommendations"][0]["rank"] == 1
        assert "predicted_area_frequency" in data["recommendations"][0]


def test_crop_recommendation_invalid_inputs():
    """Verify empty district or invalid top_k is rejected with 422."""
    bad_district = {
        "district": "",
        "season": "Kharif",
        "water_availability": "Medium",
    }
    res1 = client.post("/api/v1/crop-recommendation", json=bad_district)
    assert res1.status_code == 422

    bad_top_k = {
        "district": "Pune",
        "season": "Kharif",
        "water_availability": "Medium",
        "top_k": 100,  # Max is 20
    }
    res2 = client.post("/api/v1/crop-recommendation", json=bad_top_k)
    assert res2.status_code == 422


def test_crop_recommendation_potassium_extrapolation_warning():
    """Verify potassium > 205 kg/ha triggers Vertisol saturation warning without crashing."""
    payload = {
        "district": "Pune",
        "season": "Kharif",
        "water_availability": "Medium",
        "N": 50.0,
        "P": 30.0,
        "K": 350.0,  # Exceeds Model 1 max 205 kg/ha, common in MH Vertisols
        "ph": 7.2,
        "temperature": 25.0,
        "humidity": 65.0,
        "rainfall": 150.0,
        "top_k": 3,
    }
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("exceeds Model 1 training maximum (205.0 kg/ha)" in w for w in data.get("warnings", []))
