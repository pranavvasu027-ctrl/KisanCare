import pytest
from fastapi.testclient import TestClient
from ml.main import app
from ml.auth import get_current_user_client
from unittest.mock import MagicMock

# Mock Supabase Client
mock_db = MagicMock()
mock_db.current_user_id = "test-user-123"

def override_get_current_user_client():
    return mock_db

app.dependency_overrides[get_current_user_client] = override_get_current_user_client

client = TestClient(app)

def test_create_farm():
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "farm-1", "user_id": "test-user-123", "farm_name": "Test Farm", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}])
    response = client.post("/api/v1/farms", json={"farm_name": "Test Farm"})
    assert response.status_code == 200
    assert response.json()["id"] == "farm-1"

def test_get_farms():
    mock_db.table().select().eq().execute.return_value = MagicMock(data=[{"id": "farm-1", "user_id": "test-user-123", "farm_name": "Test Farm", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}])
    response = client.get("/api/v1/farms")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_create_field_unauthorized():
    # Mocking the verification step to return empty (not authorized)
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(data=[])
    response = client.post("/api/v1/farms/farm-1/fields", json={"field_name": "Field 1"})
    assert response.status_code == 403

def test_create_field_authorized():
    # Mock farm existence
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(data=[{"id": "farm-1"}])
    # Mock insert
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "field-1", "farm_id": "farm-1", "field_name": "Field 1", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}])
    
    response = client.post("/api/v1/farms/farm-1/fields", json={"field_name": "Field 1"})
    assert response.status_code == 200
    assert response.json()["id"] == "field-1"

def test_get_farm_context():
    mock_db.table().select().eq().eq().execute.return_value = MagicMock(data=[{
        "id": "farm-1", "user_id": "test-user-123", "farm_name": "Test Farm", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00",
        "fields": [
            {
                "id": "field-1", "farm_id": "farm-1", "field_name": "Field 1", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00",
                "seasons": [
                    {"id": "season-1", "field_id": "field-1", "season_name": "Kharif 2026", "status": "ACTIVE", "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}
                ]
            }
        ]
    }])
    response = client.get("/api/v1/farms/farm-1/context")
    assert response.status_code == 200
    assert response.json()["fields"][0]["seasons"][0]["season_name"] == "Kharif 2026"

from unittest.mock import patch
import json

def test_recommend_crops_unauthorized():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[])
    response = client.get("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/recommend-crops")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farm context not found or not authorized"

def test_recommend_crops_insufficient_data():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "NASHIK",
        "fields": [{"id": "field-1", "irrigation_records": [], "seasons": [{"id": "season-1", "season_name": "Kharif"}]}]
    }])
    response = client.get("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/recommend-crops")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "insufficient_data"
    assert "water_availability" in res_data["warnings"][0]

@patch("ml.routers.farms.get_crop_pipeline")
def test_recommend_crops_success(mock_get_pipeline):
    # Setup mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.recommend.return_value = {
        "model_version": "1.0.0",
        "status": "SUCCESS",
        "recommendations": [{"crop": "Rice", "predicted_area_frequency": 0.95}],
        "data_source": "TEST"
    }
    mock_get_pipeline.return_value = mock_pipeline
    
    # Setup db mock
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "NASHIK",
        "fields": [{"id": "field-1", "irrigation_records": [{"water_availability": "High"}], "seasons": [{"id": "season-1", "season_name": "Kharif"}]}]
    }])
    mock_db.table().insert().execute.return_value = MagicMock(data=[{"id": "pred-1"}])
    
    response = client.get("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/recommend-crops")
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "success"
    assert res_data["model_name"] == "crop_recommendation"
    assert res_data["prediction"]["top_recommendation"] == "Rice"
    assert res_data["inputs_used"]["district"] == "NASHIK"
    assert res_data["inputs_used"]["water_availability"] == "High"
    
    # Verify persistence was called
    mock_db.table().insert.assert_called_with({
        "farm_id": "farm-1",
        "field_id": "field-1",
        "season_id": "season-1",
        "model_name": "crop_recommendation",
        "model_version": "1.0.0",
        "prediction": {"top_recommendation": "Rice", "all_recommendations": [{"crop": "Rice", "predicted_area_frequency": 0.95}]},
        "data_provenance": "TEST"
    })
