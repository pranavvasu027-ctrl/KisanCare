import pytest
from fastapi.testclient import TestClient
from ml.main import app
from ml.auth import get_current_user_client
from unittest.mock import MagicMock, patch
from ml.schemas.prediction import ModelResult
from datetime import datetime

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

def get_base_payload():
    return {
        "decision_type": "crop_selection",
        "preferences": {
            "water_conservation_priority": False
        },
        "cost_prediction_inputs": {
            "sunlight_hours_day": 8.0,
            "fertilizer_kg_ha": 50.0,
            "pesticide_litre_ha": 2.0,
            "seed_quality_score": 5.0,
            "water_used_m3": 1000.0,
            "water_efficiency_t_per_1000m3": 1.5,
            "disease_pest_risk_pct": 10.0
        }
    }

def test_decide_unauthorized():
    mock_db.table().select().eq().eq().eq().eq().execute.return_value = MagicMock(data=[])
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/decide", json=get_base_payload())
    assert response.status_code == 404

@patch("ml.orchestrator.ModelOrchestrator._execute_crop_recommendation")
@patch("ml.orchestrator.ModelOrchestrator._execute_cost_prediction")
def test_decide_success(mock_cost, mock_crop):
    mock_crop.return_value = ModelResult(
        model_name="crop_recommendation", model_version="1.0", status="success",
        prediction={"recommendations": [{"crop": "Wheat", "probability": 0.8, "rank": 1}, {"crop": "Rice", "probability": 0.6, "rank": 2}]},
        data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    mock_cost.return_value = ModelResult(
        model_name="cost_prediction", model_version="1.0", status="success",
        prediction={"predicted_total_cost_inr": 20000}, data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    default_db_mock()
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/decide", json=get_base_payload())
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ready"
    assert res["primary_recommendation"]["identifier"] == "REC-0"
    assert res["primary_recommendation"]["recommended_action"] == "Cultivate Wheat"
    # Rice is in alternatives
    assert len(res["alternatives"]) == 1
    assert res["alternatives"][0]["recommended_action"] == "Cultivate Rice"

@patch("ml.orchestrator.ModelOrchestrator._execute_crop_recommendation")
@patch("ml.orchestrator.ModelOrchestrator._execute_cost_prediction")
def test_decide_water_conservation_conflict(mock_cost, mock_crop):
    mock_crop.return_value = ModelResult(
        model_name="crop_recommendation", model_version="1.0", status="success",
        prediction={"recommendations": [{"crop": "Rice", "probability": 0.9, "rank": 1}, {"crop": "Wheat", "probability": 0.8, "rank": 2}]},
        data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    mock_cost.return_value = ModelResult(
        model_name="cost_prediction", model_version="unknown", status="insufficient_data",
        prediction={}, data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    default_db_mock()
    payload = get_base_payload()
    payload["preferences"]["water_conservation_priority"] = True
    
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/decide", json=payload)
    assert response.status_code == 200
    res = response.json()
    
    # Primary recommendation should jump to Wheat because Rice throws a Hard Constraint Conflict
    assert res["primary_recommendation"]["recommended_action"] == "Cultivate Wheat"
    assert res["primary_recommendation"]["warnings"] == []
    
    # Rice should be in alternatives, with a warning
    assert "Cultivate Rice" in res["alternatives"][0]["recommended_action"]
    assert "Hard Constraint Conflict" in res["alternatives"][0]["warnings"][0]

@patch("ml.orchestrator.ModelOrchestrator._execute_crop_recommendation")
@patch("ml.orchestrator.ModelOrchestrator._execute_cost_prediction")
def test_decide_missing_crop_model(mock_cost, mock_crop):
    mock_crop.return_value = ModelResult(
        model_name="crop_recommendation", model_version="1.0", status="insufficient_data",
        prediction={}, data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    mock_cost.return_value = ModelResult(
        model_name="cost_prediction", model_version="1.0", status="success",
        prediction={"predicted_total_cost_inr": 20000}, data_provenance="dt", timestamp=datetime.utcnow(), inputs_used={}
    )
    default_db_mock()
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/decide", json=get_base_payload())
    assert response.status_code == 200
    res = response.json()
    
    assert res["status"] == "needs_more_data"
    assert res["primary_recommendation"] is None
    assert "Crop Recommendation is unavailable" in res["missing_information"][0]
    
def test_decide_unsupported_type():
    default_db_mock()
    payload = get_base_payload()
    payload["decision_type"] = "unsupported_decision"
    response = client.post("/api/v1/farms/farm-1/fields/field-1/seasons/season-1/decide", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "blocked"
    assert "Unsupported decision type" in res["missing_information"][0]
