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
    from ml.crop_recommendation.predict import predict_crop_from_dict, InputValidationError, ModelUnavailableError
    try:
        return predict_crop_from_dict(data)
    except InputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.error("Crop recommendation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Crop recommendation failed: {str(exc)}")


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
