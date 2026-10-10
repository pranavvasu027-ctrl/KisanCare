from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.economics.engine import calculate_economics
from app.simulation.engine import run_simulation
import requests
import os

router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")

class FarmCreate(BaseModel):
    farmer_id: str
    location: str
    area: float

class SimulationRequest(BaseModel):
    farm_id: str
    changes: Dict[str, Any]

@router.post("/farms")
def create_farm(farm: FarmCreate):
    return {"farm_id": "F001", "status": "created", "data": farm.model_dump()}

@router.get("/digital-twin/{farm_id}")
def get_digital_twin(farm_id: str):
    # Mocking DB retrieval for MVP
    return {
        "farm_id": farm_id,
        "name": f"Farm {farm_id}",
        "area_acres": 10,
        "healthScore": 85,
        "climate": { "temperature": 25.5, "weather_condition": "Sunny", "humidity": 60 },
        "state": {
            "crop": "wheat",
            "soil_moisture": 0.45,
            "temperature": 25.5
        }
    }

@router.post("/crop-recommendation")
def predict_crop(data: Dict[str, Any]):
    try:
        # Forward to ML service
        response = requests.post(f"{ML_SERVICE_URL}/api/v1/crop-recommendation", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"ML Service returned {response.status_code}: {response.text}")
    except Exception as e:
        # Fallback mock for demo if ML service is down
        print(f"Error calling ML service: {e}")
        return {
            "recommendations": [
                {"crop": "Soybean (Fallback)", "score": 92, "expected_yield": 2.8, "predicted_profit": 42000, "water_requirement": "Medium", "tags": ["High Profit"]}
            ],
            "isDemo": True
        }

@router.post("/market-price/")
def get_market_price_dummy(data: Dict[str, Any]):
    # Temporary mock since market_price module is missing
    return {
        "current_price": 4650,
        "trend": "+4.2%",
        "forecast_min": 4700,
        "forecast_max": 4800,
        "nearby_markets": [
            { "name": "Nagpur APMC", "distance": 24, "price": 4680, "arrivals": 450, "trend": "+20" }
        ]
    }

@router.post("/economics/calculate")
def get_economics(data: Dict[str, Any]):
    return calculate_economics(data)

@router.post("/simulate")
def simulate(req: SimulationRequest):
    return run_simulation(req.farm_id, req.changes)
