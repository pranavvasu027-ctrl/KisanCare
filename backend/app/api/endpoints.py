"""Public backend routes and resilient ML-service proxying."""
from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..economics.engine import calculate_economics
from ..simulation.engine import run_simulation

router = APIRouter()


class FarmCreate(BaseModel):
    farmer_id: str = Field(min_length=1, max_length=128)
    location: str = Field(min_length=1, max_length=256)
    area: float = Field(gt=0)


class SimulationRequest(BaseModel):
    farm_id: str = Field(min_length=1, max_length=128)
    changes: Dict[str, Any]


class CropRecommendationRequest(BaseModel):
    district: str = Field(min_length=1, max_length=128)
    season: str = Field(min_length=1, max_length=32)
    water_availability: str = Field(min_length=1, max_length=32)
    top_k: int = Field(default=5, ge=1, le=20)


class MarketPriceRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    market: str = Field(min_length=1, max_length=128)
    date: str = Field(min_length=1, max_length=32)


class SymptomsRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    symptoms: List[str] = Field(min_length=1)


class SoilRequest(BaseModel):
    n: float
    p: float
    k: float
    ph: float = Field(ge=0, le=14)


class YieldRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    area_acres: float = Field(gt=0)
    soil_health_score: float
    weather_score: float


class IrrigationRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=128)
    soil_moisture: float = Field(ge=0, le=100)
    days_since_rain: int = Field(ge=0)


class WeatherRiskRequest(BaseModel):
    temperature: float
    humidity: float = Field(ge=0, le=100)
    rainfall_forecast: float = Field(ge=0)


def _ml_service_url() -> str:
    return os.getenv("ML_SERVICE_URL", "http://localhost:8001").rstrip("/")


def _ml_timeout_seconds() -> float:
    try:
        return max(0.1, float(os.getenv("ML_SERVICE_TIMEOUT_SECONDS", "8")))
    except ValueError:
        return 8.0


def _proxy_to_ml(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a request and map transport/protocol failures predictably."""
    try:
        response = requests.post(f"{_ml_service_url()}{path}", json=payload, timeout=_ml_timeout_seconds())
    except requests.Timeout as exc:
        raise HTTPException(504, {"code": "ml_service_timeout", "message": "ML service timed out"}) from exc
    except requests.RequestException as exc:
        raise HTTPException(503, {"code": "ml_service_unavailable", "message": "ML service is unavailable"}) from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPException(502, {"code": "ml_service_invalid_response", "message": "ML service returned invalid JSON"}) from exc
    if response.status_code >= 500:
        raise HTTPException(503, {"code": "ml_service_unavailable", "message": "ML service is unavailable"})
    if response.status_code >= 400:
        raise HTTPException(response.status_code, body.get("detail", body))
    if not isinstance(body, dict):
        raise HTTPException(502, {"code": "ml_service_invalid_response", "message": "ML service returned an invalid response body"})
    return body


def _crop_mock(payload: CropRecommendationRequest) -> Dict[str, Any]:
    return {
        "status": "mock", "is_mock": True, "data_provenance": "backend_mock_fallback",
        "message": "ML service is unavailable; this is not a model prediction.",
        "district": payload.district, "season": payload.season, "water_availability": payload.water_availability,
        "recommendations": [{"crop": "Soybean", "rank": 1, "label": "mock recommendation"}],
    }


@router.post("/farms")
def create_farm(farm: FarmCreate):
    return {"farm_id": "F001", "status": "created", "data": farm.model_dump(), "is_mock": True}


@router.get("/digital-twin/{farm_id}")
def get_digital_twin(farm_id: str):
    return {"farm_id": farm_id, "name": f"Farm {farm_id}", "area_acres": 10, "healthScore": 85,
            "climate": {"temperature": 25.5, "weather_condition": "Sunny", "humidity": 60},
            "state": {"crop": "wheat", "soil_moisture": 0.45, "temperature": 25.5},
            "is_mock": True, "data_provenance": "backend_mock"}


@router.post("/crop-recommendation")
def predict_crop(data: CropRecommendationRequest):
    try:
        return _proxy_to_ml("/api/v1/crop-recommendation", data.model_dump())
    except HTTPException as exc:
        if exc.status_code == 503 and os.getenv("ML_MOCK_FALLBACK_ENABLED", "false").lower() == "true":
            return _crop_mock(data)
        raise


@router.post("/market-price")
def get_market_price(data: MarketPriceRequest):
    return _proxy_to_ml("/api/v1/models/market-price", data.model_dump())


@router.post("/disease-detection")
def detect_disease(data: SymptomsRequest):
    return _proxy_to_ml("/api/v1/models/disease-detection", data.model_dump())


@router.post("/pest-detection")
def detect_pest(data: SymptomsRequest):
    return _proxy_to_ml("/api/v1/models/pest-detection", data.model_dump())


@router.post("/soil-assessment")
def assess_soil(data: SoilRequest):
    return _proxy_to_ml("/api/v1/models/soil-assessment", data.model_dump())


@router.post("/yield-prediction")
def predict_yield(data: YieldRequest):
    return _proxy_to_ml("/api/v1/models/yield-prediction", data.model_dump())


@router.post("/irrigation")
def recommend_irrigation(data: IrrigationRequest):
    return _proxy_to_ml("/api/v1/models/irrigation", data.model_dump())


@router.post("/weather-risk")
def assess_weather_risk(data: WeatherRiskRequest):
    return _proxy_to_ml("/api/v1/models/weather-risk", data.model_dump())


@router.post("/economics/calculate")
def get_economics(data: Dict[str, Any]):
    return calculate_economics(data)


@router.post("/simulate")
def simulate(req: SimulationRequest):
    return run_simulation(req.farm_id, req.changes)
