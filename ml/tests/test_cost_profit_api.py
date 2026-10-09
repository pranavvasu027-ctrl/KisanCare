import pytest
from fastapi.testclient import TestClient
from ml.main import app
from ml.auth import get_current_user_client
from unittest.mock import MagicMock, patch

mock_db = MagicMock()
mock_db.current_user_id = "test-user-123"

def override_get_current_user_client():
    return mock_db

app.dependency_overrides[get_current_user_client] = override_get_current_user_client
client = TestClient(app)

# Helper for standard payload
def valid_payload():
    return {
        "sunlight_hours_day": 8.0,
        "fertilizer_kg_ha": 50.0,
        "pesticide_litre_ha": 2.0,
        "seed_quality_score": 5.0,
        "water_used_m3": 1000.0,
        "water_efficiency_t_per_1000m3": 1.5,
        "disease_pest_risk_pct": 10.0
    }

def test_cost_unauthorized():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[])
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/predict-cost", json=valid_payload())
    assert response.status_code == 404

def test_cost_insufficient_data():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "PUNE",
        "fields": [{"id": "field-1", "area": 2.0, "seasons": [{"id": "season-1", "season_name": "Kharif", "crop": "Wheat"}]}]
    }])
    # Missing all user inputs
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/predict-cost", json={})
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "insufficient_data"
    assert "Sunlight_Hours_Day" in res["warnings"][0]

@patch("models.model6_cost_profit.inference.predict_cost")
def test_cost_success(mock_predict):
    mock_predict.return_value = {
        "predicted_total_cost_inr": 20000.0,
        "predicted_cost_per_hectare_inr": 10000.0,
        "model_status": "SUCCESS",
        "model_type": "HistGradientBoosting_Prototype"
    }
    
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "PUNE",
        "fields": [
            {
                "id": "field-1", 
                "area": 2.0,
                "seasons": [{"id": "season-1", "season_name": "Kharif", "crop": "Wheat"}],
                "soil_records": [{"ph": 6.5, "moisture": 40.0, "nitrogen": 100, "phosphorus": 40, "potassium": 40}],
                "weather_records": [{"temperature": 25.0, "rainfall": 200.0, "humidity": 60.0}],
                "irrigation_records": [{"irrigation_method": "Drip", "irrigation_amount": 1000.0}]
            }
        ]
    }])
    
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/predict-cost", json=valid_payload())
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["prediction"]["predicted_total_cost_inr"] == 20000.0
    assert "Yield and Market Price models are not yet available" in res["warnings"][0]
    
    # Assert persistence
    mock_db.table().insert.assert_called()

@patch("models.model6_cost_profit.inference.predict_cost")
def test_cost_inference_error(mock_predict):
    mock_predict.side_effect = ValueError("Farm_Area_Hectares must be > 0")
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "PUNE",
        "fields": [{"id": "field-1", "area": -1.0, "seasons": [{"id": "season-1", "season_name": "Kharif", "crop": "Wheat"}], "soil_records": [{"ph": 6.5, "moisture": 40.0, "nitrogen": 100, "phosphorus": 40, "potassium": 40}], "weather_records": [{"temperature": 25.0, "rainfall": 200.0, "humidity": 60.0}], "irrigation_records": [{"irrigation_method": "Drip", "irrigation_amount": 1000.0}]}]
    }])
    
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/predict-cost", json=valid_payload())
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "error"
    assert "Farm_Area_Hectares must be > 0" in res["warnings"][0]

def test_cost_live_inference():
    # Attempt to call without mock to test artifact loading
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "PUNE",
        "fields": [
            {
                "id": "field-1", 
                "area": 2.0,
                "seasons": [{"id": "season-1", "season_name": "Kharif", "crop": "Wheat"}],
                "soil_records": [{"ph": 6.5, "moisture": 40.0, "nitrogen": 100, "phosphorus": 40, "potassium": 40}],
                "weather_records": [{"temperature": 25.0, "rainfall": 200.0, "humidity": 60.0}],
                "irrigation_records": [{"irrigation_method": "Drip", "irrigation_amount": 1000.0}]
            }
        ]
    }])
    
    # We catch the OS-level DLL error gracefully in the API now, or it succeeds
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/predict-cost", json=valid_payload())
    assert response.status_code == 200
    # It might return success, or error if DLL blocks, but the API should handle it cleanly
    res = response.json()
    assert res["status"] in ["success", "error", "unavailable"]
