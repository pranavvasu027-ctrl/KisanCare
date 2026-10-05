"""Data models and schemas for the Crop Recommendation and History/Rotation Scoring Layer."""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class RotationCompatibility(BaseModel):
    """Compatibility matrix and guidelines for crop rotation sequence."""
    recommended_successors: List[str] = Field(
        default_factory=list,
        description="Crops or crop families that benefit strongly from following this crop."
    )
    avoid_successors: List[str] = Field(
        default_factory=list,
        description="Crops or crop families that should NOT immediately follow this crop."
    )
    min_rotation_interval_seasons: int = Field(
        default=1,
        description="Minimum number of seasons/years before planting the same crop again."
    )
    notes: str = Field(
        default="",
        description="Agronomic notes explaining the rotational dynamics."
    )


class CropKnowledge(BaseModel):
    """Agronomic and nutrient profile for a single crop in the knowledge base."""
    name: str = Field(..., description="Canonical crop name in lowercase.")
    aliases: List[str] = Field(default_factory=list, description="Common alternative names/spellings.")
    crop_family: str = Field(..., description="Botanical family (e.g., Fabaceae, Poaceae, Solanaceae).")
    n_demand: str = Field(..., description="Nitrogen requirement level: Low, Medium, High, Very High.")
    p_demand: str = Field(..., description="Phosphorus requirement level: Low, Medium, High.")
    k_demand: str = Field(..., description="Potassium requirement level: Low, Medium, High, Very High.")
    n_demand_kg_ha: List[float] = Field(default_factory=lambda: [40.0, 80.0], description="Approx [min, max] kg/ha N.")
    p_demand_kg_ha: List[float] = Field(default_factory=lambda: [20.0, 50.0], description="Approx [min, max] kg/ha P.")
    k_demand_kg_ha: List[float] = Field(default_factory=lambda: [30.0, 70.0], description="Approx [min, max] kg/ha K.")
    is_legume: bool = Field(..., description="Whether the crop belongs to the legume (Fabaceae) family and fixes N.")
    feeder_type: str = Field(..., description="Heavy Feeder, Moderate Feeder, Light Feeder, or Soil Builder (Legume).")
    root_depth: str = Field(..., description="Root system architecture: Deep, Medium, or Shallow.")
    rotation_compatibility: RotationCompatibility = Field(default_factory=RotationCompatibility)

    def matches(self, query_crop: str) -> bool:
        """Check if a given string matches this crop's name or any aliases."""
        clean = query_crop.strip().lower()
        if clean == self.name.lower():
            return True
        for alias in self.aliases:
            if clean == alias.lower():
                return True
        return False


class SeasonalCropRecord(BaseModel):
    """Optional historical record specifying year and season."""
    year: Optional[int] = Field(None, description="Calendar year (e.g. 2024, 2025).")
    season: Optional[str] = Field(None, description="Agricultural season (e.g. Kharif, Rabi, Zaid, Summer, Winter).")
    crop: str = Field(..., description="Name of the crop cultivated.")
    notes: Optional[str] = Field(None, description="Optional yield, fertilization, or disease remarks.")


class CropHistoryInput(BaseModel):
    """Inputs representing the farmer's crop history across current and previous seasons."""
    current_crop: Optional[str] = Field(
        None,
        description="The crop currently in the field or most recently harvested (T)."
    )
    prev_crop_1: Optional[str] = Field(
        None,
        description="Crop grown 1 season prior to current crop (T-1)."
    )
    prev_crop_2: Optional[str] = Field(
        None,
        description="Crop grown 2 seasons prior (T-2)."
    )
    prev_crop_3: Optional[str] = Field(
        None,
        description="Crop grown 3 seasons prior (T-3)."
    )
    seasonal_history: Optional[List[SeasonalCropRecord]] = Field(
        default=None,
        description="Optional detailed records for past seasons/years."
    )

    def get_ordered_history(self) -> List[str]:
        """Returns the list of historical crops from most recent to oldest.

        Order: [current_crop, prev_crop_1, prev_crop_2, prev_crop_3]
        If seasonal_history is provided and positional crops are empty,
        extracts from seasonal_history.
        """
        ordered: List[str] = []
        for c in [self.current_crop, self.prev_crop_1, self.prev_crop_2, self.prev_crop_3]:
            if c and c.strip():
                ordered.append(c.strip().lower())

        if not ordered and self.seasonal_history:
            for rec in self.seasonal_history:
                if rec.crop and rec.crop.strip():
                    ordered.append(rec.crop.strip().lower())

        return ordered

    def has_history(self) -> bool:
        """True if at least one historical crop is provided."""
        return len(self.get_ordered_history()) > 0


class SoilClimateData(BaseModel):
    """Current soil-test measurements and local climate parameters.

    IMPORTANT: Crop history must NOT be treated as proof of nutrient deficiency.
    Current soil-test N/P/K values remain the primary indicator of nutrient status.
    """
    N: float = Field(..., ge=0.0, description="Available Soil Nitrogen (kg/ha or index).")
    P: float = Field(..., ge=0.0, description="Available Soil Phosphorus (kg/ha or index).")
    K: float = Field(..., ge=0.0, description="Available Soil Potassium (kg/ha or index).")
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="Soil pH level.")
    temperature: Optional[float] = Field(None, description="Average temperature in Celsius.")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity percentage.")
    rainfall: Optional[float] = Field(None, ge=0.0, description="Seasonal rainfall in mm.")
    state: Optional[str] = Field(None, description="State or province for regional zoning.")
    district: Optional[str] = Field(None, description="District or county.")

    def get_npk_adequacy(self) -> Dict[str, str]:
        """Categorize soil-test N, P, and K status into Low, Medium, or High based on standard agronomic benchmarks."""
        # Standard ICAR/Global benchmark ranges for soil test values in kg/ha:
        # N: <140 Low, 140-280 Medium, >280 High
        # P: <10 Low, 10-25 Medium, >25 High
        # K: <110 Low, 110-280 Medium, >280 High
        # For normalized 0-100 or Kaggle-like scales, accommodate standard test distributions
        res = {}
        if self.N < 40:
            res["N"] = "Low"
        elif self.N > 100:
            res["N"] = "High"
        else:
            res["N"] = "Medium"

        if self.P < 20:
            res["P"] = "Low"
        elif self.P > 60:
            res["P"] = "High"
        else:
            res["P"] = "Medium"

        if self.K < 30:
            res["K"] = "Low"
        elif self.K > 80:
            res["K"] = "High"
        else:
            res["K"] = "Medium"

        return res


class ScoringWeights(BaseModel):
    """Configurable weights for the multi-layer crop recommendation scoring."""
    soil_climate: float = Field(0.50, ge=0.0, le=1.0, description="Weight for SoilClimateScore.")
    regional: float = Field(0.30, ge=0.0, le=1.0, description="Weight for RegionalScore.")
    history_rotation: float = Field(0.20, ge=0.0, le=1.0, description="Weight for HistoryRotationScore.")

    @model_validator(mode="after")
    def validate_sum(self) -> ScoringWeights:
        total = self.soil_climate + self.regional + self.history_rotation
        if abs(total - 1.0) > 1e-4:
            # Auto-normalize if slight rounding difference
            if total > 0:
                self.soil_climate = round(self.soil_climate / total, 4)
                self.regional = round(self.regional / total, 4)
                self.history_rotation = round(1.0 - (self.soil_climate + self.regional), 4)
        return self


class CropScoreBreakdown(BaseModel):
    """Detailed score breakdown and agronomic reasoning for a candidate crop."""
    crop: str = Field(..., description="Candidate crop name.")
    soil_climate_score: float = Field(..., ge=0.0, le=1.0, description="Score based on soil nutrients and climate features.")
    regional_score: float = Field(..., ge=0.0, le=1.0, description="Score based on regional/agro-climatic suitability.")
    history_rotation_score: float = Field(..., ge=0.0, le=1.0, description="Score computed by the crop-history/rotation rule layer.")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite score.")
    reason: str = Field(..., description="Comprehensive agronomic explanation justifying the score.")
    soil_climate_source: Optional[str] = Field(
        default="Hugging Face: Sheshank2609/crop-recommendation-system",
        description="Source of the SoilClimateScore (HF Model or Fallback Agronomic Engine)."
    )
    detailed_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed breakdown of rotation rules applied (monoculture, legume, nutrient pressure, sequence)."
    )


class RecommendationRequest(BaseModel):
    """Inference API request payload."""
    soil_climate: SoilClimateData
    history: CropHistoryInput
    top_k: int = Field(5, ge=1, le=50, description="Number of top crop recommendations to return.")
    candidate_crops: Optional[List[str]] = Field(None, description="Optional restricted list of candidate crops to evaluate.")
    weights: Optional[ScoringWeights] = Field(None, description="Optional custom weights override.")


class RecommendationResponse(BaseModel):
    """Inference API response payload."""
    recommendations: List[CropScoreBreakdown]
    weights_used: ScoringWeights
    soil_test_npk_status: Dict[str, str]
    history_evaluated: List[str]
    model_source: str = Field(
        default="Hugging Face: Sheshank2609/crop-recommendation-system",
        description="Source of the ML model used for SoilClimateScore."
    )
    model_loaded: bool = Field(
        default=True,
        description="Whether the real Hugging Face model was loaded successfully."
    )
    note: str = Field(
        default="HistoryRotationScore is an independent rule-based rotation/nutrient-pressure layer and is NOT part of the Hugging Face model.",
        description="System disclaimer regarding model separation and soil-test primacy."
    )
