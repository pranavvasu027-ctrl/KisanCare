"""Crop Yield Prediction Package.

A standalone Python library for India crop yield prediction using a pretrained
Random Forest Regressor from Hugging Face (NIHAL670/Crop-yield).
"""

from crop_yield.model_loader import (
    MODEL_SOURCE,
    MODEL_LOADED,
    get_model_status,
    get_supported_categories,
    load_model_artifacts,
)
from crop_yield.predictor import (
    FEATURE_COLUMNS,
    PredictionResult,
    YIELD_UNIT,
    PRODUCTION_UNIT,
    predict_yield,
)

__all__ = [
    "MODEL_SOURCE",
    "MODEL_LOADED",
    "FEATURE_COLUMNS",
    "YIELD_UNIT",
    "PRODUCTION_UNIT",
    "PredictionResult",
    "predict_yield",
    "get_model_status",
    "get_supported_categories",
    "load_model_artifacts",
]
