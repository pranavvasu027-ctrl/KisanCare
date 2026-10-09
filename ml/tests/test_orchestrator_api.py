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

def default_db_mock():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[{
        "location": "PUNE",
        "fields": [
            {
                "id": "field-1", 
                "area": 2.0,
                "seasons": [{"id": "season-1", "season_name": "Kharif", "crop": "Wheat"}],
                "soil_records": [{"ph": 6.5, "moisture": 40.0, "nitrogen": 100, "phosphorus": 40, "potassium": 40}],
                "weather_records": [{"temperature": 25.0, "rainfall": 200.0, "humidity": 60.0}],
                "irrigation_records": [{"irrigation_method": "Drip", "irrigation_amount": 1000.0, "water_availability": "Medium"}]
            }
        ]
    }])
    mock_db.table().insert.reset_mock()

def get_cost_inputs():
    return {
        "sunlight_hours_day": 8.0,
        "fertilizer_kg_ha": 50.0,
        "pesticide_litre_ha": 2.0,
        "seed_quality_score": 5.0,
        "water_used_m3": 1000.0,
        "water_efficiency_t_per_1000m3": 1.5,
        "disease_pest_risk_pct": 10.0
    }

def test_orch_unauthorized():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[])
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/orchestrate", json={"models": ["crop_recommendation"]})
    assert response.status_code == 404

def test_orch_unknown_model():
    default_db_mock()
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/orchestrate", json={"models": ["imaginary_model"]})
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "error"
    assert "imaginary_model" in res["results"]
    assert res["results"]["imaginary_model"]["status"] == "error"

def test_orch_unavailable_model():
    default_db_mock()
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/orchestrate", json={"models": ["yield_prediction"]})
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "partial"
    assert res["results"]["yield_prediction"]["status"] == "unavailable"

@patch("ml.orchestrator.ModelOrchestrator._execute_crop_recommendation")
@patch("ml.orchestrator.ModelOrchestrator._execute_cost_prediction")
def test_orch_success_both(mock_cost, mock_crop):
    from ml.schemas.prediction import ModelResult
    import datetime
    
    mock_crop.return_value = ModelResult(
        model_name="crop_recommendation", model_version="1.0", status="success",
        prediction={"recommendations": []}, data_provenance="dt", timestamp=datetime.datetime.utcnow(), inputs_used={}
    )
    mock_cost.return_value = ModelResult(
        model_name="cost_prediction", model_version="1.0", status="success",
        prediction={"cost": 100}, data_provenance="dt", timestamp=datetime.datetime.utcnow(), inputs_used={}
    )
    
    default_db_mock()
    response = client.post(
        "/api/v1/farms/farm-1/fields/field-1/seasons/season-1/orchestrate", 
        json={"models": ["crop_recommendation", "cost_prediction"], "cost_prediction_inputs": get_cost_inputs()}
    )
    
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["results"]["crop_recommendation"]["status"] == "success"
    assert res["results"]["cost_prediction"]["status"] == "success"
    assert mock_db.table().insert.call_count == 2

@patch("ml.orchestrator.ModelOrchestrator._execute_crop_recommendation")
@patch("ml.orchestrator.ModelOrchestrator._execute_cost_prediction")
def test_orch_independent_failures(mock_cost, mock_crop):
    from ml.schemas.prediction import ModelResult
    import datetime
    
    # Crop succeeds
    mock_crop.return_value = ModelResult(
        model_name="crop_recommendation", model_version="1.0", status="success",
        prediction={"recommendations": []}, data_provenance="dt", timestamp=datetime.datetime.utcnow(), inputs_used={}
    )
    # Cost has insufficient data
    mock_cost.return_value = ModelResult(
        model_name="cost_prediction", model_version="unknown", status="insufficient_data",
        prediction={}, data_provenance="dt", timestamp=datetime.datetime.utcnow(), inputs_used={}
    )
    
    default_db_mock()
    response = client.post(
        "/api/v1/farms/farm-1/fields/field-1/seasons/season-1/orchestrate", 
        json={"models": ["crop_recommendation", "cost_prediction"]}
    )
    
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "partial"
    assert res["results"]["crop_recommendation"]["status"] == "success"
    assert res["results"]["cost_prediction"]["status"] == "insufficient_data"
    
    # Only crop should be persisted! (Wait, my logic currently persists any "success")
    assert mock_db.table().insert.call_count == 1
    
    args, kwargs = mock_db.table().insert.call_args
    assert args[0]["model_name"] == "crop_recommendation"

