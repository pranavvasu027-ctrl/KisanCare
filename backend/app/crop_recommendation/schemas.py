"""
Crop Recommendation Schemas
Farmer-facing response models and request payload definitions.
Adheres strictly to the principle of never exposing raw classifier probabilities
or raw technical measurements in normal farmer results.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class CropRecommendationFarmerItem(BaseModel):
    """Farmer-friendly crop recommendation card."""
    crop: str = Field(..., description="Crop display name")
    rank: int = Field(..., ge=1, le=3, description="Rank 1, 2, or 3")
    suitability_label: str = Field(..., description="Farmer-friendly label: Highly Suitable, Moderately Suitable, Low Suitability")
    reason: str = Field(..., description="Concise explanation of why this crop is recommended for this soil & season")
    local_considerations: str = Field(..., description="Regional agronomic context, mandi market demand, and soil adaptation")
    water_advisory: Optional[str] = Field(None, description="Advisory if supplemental irrigation is required")
    warning: Optional[str] = Field(None, description="Warning if regional evidence is limited or experimental")
    is_regionally_verified: bool = Field(True, description="True if proven in district historical census records")


class CropRecommendationReportResponse(BaseModel):
    """Full farmer-facing response from a single soil report upload."""
    success: bool
    district: str
    season: str
    climate_source: str
    recommendations: List[CropRecommendationFarmerItem] = Field(..., max_length=3)
    general_advisory: Optional[str] = None
    warnings: List[str] = []
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    applied_ph: Optional[float] = None
    is_ph_baseline_applied: bool = False
    extracted_nutrients: Optional[dict] = None


class CropRecommendationJsonRequest(BaseModel):
    """Direct JSON input for testing crop recommendation."""
    N: float = Field(..., ge=0.0, le=300.0)
    P: float = Field(..., ge=0.0, le=300.0)
    K: float = Field(..., ge=0.0, le=800.0)
    ph: float = Field(..., ge=3.5, le=9.5)
    temperature: Optional[float] = Field(None, ge=5.0, le=50.0)
    humidity: Optional[float] = Field(None, ge=10.0, le=100.0)
    rainfall: Optional[float] = Field(None, ge=20.0, le=3000.0)
    district: Optional[str] = "Nashik"
    season: Optional[str] = "Kharif"
    water_access: Optional[str] = None
    top_k: int = Field(3, ge=1, le=5)
