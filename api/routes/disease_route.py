"""FastAPI route definitions for KisanCare Plant Pathology & Disease Detection API."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from api.schemas.disease_schema import (
    DiseasePredictionRequestJSON,
    DiseasePredictionResponse,
)
from api.services.disease_service import (
    InvalidImageError,
    ModelUnavailableError,
    disease_detection_service,
)
try:
    from models.disease_detection.specialists.registry import specialist_registry
except ImportError:
    from specialists.registry import specialist_registry

logger = logging.getLogger("kisancare.api.disease")

router = APIRouter(tags=["Disease & Pathology Detection"])


@router.get(
    "/api/disease/status",
    summary="Get Disease Model Diagnostic Status",
    response_model=Dict[str, Any],
)
def get_disease_status():
    """Return model readiness, loaded status, and parameter counts."""
    return disease_detection_service.get_status()


@router.get(
    "/api/disease/specialists",
    summary="List Registered Specialist Models",
    response_model=Dict[str, Any],
)
def get_specialists_registry():
    """Return status and metadata for all crop specialist models."""
    return specialist_registry.get_registry_status()


@router.get(
    "/api/disease/classes",
    summary="List Supported Pathologies and Host Crops",
    response_model=Dict[str, Any],
)
def get_supported_classes():
    """Return all supported classes and host crop taxonomy from the active engine."""
    status_info = disease_detection_service.get_status()
    return {
        "num_classes": status_info.get("classes_count", 387),
        "crops_count": status_info.get("crops_count", 59),
        "classes": status_info.get("classes", []),
        "supported_crops": status_info.get("supported_crops", [
            "Apple", "Blueberry", "Cherry", "Corn", "Grape", "Orange",
            "Peach", "Pepper Bell", "Potato", "Raspberry", "Soybean",
            "Squash", "Strawberry", "Tomato", "Cotton", "Rice", "Wheat"
        ]),
        "active_engine": status_info.get("active_engine"),
    }


@router.get(
    "/api/disease/engine",
    summary="Get Active Model Engine and Rollback Status",
    response_model=Dict[str, Any],
)
def get_disease_engine():
    """Return active engine name and availability of primary and rollback engines."""
    status_info = disease_detection_service.get_status()
    return {
        "active_engine": status_info.get("active_engine"),
        "primary_engine_available": status_info.get("primary_engine_available"),
        "rollback_engine_available": status_info.get("rollback_engine_available"),
    }


@router.post(
    "/api/disease/engine",
    summary="Switch Active Disease Detection Engine (india_multicrop / efficientnet)",
    response_model=Dict[str, Any],
)
def switch_disease_engine(payload: Dict[str, str]):
    """Switch between 'india_multicrop' and 'efficientnet' engines for instant rollback."""
    engine = payload.get("engine", "")
    try:
        disease_detection_service.set_engine(engine)
        return {
            "success": True,
            "active_engine": engine,
            "message": f"Successfully activated '{engine}' engine.",
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Engine switch failed: {err}"
        )


@router.post(
    "/api/disease/predict",
    summary="Predict Foliar Plant Disease (Multipart Upload)",
    response_model=DiseasePredictionResponse,
    responses={
        200: {"description": "Diagnostic pathology prediction with CIBRC treatments"},
        400: {"description": "Corrupt or invalid image uploaded"},
        422: {"description": "Validation error in parameters"},
        503: {"description": "Model weights unavailable or inference failure"},
    },
)
async def predict_disease_multipart(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Plant leaf image (JPEG, PNG, WebP)"),
    crop: Optional[str] = Form(None, description="Declared host crop"),
    location_state: Optional[str] = Form(None, description="Geographic state in India"),
    growth_stage: Optional[str] = Form(None, description="Crop growth stage"),
    image_type: Optional[str] = Form(None, description="Image capture modality"),
    sample_id: Optional[str] = Form(None, description="Preset test image identifier"),
    symptoms: Optional[str] = Form(None, description="Optional comma-separated or JSON symptoms list"),
    abstention_threshold: Optional[float] = Form(None, description="Custom abstention cutoff (0.0-1.0)"),
):
    """Multipart or JSON endpoint for foliar disease diagnosis."""
    content_type = request.headers.get("content-type", "")

    # Check if request body was delivered as application/json
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload.")
        
        try:
            return disease_detection_service.predict(
                image_base64=body.get("image_base64"),
                sample_id=body.get("sample_id"),
                crop=body.get("crop", "Tomato"),
                location_state=body.get("location_state", "Maharashtra"),
                growth_stage=body.get("growth_stage", "vegetative"),
                image_type=body.get("image_type", "leaf"),
                symptoms=body.get("symptoms", []),
                abstention_threshold=body.get("abstention_threshold"),
            )
        except InvalidImageError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
        except ModelUnavailableError as err:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
        except Exception as err:
            logger.error("Error during disease prediction: %s", err, exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference execution failed: {err}")

    # Multipart form-data branch
    image_bytes = None
    if file:
        image_bytes = await file.read()

    symptoms_list: List[str] = []
    if symptoms:
        try:
            parsed = json.loads(symptoms)
            if isinstance(parsed, list):
                symptoms_list = [str(s) for s in parsed]
            else:
                symptoms_list = [str(s).strip() for s in symptoms.split(",") if str(s).strip()]
        except Exception:
            symptoms_list = [str(s).strip() for s in symptoms.split(",") if str(s).strip()]

    try:
        return disease_detection_service.predict(
            image_bytes=image_bytes,
            sample_id=sample_id,
            crop=crop or "Tomato",
            location_state=location_state or "Maharashtra",
            growth_stage=growth_stage or "vegetative",
            image_type=image_type or "leaf",
            symptoms=symptoms_list,
            abstention_threshold=abstention_threshold,
        )
    except InvalidImageError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ModelUnavailableError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
    except Exception as err:
        logger.error("Unexpected error during disease prediction: %s", err, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {err}"
        )


@router.post(
    "/api/disease/predict/json",
    summary="Predict Foliar Plant Disease (JSON Base64 Payload)",
    response_model=DiseasePredictionResponse,
)
def predict_disease_json(request: DiseasePredictionRequestJSON):
    """JSON base64 endpoint for foliar disease diagnosis."""
    try:
        return disease_detection_service.predict(
            image_base64=request.image_base64,
            sample_id=request.sample_id,
            crop=request.crop,
            location_state=request.location_state,
            growth_stage=request.growth_stage,
            image_type=request.image_type,
            symptoms=request.symptoms,
            abstention_threshold=request.abstention_threshold,
        )
    except InvalidImageError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ModelUnavailableError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
    except Exception as err:
        logger.error("Unexpected error during JSON disease prediction: %s", err, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {err}"
        )


@router.post(
    "/api/v1/disease-detection",
    summary="Frontend Integrated Disease Detection Endpoint (Backward Compatible)",
    response_model=DiseasePredictionResponse,
)
async def predict_disease_v1_compatible(
    request: Request,
    file: Optional[UploadFile] = File(None),
    crop: Optional[str] = Form(None),
    location_state: Optional[str] = Form(None),
    growth_stage: Optional[str] = Form(None),
    image_type: Optional[str] = Form(None),
    sample_id: Optional[str] = Form(None),
    symptoms: Optional[str] = Form(None),
    abstention_threshold: Optional[float] = Form(None),
):
    """Endpoint matching the exact `/api/v1/disease-detection` route used by the frontend."""
    return await predict_disease_multipart(
        request=request,
        file=file,
        crop=crop,
        location_state=location_state,
        growth_stage=growth_stage,
        image_type=image_type,
        sample_id=sample_id,
        symptoms=symptoms,
        abstention_threshold=abstention_threshold,
    )
