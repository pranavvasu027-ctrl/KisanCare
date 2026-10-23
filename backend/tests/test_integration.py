import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_digital_twin():
    response = client.get("/api/v1/farms/F001/digital-twin")
    assert response.status_code == 200
    data = response.json()
    assert data["farm_id"] == "F001"
    assert "state" in data
    assert data["state"]["crop"] == "wheat"
    assert data["state"]["soil_moisture"] == 0.45


def test_simulate():
    response = client.post("/api/v1/simulate", json={
        "farm_id": "F001",
        "changes": {"rainfall_change_percent": -20}
    })
    assert response.status_code == 200
    data = response.json()
    assert "baseline" in data
    assert "scenario" in data
    assert "differences" in data
    assert "explanation" in data
    assert data["scenario"]["yield"] < data["baseline"]["yield"]


def test_economics_calculation():
    response = client.post("/api/v1/economics/calculate", json={
        "expected_yield": 20,
        "expected_price": 3000,
        "input_cost": 10000,
        "labour_cost": 15000,
        "irrigation_cost": 5000
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == 30000
    assert data["expected_revenue"] == 60000
    assert data["expected_profit"] == 30000
    assert data["roi_percent"] == 100.0
    assert data["break_even_price"] == 1500.0


def test_crop_prediction_schema_forwarding():
    """Verify that crop prediction correctly wraps payload in {'data': ...} and handles ML service."""
    mock_ml_response = {
        "prediction": "Soybean",
        "confidence": 0.82,
        "unit": "crop_type",
        "factors": ["Favorable rainfall"],
        "limitations": ["DEMO DATA - NOT REAL PREDICTION"]
    }
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_ml_response

        response = client.post("/api/v1/predict/crop", json={
            "location": "Nashik",
            "soil_type": "Black",
            "weather": {"rainfall": 700}
        })

        assert response.status_code == 200
        # Ensure requests.post was called with {'data': ...}
        called_args, called_kwargs = mock_post.call_args
        assert "json" in called_kwargs
        assert "data" in called_kwargs["json"]
        assert called_kwargs["json"]["data"]["location"] == "Nashik"


def test_crop_prediction_ml_down_no_silent_fallback_by_default():
    """Verify that if ML service is unreachable, it raises 503 rather than silently returning a fake prediction."""
    import requests
    with patch("requests.post", side_effect=requests.RequestException("Connection refused")):
        with patch.dict(os.environ, {"ENABLE_DEMO_FALLBACK": "false"}):
            # re-import or reload endpoints setting
            from app.api import endpoints
            endpoints.ENABLE_DEMO_FALLBACK = False

            response = client.post("/api/v1/predict/crop", json={"soil_type": "Loam"})
            assert response.status_code == 503
            assert "unreachable" in response.json()["detail"].lower()


def test_crop_prediction_ml_down_explicit_demo_fallback():
    """Verify that if demo fallback is explicitly enabled via config, it is visibly labelled."""
    import requests
    with patch("requests.post", side_effect=requests.RequestException("Connection refused")):
        from app.api import endpoints
        endpoints.ENABLE_DEMO_FALLBACK = True

        response = client.post("/api/v1/predict/crop", json={"soil_type": "Loam"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_demo") is True
        assert data.get("confidence") is None  # Never fake confidence score
        assert any("DEMO" in lim for lim in data.get("limitations", []))


def test_market_price_prediction_honestly_unavailable():
    """Verify market price prediction endpoint returns 501 with honest explanation."""
    response = client.post("/api/v1/predict/price")
    assert response.status_code == 501
    assert "unavailable" in response.json()["detail"].lower()
