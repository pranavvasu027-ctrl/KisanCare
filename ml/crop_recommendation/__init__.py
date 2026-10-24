"""Crop recommendation package using Hugging Face dual-model architecture."""

from ml.crop_recommendation.huggingface_pipeline import (
    CropRecommendationPipeline,
    CropRecommendationInput,
    get_pipeline,
)

__all__ = [
    "CropRecommendationPipeline",
    "CropRecommendationInput",
    "get_pipeline",
]
