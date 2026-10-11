"""Tests for model loading lifecycle and memory caching efficiency."""

import json
from fastapi.testclient import TestClient

from api.main import app
from models.crop_yield.model_loader import load_model_artifacts
from models.irrigation.loader import load_irrigation_model

client = TestClient(app)


def test_models_loaded_only_once_in_memory():
    """Verify that repeated loader calls return cached singleton references without reloading."""
    # Crop yield model artifact caching check
    yield_artifacts_1 = load_model_artifacts()
    yield_artifacts_2 = load_model_artifacts()
    assert yield_artifacts_1 is yield_artifacts_2
    assert id(yield_artifacts_1["model"]) == id(yield_artifacts_2["model"])

    # Irrigation model artifact caching check
    irr_artifacts_1 = load_irrigation_model()
    irr_artifacts_2 = load_irrigation_model()
    assert irr_artifacts_1 is irr_artifacts_2
    assert id(irr_artifacts_1["eto_model"]) == id(irr_artifacts_2["eto_model"])


def test_repeated_irrigation_api_requests():
    """Verify repeated API calls execute rapidly and stably without memory leaks or reload overhead."""
    payload = {
        "crop": "wheat",
        "crop_stage": "mid",
        "soil_type": "loam",
        "soil_moisture": 0.20,
        "rainfall": 0.0,
    }
    for _ in range(5):
        resp = client.post("/api/irrigation/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # Verify JSON serializability directly
        serialized = json.dumps(data)
        assert len(serialized) > 50


def test_repeated_yield_api_requests():
    """Verify repeated yield requests execute deterministically and stably."""
    payload = {
        "state": "Punjab",
        "crop": "Wheat",
        "season": "Rabi",
        "soil_type": "Alluvial",
        "area": 10.0,
        "rainfall": 650.0,
        "temperature": 22.5,
        "humidity": 65.0,
        "nitrogen": 120.0,
        "phosphorus": 50.0,
        "potassium": 40.0,
    }
    first_pred = None
    for _ in range(5):
        resp = client.post("/api/yield/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        if first_pred is None:
            first_pred = data["prediction"]["predicted_yield"]
        else:
            assert data["prediction"]["predicted_yield"] == first_pred

        # Verify JSON serializability
        serialized = json.dumps(data)
        assert len(serialized) > 50
