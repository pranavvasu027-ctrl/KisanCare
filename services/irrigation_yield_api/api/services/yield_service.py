"""Service layer for Crop Yield Intelligence Model."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from api.schemas.yield_schema import (
    YieldPredictionData,
    YieldRequest,
    YieldResponse,
)
from models.crop_yield.model_loader import (
    MODEL_SOURCE,
    get_supported_categories,
    load_model_artifacts,
)
from models.crop_yield.predictor import YieldPredictionResult, predict_crop_yield

logger = logging.getLogger("kisancare.yield_service")


class YieldService:
    """Singleton service for managing and querying the Crop Yield Model."""

    _instance: Optional[YieldService] = None
    _artifacts: Optional[Dict[str, Any]] = None

    def __new__(cls) -> YieldService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Pre-load model artifacts and encoders into memory at startup."""
        if self._artifacts is None:
            logger.info("Initializing and preloading Crop Yield Model artifacts...")
            self._artifacts = load_model_artifacts()
            logger.info("Crop Yield Model initialized successfully.")

    def is_loaded(self) -> bool:
        """Check if model artifacts are loaded in memory."""
        return self._artifacts is not None

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the crop yield model."""
        if not self.is_loaded():
            return {
                "loaded": False,
                "status": "uninitialized",
                "model_type": "RandomForestRegressor (200 estimators)",
                "source": MODEL_SOURCE,
                "metadata": {},
            }

        supported = get_supported_categories(self._artifacts)
        return {
            "loaded": True,
            "status": "ready",
            "model_type": "RandomForestRegressor (200 estimators)",
            "source": MODEL_SOURCE,
            "metadata": {
                "num_states": len(supported["states"]),
                "num_crops": len(supported["crops"]),
                "num_seasons": len(supported["seasons"]),
                "num_soil_types": len(supported["soil_types"]),
            },
        }

    def predict(self, request: YieldRequest) -> YieldResponse:
        """Run crop yield prediction pipeline and format response."""
        # Ensure model is initialized
        if self._artifacts is None:
            self.initialize()

        raw_result: YieldPredictionResult = predict_crop_yield(
            state=request.state,
            crop=request.crop,
            season=request.season,
            soil_type=request.soil_type,
            area=request.area,
            rainfall=request.rainfall,
            temperature=request.temperature,
            humidity=request.humidity,
            nitrogen=request.nitrogen,
            phosphorus=request.phosphorus,
            potassium=request.potassium,
        )

        prediction_data = YieldPredictionData(
            predicted_yield=raw_result.predicted_yield,
            yield_unit=raw_result.yield_unit,
            estimated_production=raw_result.estimated_production,
            production_unit=raw_result.production_unit,
            cultivated_area_hectares=raw_result.cultivated_area_hectares,
            input_summary=raw_result.input_summary,
            model_source=raw_result.model_source,
        )

        return YieldResponse(
            success=True,
            model="yield",
            prediction=prediction_data,
        )


# Global singleton instance
yield_service = YieldService()
