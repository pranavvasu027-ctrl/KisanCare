from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ml.rule_based.engine import RuleBasedModels
from ml.market_price.predict import MarketPricePredictor

import os

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# Determine models dir relative to this file
models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
market_predictor = MarketPricePredictor(models_dir=models_dir)

# 1. Disease Detection
class DiseaseRequest(BaseModel):
    crop: str
    symptoms: List[str]

@router.post("/disease-detection")
def detect_disease(req: DiseaseRequest):
    if not req.symptoms:
        raise HTTPException(status_code=422, detail="Symptoms cannot be empty.")
    return RuleBasedModels.detect_disease(req.symptoms, req.crop)

# 2. Pest Detection
class PestRequest(BaseModel):
    crop: str
    symptoms: List[str]

@router.post("/pest-detection")
def detect_pest(req: PestRequest):
    if not req.symptoms:
        raise HTTPException(status_code=422, detail="Symptoms cannot be empty.")
    return RuleBasedModels.detect_pest(req.symptoms, req.crop)

# 3. Soil Nutrient Assessment
class SoilRequest(BaseModel):
    n: float
    p: float
    k: float
    ph: float

@router.post("/soil-assessment")
def assess_soil(req: SoilRequest):
    if req.ph < 0 or req.ph > 14:
        raise HTTPException(status_code=422, detail="Invalid pH value.")
    return RuleBasedModels.assess_soil_nutrients(req.n, req.p, req.k, req.ph)

# 4. Crop Yield Prediction
class YieldRequest(BaseModel):
    crop: str
    area_acres: float
    soil_health_score: float
    weather_score: float

@router.post("/yield-prediction")
def predict_yield(req: YieldRequest):
    if req.area_acres <= 0:
        raise HTTPException(status_code=422, detail="Area must be positive.")
    return RuleBasedModels.predict_yield(req.crop, req.area_acres, req.soil_health_score, req.weather_score)

# 5. Irrigation Recommendation
class IrrigationRequest(BaseModel):
    crop: str
    soil_moisture: float
    days_since_rain: int

@router.post("/irrigation")
def recommend_irrigation(req: IrrigationRequest):
    if req.soil_moisture < 0 or req.soil_moisture > 100:
        raise HTTPException(status_code=422, detail="Soil moisture must be between 0 and 100.")
    return RuleBasedModels.recommend_irrigation(req.crop, req.soil_moisture, req.days_since_rain)

# 6. Weather Risk Assessment
class WeatherRiskRequest(BaseModel):
    temperature: float
    humidity: float
    rainfall_forecast: float

@router.post("/weather-risk")
def assess_weather_risk(req: WeatherRiskRequest):
    if req.humidity < 0 or req.humidity > 100:
        raise HTTPException(status_code=422, detail="Humidity must be between 0 and 100.")
    return RuleBasedModels.assess_weather_risk(req.temperature, req.humidity, req.rainfall_forecast)

# 7. Market Price Forecasting
class MarketPriceRequest(BaseModel):
    crop: str
    market: str
    date: str

@router.post("/market-price")
def forecast_market_price(req: MarketPriceRequest):
    res = market_predictor.predict(req.crop, req.market, req.date)
    if res.get("status") == "error":
        raise HTTPException(status_code=404 if "not found" in res["message"].lower() else 422 if "insufficient" in res["message"].lower() or "gap" in res["message"].lower() else 500, detail=res["message"])
    return res
