import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_onboarding_successful_validation():
    payload = {
        "farmer_id": "test-farmer-001",
        "name": "Ramesh Patil",
        "phone": "+919876543210",
        "state": "Maharashtra",
        "district": "Akola",
        "village": "Takli Bu",
        "preferred_language": "mr",
        "farming_experience": "10-15 years",
        "farmer_category": "Small / Marginal",
        "farm_name": "Patil Krishi Farm",
        "total_area": 10.5,
        "area_unit": "acre",
        "latitude": 20.7002,
        "longitude": 77.0082,
        "irrigation_source": "Borewell + Drip",
        "land_ownership": "Owned",
        "fields": [
            {
                "field_name": "North Parcel (Wavar 1)",
                "area": 6.0,
                "area_unit": "acre",
                "soil_type": "Black Cotton (Regur)",
                "irrigation_method": "Drip",
                "current_crop": "Cotton",
                "previous_crop": "Soybean"
            },
            {
                "field_name": "South Parcel (Wavar 2)",
                "area": 4.5,
                "area_unit": "acre",
                "soil_type": "Medium Black Loam",
                "irrigation_method": "Rainfed",
                "current_crop": "Soybean",
                "previous_crop": "Wheat"
            }
        ]
    }
    response = client.post("/api/v1/onboarding", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert "farm_id" in data
    assert data["farm_name"] == "Patil Krishi Farm"
    assert data["fields_created"] == 2


def test_onboarding_rejects_missing_required_fields():
    # Missing farmer name
    invalid_payload = {
        "phone": "+919876543210",
        "district": "Akola",
        "village": "Takli Bu",
        "farm_name": "Incomplete Farm",
        "total_area": 5.0,
        "fields": [
            {"field_name": "Field 1", "area": 5.0}
        ]
    }
    response = client.post("/api/v1/onboarding", json=invalid_payload)
    assert response.status_code == 422


def test_onboarding_rejects_non_positive_area():
    payload = {
        "name": "Suresh Rao",
        "phone": "9876543210",
        "district": "Amravati",
        "village": "Akot",
        "farm_name": "Zero Area Farm",
        "total_area": -2.0,  # Invalid negative area
        "fields": [
            {"field_name": "Field 1", "area": 5.0}
        ]
    }
    response = client.post("/api/v1/onboarding", json=payload)
    assert response.status_code == 422


def test_onboarding_requires_at_least_one_field():
    payload = {
        "name": "Suresh Rao",
        "phone": "9876543210",
        "district": "Amravati",
        "village": "Akot",
        "farm_name": "Empty Field Farm",
        "total_area": 5.0,
        "fields": []  # Invalid empty fields
    }
    response = client.post("/api/v1/onboarding", json=payload)
    assert response.status_code == 422
