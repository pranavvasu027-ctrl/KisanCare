"""API route for Irrigation Prediction."""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from api.schemas.irrigation_schema import IrrigationRequest, IrrigationResponse
from api.services.irrigation_service import irrigation_service

logger = logging.getLogger("kisancare.routes.irrigation")
router = APIRouter(prefix="/api/irrigation", tags=["Irrigation"])


@router.post(
    "/predict",
    response_model=IrrigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict irrigation schedule and water requirements",
    description=(
        "Calculates precision irrigation requirements using FAO-56 dual crop coefficient "
        "soil water balance coupled with reference evapotranspiration (ETo) deep learning."
    ),
    responses={
        200: {
            "description": "Irrigation advisory generated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "model": "irrigation",
                        "prediction": {
                            "irrigation_required": True,
                            "irrigation_quantity_mm": 51.53,
                            "irrigation_timing": "today",
                            "decision_date": "2026-10-05",
                            "crop": "wheat",
                            "crop_stage": "mid",
                            "soil_type": "loam",
                            "soil_moisture": 0.15,
                            "rainfall_mm": 0.0,
                            "water_balance": {
                                "soil_water_depletion_mm": 37.5,
                                "total_available_water_mm": 225.0,
                                "readily_available_water_mm": 123.75,
                                "crop_evapotranspiration_mm": 5.75,
                                "reference_eto_mm": 5.0,
                                "net_irrigation_requirement_mm": 43.8,
                            },
                            "decision_reason_codes": ["HIGH_ROOT_ZONE_DEPLETION"],
                            "warnings": [],
                            "model_source": "FAO-56 Physical Balance + ETo-LSTM-Attention",
                            "units": {
                                "irrigation_quantity": "mm",
                                "soil_water_depletion": "mm",
                                "total_available_water": "mm",
                                "readily_available_water": "mm",
                                "crop_evapotranspiration": "mm",
                                "reference_eto": "mm",
                                "net_irrigation_requirement": "mm",
                                "soil_moisture": "m³/m³ (fraction)",
                                "rainfall": "mm",
                            },
                        },
                    }
                }
            },
        },
        422: {"description": "Validation error or invalid agronomic parameter."},
    },
)
async def predict_irrigation_endpoint(request: IrrigationRequest) -> IrrigationResponse:
    """Execute irrigation recommendation pipeline."""
    try:
        response = irrigation_service.predict(request)
        return response
    except ValueError as ve:
        logger.warning("Irrigation prediction validation error: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as exc:
        logger.error("Unexpected error in irrigation prediction: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating irrigation requirements.",
        )
