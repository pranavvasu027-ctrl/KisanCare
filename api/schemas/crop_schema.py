"""Pydantic schemas for Crop Recommendation API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CropScoreBreakdownSchema(BaseModel):
    """Detailed score breakdown and agronomic reasoning for a candidate crop."""
    crop: str = Field(..., description="Candidate crop name.")
    soil_climate_score: float = Field(..., description="Score based on soil nutrients and climate features.")
    regional_score: float = Field(..., description="Score based on regional/agro-climatic suitability.")
    region_score: Optional[float] = Field(None, description="Model 2 Regional suitability score.")
    history_rotation_score: float = Field(0.0, description="Score computed by the crop-history/rotation rule layer.")
    final_score: float = Field(..., description="Weighted composite score.")
    reason: str = Field(..., description="Agronomic explanation justifying the score.")
    rank: Optional[int] = Field(None, description="Rank position (1-based)")
    confidence_pct: Optional[float] = Field(None, description="Confidence percentage (0-100)")
    npk_score: Optional[float] = Field(None, description="Model 1 Random Forest NPK probability score")
    region_suitability: Optional[str] = Field(None, description="Regional suitability categorical label")
    grown_pct_of_years: Optional[float] = Field(None, description="Percentage of historical years grown in region")
    avg_yield_t_ha: Optional[float] = Field(None, description="Historical average yield in tonnes/hectare")
    historically_grown: Optional[bool] = Field(None, description="Whether historically grown in this district/season")
    water_constrained: Optional[bool] = Field(False, description="Whether water availability limits crop suitability")
    is_regionally_supported: Optional[bool] = Field(True, description="Whether crop has historical cultivation evidence in Model 2 regional dataset")
    evidence_tier: Optional[str] = Field(None, description="Regional evidence tier (e.g. Verified in Sangli vs Biophysical Candidate Only)")
    soil_climate_source: Optional[str] = Field(
        default=None,
        description="Source of the SoilClimateScore."
    )
    detailed_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed breakdown of rotation rules applied."
    )


class CropRecommendationRequest(BaseModel):
    """Inference API request payload for crop recommendation.

    All seven soil and climate inputs are required to prevent silent assumption
    or invention of unmeasured physical observations.
    """
    N: float = Field(..., ge=0.0, le=300.0, description="Available Soil Nitrogen (kg/ha or mg/kg)")
    P: float = Field(..., ge=0.0, le=300.0, description="Available Soil Phosphorus (kg/ha or mg/kg)")
    K: float = Field(..., ge=0.0, le=800.0, description="Available Soil Potassium (kg/ha or mg/kg)")
    ph: float = Field(..., ge=3.5, le=9.5, description="Soil pH value (3.5 - 9.5)")
    temperature: float = Field(..., ge=5.0, le=50.0, description="Mean temperature in Celsius (5.0 - 50.0)")
    humidity: float = Field(..., ge=10.0, le=100.0, description="Relative humidity percentage (10.0 - 100.0)")
    rainfall: float = Field(..., ge=20.0, le=3000.0, description="Precipitation in mm (20.0 - 3000.0)")
    state: Optional[str] = Field("Maharashtra", description="Indian state for regional suitability mapping")
    district: Optional[str] = Field("Nashik", description="District name (e.g., Nashik, Pune)")
    season: Optional[str] = Field("Kharif", description="Agricultural season (Kharif, Rabi, Summer, Whole Year)")
    water_access: Optional[str] = Field(None, description="Irrigation infrastructure availability")
    w_model1: Optional[float] = Field(0.60, ge=0.0, le=1.0, description="Model 1 NPK probability weight")
    current_crop: Optional[str] = Field(None, description="Current or most recently harvested crop")
    prev_crop_1: Optional[str] = Field(None, description="Crop grown 1 season prior")
    prev_crop_2: Optional[str] = Field(None, description="Crop grown 2 seasons prior")
    top_k: int = Field(5, ge=1, le=22, description="Number of top crop recommendations to return")
    candidate_crops: Optional[List[str]] = Field(None, description="Optional restricted list of crops to evaluate")


class CropRecommendationResponse(BaseModel):
    """Inference API response payload for crop recommendation."""
    success: bool = Field(True, description="Whether inference completed successfully")
    model: str = Field("crop_recommendation", description="Model identifier")
    prediction: str = Field(..., description="Top recommended crop")
    final_score: float = Field(..., description="Top recommendation final blended score")
    combined_score: Optional[float] = Field(None, description="Top recommendation blended score")
    unit: str = Field("crop_type", description="Prediction unit")
    recommendations: List[CropScoreBreakdownSchema] = Field(..., description="Ranked list of recommended crops")
    soil_test_npk_status: Dict[str, str] = Field(..., description="NPK status categorization (Low, Medium, High)")
    history_evaluated: List[str] = Field(default_factory=list, description="Historical crop sequence evaluated")
    weights_used: Optional[Dict[str, float]] = Field(default=None, description="Weights used for scoring")
    input_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of input features")
    warnings: List[str] = Field(default_factory=list, description="Agronomic and validation warnings")
    model_source: str = Field(..., description="Underlying model source and algorithm")
    model_loaded: bool = Field(True, description="Whether the ML model is loaded")
    is_demo: bool = Field(False, description="Flag indicating whether output is demo or authentic ML")
    limitations: List[str] = Field(
        default_factory=lambda: [
            "Random Forest classifier trained on 2,200 benchmark observations across 22 crops.",
            "Regional suitability scoring based on 26 years of Maharashtra district crop records (1997-2022).",
            "Blended multi-criteria score (60% NPK / 40% Regional); not a calibrated single-distribution probability."
        ],
        description="Known model limitations"
    )
