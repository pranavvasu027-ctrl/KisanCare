"""Service layer for Irrigation Intelligence Model."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from api.schemas.irrigation_schema import (
    IrrigationPredictionData,
    IrrigationRequest,
    IrrigationResponse,
    WaterBalanceMetricsResponse,
)
from models.irrigation.engine import IrrigationResult, predict_irrigation
from models.irrigation.loader import load_irrigation_model

logger = logging.getLogger("kisancare.irrigation_service")


class IrrigationService:
    """Singleton service for managing and querying the Irrigation Model."""

    _instance: Optional[IrrigationService] = None
    _artifacts: Optional[Dict[str, Any]] = None

    def __new__(cls) -> IrrigationService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Pre-load model artifacts into memory at startup."""
        if self._artifacts is None:
            logger.info("Initializing and preloading Irrigation Model artifacts...")
            self._artifacts = load_irrigation_model()
            logger.info("Irrigation Model initialized successfully.")

    def is_loaded(self) -> bool:
        """Check if model artifacts are loaded in memory."""
        return self._artifacts is not None

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the irrigation model."""
        if not self.is_loaded():
            return {
                "loaded": False,
                "status": "uninitialized",
                "model_type": "FAO-56 Physical Water Balance + PyTorch ETo LSTM",
                "source": "models/irrigation/eto/eto_punjab_best.pth",
                "metadata": {},
            }

        return {
            "loaded": True,
            "status": "ready",
            "model_type": "FAO-56 Physical Water Balance + PyTorch ETo LSTM",
            "source": "models/irrigation/eto/eto_punjab_best.pth",
            "metadata": {
                "crops_supported": list(self._artifacts.get("crop_coefficients", {}).keys()),
                "device": "cpu",
            },
        }

    def predict(self, request: IrrigationRequest) -> IrrigationResponse:
        """Run irrigation prediction pipeline and format response."""
        # Ensure model is initialized
        if self._artifacts is None:
            self.initialize()

        raw_result: IrrigationResult = predict_irrigation(
            crop=request.crop,
            crop_stage=request.crop_stage,
            soil_type=request.soil_type,
            soil_moisture=request.soil_moisture,
            rainfall=request.rainfall,
            decision_date=request.decision_date,
            historical_weather=request.historical_weather,
        )

        wb_response = WaterBalanceMetricsResponse(
            soil_water_depletion_mm=raw_result.water_balance.soil_water_depletion_mm,
            total_available_water_mm=raw_result.water_balance.total_available_water_mm,
            readily_available_water_mm=raw_result.water_balance.readily_available_water_mm,
            crop_evapotranspiration_mm=raw_result.water_balance.crop_evapotranspiration_mm,
            reference_eto_mm=raw_result.water_balance.reference_eto_mm,
            net_irrigation_requirement_mm=raw_result.water_balance.net_irrigation_requirement_mm,
        )

        prediction_data = IrrigationPredictionData(
            irrigation_required=raw_result.irrigation_required,
            irrigation_quantity_mm=raw_result.irrigation_quantity_mm,
            irrigation_timing=raw_result.irrigation_timing,
            decision_date=raw_result.decision_date,
            crop=raw_result.crop,
            crop_stage=raw_result.crop_stage,
            soil_type=raw_result.soil_type,
            soil_moisture=raw_result.soil_moisture,
            rainfall_mm=raw_result.rainfall_mm,
            water_balance=wb_response,
            decision_reason_codes=raw_result.decision_reason_codes,
            warnings=raw_result.warnings,
            model_source=raw_result.model_source,
        )

        return IrrigationResponse(
            success=True,
            model="irrigation",
            prediction=prediction_data,
        )


# Global singleton instance
irrigation_service = IrrigationService()
