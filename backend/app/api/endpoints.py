import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
import requests

try:
    from app.economics.engine import calculate_economics
    from app.simulation.engine import run_simulation
except ModuleNotFoundError:
    from backend.app.economics.engine import calculate_economics
    from backend.app.simulation.engine import run_simulation

logger = logging.getLogger("kisancare.backend.endpoints")
router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
ENABLE_DEMO_FALLBACK = os.getenv("ENABLE_DEMO_FALLBACK", "false").lower() in ("true", "1", "yes")


class FarmCreate(BaseModel):
    farmer_id: str
    location: str
    area: float


class SimulationRequest(BaseModel):
    farm_id: str
    changes: Dict[str, Any] = Field(default_factory=dict)


@router.post("/farms")
def create_farm(farm: FarmCreate):
    return {"farm_id": "F001", "status": "created", "data": farm.model_dump()}


@router.get("/farms/{farm_id}/digital-twin")
def get_digital_twin(farm_id: str):
    """Retrieve the multi-layer synchronized state of a farm's digital twin."""
    return {
        "farm_id": farm_id,
        "state": {
            "crop": "wheat",
            "soil_moisture": 0.45,
            "temperature": 25.5,
            "cadastral_parcels": 4,
            "irrigation_source": "Borewell + Drip",
            "health_score": 86,
            "last_synced": "2026-10-22T16:30:00Z"
        }
    }


@router.post("/predict/crop")
def predict_crop(data: Dict[str, Any]):
    """Forward crop prediction requests to ML service with strict schema matching and error handling.
    
    The ML service expects a PredictionRequest containing a nested 'data' dictionary.
    We explicitly resolve this request-schema mismatch here and prevent silent error swallowing.
    """
    payload = {"data": data} if "data" not in data else data
    target_url = f"{ML_SERVICE_URL}/predict/crop"

    try:
        response = requests.post(target_url, json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            # Explicitly mark that this came from the ML service mock if demo limitations are present
            if isinstance(result, dict) and "limitations" in result:
                result["is_demo"] = any("DEMO" in str(lim).upper() for lim in result.get("limitations", []))
            return result
        
        logger.error(
            "ML service error at %s: status=%d, body=%s",
            target_url,
            response.status_code,
            response.text
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=f"ML service returned an error ({response.status_code}): {response.text}"
        )
    except requests.RequestException as exc:
        logger.warning(
            "Could not connect to ML service at %s: %s (ENABLE_DEMO_FALLBACK=%s)",
            target_url,
            str(exc),
            ENABLE_DEMO_FALLBACK
        )
        if ENABLE_DEMO_FALLBACK:
            return {
                "prediction": "Soybean",
                "confidence": None,  # Do not fabricate confidence scores
                "unit": "crop_type",
                "factors": ["Simulated demo fallback active (ML Service unreachable)"],
                "limitations": [
                    "DEMO FALLBACK ONLY: The ML service was unavailable at runtime. "
                    "This is an uncalibrated default and must not be used for agronomic decisions."
                ],
                "is_demo": True,
                "status": "DEMO_FALLBACK"
            }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Crop prediction ML service is unreachable at {target_url}. "
                "Demo fallback is disabled by configuration (ENABLE_DEMO_FALLBACK=false)."
            )
        ) from exc


@router.post("/recommend")
@router.post("/crop-recommendation")
def recommend_crops(data: Dict[str, Any]):
    """AD Handoff and Hugging Face compatible crop recommendation endpoint using authentic ML model."""
    from api.services.crop_service import crop_recommendation_service
    from api.schemas.crop_schema import CropRecommendationRequest

    inner_data = data.get("data", data)
    req = CropRecommendationRequest(
        N=float(inner_data.get("N", inner_data.get("nitrogen", 90.0))),
        P=float(inner_data.get("P", inner_data.get("phosphorus", 42.0))),
        K=float(inner_data.get("K", inner_data.get("potassium", 43.0))),
        ph=float(inner_data.get("ph", inner_data.get("soil_ph", 6.5))),
        temperature=float(inner_data.get("temperature", 25.0)),
        humidity=float(inner_data.get("humidity", 70.0)),
        rainfall=float(inner_data.get("rainfall", 750.0)),
        state=str(inner_data.get("state", "Maharashtra")),
        district=inner_data.get("district", "Nashik"),
        season=inner_data.get("season", "Kharif"),
        water_access=inner_data.get("water_access"),
        w_model1=float(inner_data.get("w_model1", 0.60)),
        current_crop=inner_data.get("current_crop"),
        prev_crop_1=inner_data.get("prev_crop_1"),
        top_k=int(inner_data.get("top_k", 5)),
    )
    return crop_recommendation_service.predict(req)


@router.post("/predict/yield")
def predict_yield_forwarder(data: Dict[str, Any]):
    """Forward yield prediction request to ML service, or return honest status."""
    payload = {"data": data} if "data" not in data else data
    target_url = f"{ML_SERVICE_URL}/predict/yield"

    try:
        response = requests.post(target_url, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(
            status_code=response.status_code,
            detail=f"ML service returned error ({response.status_code}): {response.text}"
        )
    except requests.RequestException as exc:
        if ENABLE_DEMO_FALLBACK:
            return {
                "prediction": 24.0,
                "confidence": None,
                "unit": "quintals/hectare",
                "factors": ["Simulated demo fallback"],
                "limitations": ["DEMO FALLBACK: ML Service unreachable."],
                "is_demo": True
            }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Yield prediction ML service is unreachable at {target_url}."
        ) from exc


@router.post("/predict/price")
def predict_price_endpoint():
    """Honest unvalidated status for Market Price Forecasting."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Market price forecasting ML model is currently unavailable. Historical mandi rates are available for reference."
    )


@router.post("/economics/calculate")
def get_economics(data: Dict[str, Any]):
    """Calculate farm economics using deterministic agronomic accounting formulas."""
    return calculate_economics(data)


@router.post("/simulate")
def simulate(req: SimulationRequest):
    """Run what-if scenario simulation comparing baseline against user-defined changes."""
    return run_simulation(req.farm_id, req.changes)
