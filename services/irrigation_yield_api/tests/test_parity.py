"""Tests verifying exact numerical parity between direct model inference and FastAPI endpoints."""

import math
from fastapi.testclient import TestClient

from api.main import app
from models.crop_yield.predictor import predict_crop_yield
from models.irrigation.engine import predict_irrigation

client = TestClient(app)


def test_irrigation_parity():
    """Verify API prediction strictly matches direct Python model inference for identical inputs."""
    irrigation_inputs = [
        {
            "crop": "wheat",
            "crop_stage": "mid",
            "soil_type": "loam",
            "soil_moisture": 0.15,
            "rainfall": 0.0,
            "decision_date": "2026-10-05",
        },
        {
            "crop": "wheat",
            "crop_stage": "initial",
            "soil_type": "clay",
            "soil_moisture": 0.28,
            "rainfall": 5.0,
            "decision_date": "2026-10-05",
        },
    ]

    for inp in irrigation_inputs:
        # 1. Direct Python function inference
        direct_result = predict_irrigation(**inp)

        # 2. FastAPI endpoint inference
        response = client.post("/api/irrigation/predict", json=inp)
        assert response.status_code == 200
        api_data = response.json()["prediction"]

        # Parity assertions
        assert api_data["irrigation_required"] == direct_result.irrigation_required
        assert math.isclose(api_data["irrigation_quantity_mm"], direct_result.irrigation_quantity_mm, abs_tol=1e-3)
        assert api_data["irrigation_timing"] == direct_result.irrigation_timing
        assert api_data["decision_reason_codes"] == direct_result.decision_reason_codes

        direct_wb = direct_result.water_balance
        api_wb = api_data["water_balance"]
        assert math.isclose(api_wb["soil_water_depletion_mm"], direct_wb.soil_water_depletion_mm, abs_tol=1e-3)
        assert math.isclose(api_wb["total_available_water_mm"], direct_wb.total_available_water_mm, abs_tol=1e-3)
        assert math.isclose(api_wb["readily_available_water_mm"], direct_wb.readily_available_water_mm, abs_tol=1e-3)
        assert math.isclose(api_wb["crop_evapotranspiration_mm"], direct_wb.crop_evapotranspiration_mm, abs_tol=1e-3)
        assert math.isclose(api_wb["reference_eto_mm"], direct_wb.reference_eto_mm, abs_tol=1e-3)
        assert math.isclose(api_wb["net_irrigation_requirement_mm"], direct_wb.net_irrigation_requirement_mm, abs_tol=1e-3)


def test_yield_parity():
    """Verify API crop yield prediction strictly matches direct Python model inference for identical inputs."""
    yield_inputs = [
        {
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
        },
        {
            "state": "Uttar Pradesh",
            "crop": "Rice",
            "season": "Kharif",
            "soil_type": "Clay",
            "area": 5.5,
            "rainfall": 950.0,
            "temperature": 28.0,
            "humidity": 80.0,
            "nitrogen": 90.0,
            "phosphorus": 40.0,
            "potassium": 35.0,
        },
    ]

    for inp in yield_inputs:
        # 1. Direct Python function inference
        direct_result = predict_crop_yield(**inp)

        # 2. FastAPI endpoint inference
        response = client.post("/api/yield/predict", json=inp)
        assert response.status_code == 200
        api_data = response.json()["prediction"]

        # Parity assertions
        assert math.isclose(api_data["predicted_yield"], direct_result.predicted_yield, abs_tol=1e-4)
        assert math.isclose(api_data["estimated_production"], direct_result.estimated_production, abs_tol=1e-4)
        assert api_data["yield_unit"] == direct_result.yield_unit
        assert api_data["production_unit"] == direct_result.production_unit
        assert api_data["cultivated_area_hectares"] == direct_result.cultivated_area_hectares
        assert api_data["model_source"] == direct_result.model_source
