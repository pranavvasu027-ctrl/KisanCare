"""Service layer for Crop Recommendation Intelligence Model.

Connects to the official Hugging Face Dual-Model Pipeline:
  Sheshank2609/crop-recommendation-system
  Revision: f24d6e1666bb9efa530de8f4aec0124cd83c8cfd
Combines Model 1 (Random Forest NPK/Climate Classifier) with Model 2
(Maharashtra 26-year Regional Agricultural Viability Scoring).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from api.schemas.crop_schema import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    CropScoreBreakdownSchema,
)
from ml.crop_recommendation.huggingface_pipeline import (
    CropRecommendationInput,
    CropRecommendationPipeline,
    CropRecommendationResult,
    InputValidationError,
    ModelUnavailableError,
    get_pipeline,
)

logger = logging.getLogger("kisancare.crop_service")


class CropRecommendationService:
    """Singleton service for managing and querying the Hugging Face Crop Recommendation Model."""

    _instance: Optional[CropRecommendationService] = None
    _pipeline: Optional[CropRecommendationPipeline] = None

    def __new__(cls) -> CropRecommendationService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Pre-load Hugging Face model artifacts at startup."""
        if self._pipeline is None:
            logger.info("Initializing and preloading Hugging Face Crop Recommendation Pipeline...")
            try:
                self._pipeline = get_pipeline()
                logger.info(
                    "Crop Recommendation Model initialized successfully (ready=%s, repo=%s, rev=%s).",
                    self._pipeline.is_ready,
                    self._pipeline.repo_id,
                    self._pipeline.revision[:7],
                )
            except Exception as exc:
                logger.error("Failed to initialize Hugging Face Pipeline: %s", exc, exc_info=True)
                self._pipeline = None

    def is_loaded(self) -> bool:
        """Check if model artifacts are loaded in memory."""
        return self._pipeline is not None and self._pipeline.is_ready

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the crop recommendation model."""
        if self._pipeline is None or not self._pipeline.is_ready:
            return {
                "loaded": False,
                "status": "uninitialized",
                "model_type": "Hugging Face Dual-Model (RandomForestClassifier + Regional Scorer)",
                "source": "Sheshank2609/crop-recommendation-system",
                "metadata": {},
            }

        return {
            "loaded": True,
            "status": "ready",
            "model_type": "Hugging Face Dual-Model (RandomForestClassifier + 26-yr Regional Viability)",
            "source": f"{self._pipeline.repo_id}@{self._pipeline.revision[:7]}",
            "metadata": {
                "supported_crops": len(self._pipeline.model1_classes),
                "supported_m1_classes": len(self._pipeline.model1_classes),
                "classes": self._pipeline.model1_classes,
                "m1_classes": self._pipeline.model1_classes,
                "supported_m2_records": len(self._pipeline.model2_df) if self._pipeline.model2_df is not None else 0,
                "feature_order": [
                    "N", "P", "K", "temperature", "humidity", "ph", "rainfall"
                ],
            },
        }

    def predict(self, request: CropRecommendationRequest) -> CropRecommendationResponse:
        """Execute full multi-layer crop recommendation inference."""
        if self._pipeline is None:
            self.initialize()

        if self._pipeline is None or not self._pipeline.is_ready:
            raise ModelUnavailableError("Crop recommendation model artifacts are not loaded in memory.")

        inputs = CropRecommendationInput(
            N=float(request.N),
            P=float(request.P),
            K=float(request.K),
            ph=float(request.ph) if request.ph is not None else 6.5,
            temperature=float(request.temperature) if request.temperature is not None else 25.0,
            humidity=float(request.humidity) if request.humidity is not None else 70.0,
            rainfall=float(request.rainfall) if request.rainfall is not None else 750.0,
            district=request.district or "Nashik",
            season=request.season or "Kharif",
            state=request.state or "Maharashtra",
            water_access=request.water_access,
            w_model1=float(request.w_model1) if request.w_model1 is not None else 0.60,
            top_k=int(request.top_k),
        )

        result: CropRecommendationResult = self._pipeline.predict(inputs)

        schema_recs = [
            CropScoreBreakdownSchema(
                crop=r.crop,
                rank=r.rank,
                soil_climate_score=r.npk_score,
                regional_score=r.region_score,
                region_score=r.region_score,
                history_rotation_score=0.0,
                final_score=r.combined_score,
                confidence_pct=r.confidence_pct,
                npk_score=r.npk_score,
                region_suitability=r.region_suitability,
                grown_pct_of_years=r.grown_pct_of_years,
                avg_yield_t_ha=r.avg_yield_t_ha,
                historically_grown=r.historically_grown,
                water_constrained=r.water_constrained,
                reason=r.reason,
                soil_climate_source=f"Hugging Face: {self._pipeline.repo_id} (RandomForestClassifier)",
            )
            for r in result.recommendations
        ]

        history_items = []
        if request.current_crop:
            history_items.append(f"Current: {request.current_crop}")
        if request.prev_crop_1:
            history_items.append(f"Prev 1: {request.prev_crop_1}")
        if request.prev_crop_2:
            history_items.append(f"Prev 2: {request.prev_crop_2}")

        return CropRecommendationResponse(
            success=True,
            model="crop_recommendation",
            prediction=result.prediction,
            final_score=result.combined_score,
            combined_score=result.combined_score,
            unit="crop_type",
            recommendations=schema_recs,
            soil_test_npk_status=result.soil_test_npk_status,
            history_evaluated=history_items,
            weights_used=result.weights_used,
            input_summary=result.input_summary,
            warnings=result.warnings,
            model_source=f"Hugging Face: {result.model_version}",
            model_loaded=True,
            is_demo=False,
            limitations=[
                "Model 1: Random Forest classifier trained on 2,200 benchmark observations across 22 crops.",
                "Model 2: Regional suitability scoring based on 26 years of Maharashtra district crop records (1997-2022).",
                "Combined Score: Weighted multi-criteria score (60% NPK / 40% Regional); not a calibrated single probability distribution.",
            ],
        )


# Global singleton instance
crop_recommendation_service = CropRecommendationService()
