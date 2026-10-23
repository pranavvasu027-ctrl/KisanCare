"""API routes for Crop Recommendation Intelligence Model."""

from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from api.schemas.crop_schema import (
    CropRecommendationRequest,
    CropRecommendationResponse,
)
from api.services.crop_service import crop_recommendation_service
from ml.crop_recommendation.huggingface_pipeline import (
    InputValidationError,
    ModelUnavailableError,
)

logger = logging.getLogger("kisancare.routes.crop")
router = APIRouter(tags=["Crop Recommendation"])


@router.post(
    "/api/v1/crop-recommendation",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend crops using Hugging Face dual-model pipeline",
    description=(
        "Combines Model 1 (Random Forest soil/climate classifier) with Model 2 "
        "(Maharashtra 26-year regional suitability scoring table) from Hugging Face: "
        "Sheshank2609/crop-recommendation-system."
    ),
)
@router.post(
    "/api/crop/recommend",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend optimal crops with multi-layer agronomic scoring",
)
@router.post(
    "/api/v1/recommend",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend optimal crops (AD contract endpoint)",
)
async def recommend_crops_endpoint(request: CropRecommendationRequest) -> CropRecommendationResponse:
    """Execute authenticated ML crop recommendation inference."""
    try:
        return crop_recommendation_service.predict(request)
    except InputValidationError as exc:
        logger.warning("Invalid input for crop recommendation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ModelUnavailableError as exc:
        logger.error("Crop recommendation model unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Crop recommendation failed: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crop recommendation model failed: {str(exc)}",
        ) from exc


@router.post(
    "/api/v1/predict/crop",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Crop prediction endpoint supporting flexible and nested payloads",
)
@router.post(
    "/api/predict/crop",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Crop prediction endpoint supporting flexible and nested payloads",
)
async def predict_crop_flexible_endpoint(payload: Dict[str, Any]) -> CropRecommendationResponse:
    """Accept flexible dictionary with optional nested 'data' key and run authentic ML inference."""
    try:
        from ml.crop_recommendation.predict import predict_crop_from_dict
        res = predict_crop_from_dict(payload)
        return CropRecommendationResponse(**res)
    except InputValidationError as exc:
        logger.warning("Invalid input for flexible crop prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ModelUnavailableError as exc:
        logger.error("Crop recommendation model unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Flexible crop prediction failed: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid crop prediction request payload: {str(exc)}",
        ) from exc
