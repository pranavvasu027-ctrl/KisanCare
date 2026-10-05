"""Unified Inference Function and FastAPI Service for UI Developers.

Provides:
1. `recommend_crops(...)`: Single Python inference function ready for direct UI integration.
2. `app`: FastAPI REST API endpoint for web/mobile UI integration.
"""

from typing import Dict, List, Optional, Union, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from crop_recommendation.ui_template import HTML_UI

from crop_recommendation.models import (
    SoilClimateData,
    CropHistoryInput,
    ScoringWeights,
    RecommendationRequest,
    RecommendationResponse,
    SeasonalCropRecord,
)
from crop_recommendation.engine import RecommendationEngine
from crop_recommendation.config import DEFAULT_SCORING_WEIGHTS

# Singleton engine instance
_engine: Optional[RecommendationEngine] = None


def get_engine() -> RecommendationEngine:
    """Get or create singleton recommendation engine."""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine


def recommend_crops(
    # Soil & Climate parameters
    n: float,
    p: float,
    k: float,
    ph: Optional[float] = None,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    rainfall: Optional[float] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    # Crop History parameters
    current_crop: Optional[str] = None,
    prev_crop_1: Optional[str] = None,
    prev_crop_2: Optional[str] = None,
    prev_crop_3: Optional[str] = None,
    seasonal_history: Optional[List[Dict[str, Any]]] = None,
    # Control parameters
    candidate_crops: Optional[List[str]] = None,
    top_k: int = 5,
    weights: Optional[Union[Dict[str, float], ScoringWeights]] = None,
    external_soil_scores: Optional[Dict[str, float]] = None,
) -> RecommendationResponse:
    """Single unified inference function for UI developers.

    Calculates:
      Final Score = (0.50 * SoilClimateScore) + (0.30 * RegionalScore) + (0.20 * HistoryRotationScore)

    Example:
        >>> from crop_recommendation import recommend_crops
        >>> response = recommend_crops(
        ...     n=90, p=42, k=43, ph=6.5, rainfall=200, state="Maharashtra",
        ...     current_crop="cotton", prev_crop_1="cotton", prev_crop_2="soybean",
        ...     top_k=5
        ... )
        >>> for rec in response.recommendations:
        ...     print(rec.crop, rec.final_score, rec.reason)
    """
    soil_climate = SoilClimateData(
        N=n,
        P=p,
        K=k,
        ph=ph,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        state=state,
        district=district,
    )

    hist_records = None
    if seasonal_history:
        hist_records = [SeasonalCropRecord(**rec) for rec in seasonal_history]

    history = CropHistoryInput(
        current_crop=current_crop,
        prev_crop_1=prev_crop_1,
        prev_crop_2=prev_crop_2,
        prev_crop_3=prev_crop_3,
        seasonal_history=hist_records,
    )

    scoring_weights = None
    if weights is not None:
        if isinstance(weights, dict):
            scoring_weights = ScoringWeights(**weights)
        elif isinstance(weights, ScoringWeights):
            scoring_weights = weights

    engine = get_engine()
    return engine.recommend(
        soil_climate=soil_climate,
        history=history,
        candidate_crops=candidate_crops,
        weights=scoring_weights,
        external_soil_scores=external_soil_scores,
        top_k=top_k,
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application for microservice deployment."""
    app = FastAPI(
        title="Crop Recommendation & History Rotation Scoring API",
        version="1.0.0",
        description=(
            "Independent agronomic crop recommendation scoring service. "
            "Features a rule-based crop-history/crop-rotation scoring layer "
            "evaluating monoculture, nutrient pressure, diversification, legume rotation, "
            "and sequence compatibility. Current soil-test NPK values remain the primary "
            "indicator of nutrient status."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    def render_frontend():
        return HTML_UI

    @app.get("/api/v1/health")
    def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "default_weights": DEFAULT_SCORING_WEIGHTS.model_dump(),
            "note": "History scoring is an independent rule-based layer and NOT part of the Hugging Face model."
        }

    @app.get("/api/v1/crops")
    def list_knowledge_base_crops():
        engine = get_engine()
        crops = []
        for name in engine.kb.list_crops():
            crop_obj = engine.kb.get_crop(name)
            if crop_obj:
                crops.append(crop_obj.model_dump())
        return {"total_crops": len(crops), "crops": crops}

    @app.post("/api/v1/recommend", response_model=RecommendationResponse)
    def get_recommendations_endpoint(request: RecommendationRequest):
        try:
            engine = get_engine()
            return engine.recommend(
                soil_climate=request.soil_climate,
                history=request.history,
                candidate_crops=request.candidate_crops,
                weights=request.weights,
                top_k=request.top_k,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


app = create_app()
