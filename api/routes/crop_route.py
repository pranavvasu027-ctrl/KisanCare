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


@router.post(
    "/api/v1/soil-assessment",
    status_code=status.HTTP_200_OK,
    summary="Diagnostic soil nutrient assessment",
)
@router.post(
    "/soil-assessment",
    status_code=status.HTTP_200_OK,
    summary="Diagnostic soil nutrient assessment",
)
async def assess_soil_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Provide scientific diagnostic assessment of Nitrogen, Phosphorus, Potassium, and pH levels."""
    try:
        n = float(payload.get("n", payload.get("N", 90.0)))
        p = float(payload.get("p", payload.get("P", 42.0)))
        k = float(payload.get("k", payload.get("K", 43.0)))
        ph = float(payload.get("ph", payload.get("soil_ph", 6.5)))

        # Official ICAR / Government of India Soil Health Card Standard Thresholds
        issues = []
        if n < 280:
            issues.append(f"Low Available Soil Nitrogen ({n:.0f} kg/ha < 280 kg/ha ICAR threshold)")
        if p < 10:
            issues.append(f"Low Available Soil Phosphorus ({p:.0f} kg/ha < 10 kg/ha threshold)")
        if k < 120:
            issues.append(f"Low Available Soil Potassium ({k:.0f} kg/ha < 120 kg/ha threshold)")

        if ph < 6.0:
            issues.append(f"Acidic Soil (pH {ph:.1f} < 6.0; lime or dolomite application indicated)")
        elif ph > 8.0:
            issues.append(f"Alkaline/Calcareous Soil (pH {ph:.1f} > 8.0; common in Maharashtra black vertisols; zinc and phosphorus availability may be restricted)")

        overall = "Balanced / Adequate" if len(issues) == 0 else "Soil Nutrient Deficiencies Detected"
        rec = (
            "Soil test parameters are within medium-to-adequate ranges under ICAR Soil Health Card standards. Maintain soil health with balanced crop-specific basal NPK and organic manure (FYM)."
            if len(issues) == 0 else
            f"Soil fertility management needed: {'; '.join(issues)}. Note: These represent measured soil reserves, not fertilizer application doses. Consult local KVK package of practices for crop-specific fertilizer scheduling."
        )
        return {
            "model_type": "rule_based_soil_diagnostic",
            "overall_status": overall,
            "issues": issues if issues else ["Balanced NPK & pH levels"],
            "recommendation": rec
        }
    except Exception as exc:
        logger.error("Soil assessment error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid soil assessment payload: {exc}"
        ) from exc
