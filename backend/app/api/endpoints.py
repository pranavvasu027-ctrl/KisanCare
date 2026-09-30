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

@router.get("/farms/{farm_id}/digital-twin")
def get_digital_twin(farm_id: str):
    # Mocking DB retrieval for MVP
    return {
        "farm_id": farm_id,
        "state": {
            "crop": "wheat",
            "soil_moisture": 0.45,
            "temperature": 25.5
        }
    }

@router.post("/predict/crop")
def predict_crop(data: Dict[str, Any]):
    try:
        # Forward to ML service
        response = requests.post(f"{ML_SERVICE_URL}/predict/crop", json=data)
        return response.json()
    except Exception as e:
        # Fallback mock for demo if ML service is down
        return {
            "prediction": "Soybean",
            "confidence": 0.85,
            "unit": "crop_type",
            "factors": ["soil_type", "rainfall"],
            "limitations": ["demo_data"]
        }

@router.post("/economics/calculate")
def get_economics(data: Dict[str, Any]):
    return calculate_economics(data)

@router.post("/simulate")
def simulate(req: SimulationRequest):
    return run_simulation(req.farm_id, req.changes)
