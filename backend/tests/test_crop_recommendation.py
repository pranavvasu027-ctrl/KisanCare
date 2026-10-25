import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_crop_recommendation_meta():
    """Verify crop recommendation meta endpoint returns model information."""
    response = client.get("/api/v1/crop-recommendation/meta")
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data
    assert "supported_crops" in data
    assert "supported_seasons" in data


def test_crop_recommendation_akola_kharif():
    """Verify real ML crop recommendation inference for Akola in Kharif season."""
    payload = {
        "district": "AKOLA",
        "season": "Kharif",
        "water_availability": "Medium",
        "top_k": 5
    }
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["district"] == "AKOLA"
    assert data["season"] == "Kharif"
    assert len(data["recommendations"]) > 0

    # Verify ranking monotonicity and top crops
    crops = [r["crop"] for r in data["recommendations"]]
    assert "Cotton" in crops
    assert "Soybean" in crops

    for i in range(len(data["recommendations"]) - 1):
        assert data["recommendations"][i]["predicted_area_frequency"] >= data["recommendations"][i + 1]["predicted_area_frequency"]


def test_crop_recommendation_invalid_district():
    """Verify unknown district rejection without fabricating outputs."""
    payload = {
        "district": "INVALID_DISTRICT_XYZ",
        "season": "Kharif",
        "water_availability": "Medium",
        "top_k": 5
    }
    response = client.post("/api/v1/crop-recommendation", json=payload)
    assert response.status_code in [404, 422]


def test_farms_listing():
    """Verify farm listing endpoint returns registered farms."""
    response = client.get("/api/v1/farms")
    assert response.status_code == 200
    data = response.json()
    assert "farms" in data
    assert len(data["farms"]) > 0
    farm = data["farms"][0]
    assert "id" in farm
    assert "farm_name" in farm
    assert "location" in farm


def test_assign_farm_crop_success():
    """Verify assigning a chosen crop to a farm parcel updates active_crop and sowing_date."""
    # 1. Get farm ID
    farms_res = client.get("/api/v1/farms")
    assert farms_res.status_code == 200
    farm_id = farms_res.json()["farms"][0]["id"]

    # 2. Assign crop
    payload = {
        "crop": "Cotton",
        "sowing_date": "25 Oct 2026"
    }
    response = client.put(f"/api/v1/farms/{farm_id}/crop", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["farm_id"] == farm_id
    assert data["active_crop"] == "Cotton"
    assert data["sowing_date"] == "25 Oct 2026"

    # 3. Verify in farm listing
    check_res = client.get("/api/v1/farms")
    target = next((f for f in check_res.json()["farms"] if f["id"] == farm_id), None)
    assert target is not None
    assert target.get("active_crop") == "Cotton"


def test_assign_farm_crop_invalid():
    """Verify 422 on empty crop and 404 on non-existent farm."""
    # Empty crop
    farms_res = client.get("/api/v1/farms")
    farm_id = farms_res.json()["farms"][0]["id"]
    res_empty = client.put(f"/api/v1/farms/{farm_id}/crop", json={"crop": "", "sowing_date": "2026-10-25"})
    assert res_empty.status_code == 422

    # Non-existent farm
    res_404 = client.put("/api/v1/farms/non-existent-farm-id-9999/crop", json={"crop": "Cotton"})
    assert res_404.status_code == 404
