"""API route for Crop Yield Prediction."""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from api.schemas.yield_schema import YieldRequest, YieldResponse
from api.services.yield_service import yield_service

logger = logging.getLogger("kisancare.routes.yield")
router = APIRouter(prefix="/api/yield", tags=["Crop Yield"])


@router.post(
    "/predict",
    response_model=YieldResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict crop yield and total estimated production",
    description=(
        "Estimates agricultural yield in quintal/hectare and total harvest production "
        "using a Random Forest Regressor trained on 20,000+ Indian agro-climatic records."
    ),
    responses={
        200: {
            "description": "Crop yield prediction generated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "model": "yield",
                        "prediction": {
                            "predicted_yield": 42.15,
                            "yield_unit": "quintal/hectare",
                            "estimated_production": 421.5,
                            "production_unit": "quintal",
                            "cultivated_area_hectares": 10.0,
                            "input_summary": {
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
                            "model_source": "Hugging Face NIHAL670/Crop-yield (RandomForestRegressor)",
                        },
                    }
                }
            },
        },
        422: {"description": "Validation error or invalid agro-climatic parameter."},
    },
)
async def predict_yield_endpoint(request: YieldRequest) -> YieldResponse:
    """Execute crop yield prediction pipeline."""
    try:
        response = yield_service.predict(request)
        return response
    except ValueError as ve:
        logger.warning("Yield prediction validation error: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except RuntimeError as re:
        logger.error("Yield model artifact unavailable: %s", str(re))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re),
        )
    except Exception as exc:
        logger.error("Unexpected error in crop yield prediction: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating crop yield.",
        )
