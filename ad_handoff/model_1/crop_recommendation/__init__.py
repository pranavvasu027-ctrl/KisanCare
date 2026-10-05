"""Crop Recommendation System with Crop History & Rotation Scoring Layer.

An independent agronomic scoring module that integrates farmer crop history,
rotation dynamics, legume benefits, and nutrient pressure while preserving
the primacy of current soil-test N/P/K values.
"""

from crop_recommendation.models import (
    CropHistoryInput,
    SoilClimateData,
    ScoringWeights,
    CropKnowledge,
    RotationCompatibility,
    CropScoreBreakdown,
    RecommendationRequest,
    RecommendationResponse,
    SeasonalCropRecord,
)
from crop_recommendation.config import (
    DEFAULT_SCORING_WEIGHTS,
    DEFAULT_SOIL_CLIMATE_WEIGHT,
    DEFAULT_REGIONAL_WEIGHT,
    DEFAULT_HISTORY_ROTATION_WEIGHT,
)
from crop_recommendation.knowledge_base import KnowledgeBase, get_default_knowledge_base
from crop_recommendation.soil_climate_scorer import (
    SoilClimateScorer,
    MODEL_SOURCE,
    MODEL_LOADED,
    FEATURE_ORDER,
)
from crop_recommendation.regional_scorer import RegionalScorer
from crop_recommendation.engine import RecommendationEngine
from crop_recommendation.api import recommend_crops, app

__all__ = [
    "recommend_crops",
    "RecommendationEngine",
    "HistoryRotationScorer",
    "SoilClimateScorer",
    "RegionalScorer",
    "KnowledgeBase",
    "get_default_knowledge_base",
    "CropHistoryInput",
    "SoilClimateData",
    "ScoringWeights",
    "CropKnowledge",
    "RotationCompatibility",
    "CropScoreBreakdown",
    "RecommendationRequest",
    "RecommendationResponse",
    "SeasonalCropRecord",
    "DEFAULT_SCORING_WEIGHTS",
    "DEFAULT_SOIL_CLIMATE_WEIGHT",
    "DEFAULT_REGIONAL_WEIGHT",
    "DEFAULT_HISTORY_ROTATION_WEIGHT",
    "MODEL_SOURCE",
    "MODEL_LOADED",
    "FEATURE_ORDER",
    "app",
]
