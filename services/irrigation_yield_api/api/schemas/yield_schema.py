"""Pydantic schemas for Crop Yield Inference API."""

from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator


class YieldRequest(BaseModel):
    """Input payload for crop yield prediction."""

    state: str = Field(
        ...,
        description="Indian state name (e.g., 'Punjab', 'Uttar Pradesh', 'Maharashtra', 'Haryana')",
        examples=["Punjab"],
    )
    crop: str = Field(
        ...,
        description="Crop name (e.g., 'Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane')",
        examples=["Wheat"],
    )
    season: str = Field(
        ...,
        description="Agricultural cropping season ('Kharif', 'Rabi', 'Whole Year', 'Summer')",
        examples=["Rabi"],
    )
    soil_type: str = Field(
        ...,
        description="Soil texture classification ('Alluvial', 'Black', 'Clay', 'Laterite', 'Red')",
        examples=["Alluvial"],
    )
    area: float = Field(
        ...,
        gt=0.0,
        description="Cultivated land area in hectares (> 0)",
        examples=[10.0],
    )
    rainfall: float = Field(
        ...,
        ge=0.0,
        description="Annual/seasonal precipitation in mm (>= 0)",
        examples=[650.0],
    )
    temperature: float = Field(
        ...,
        ge=-20.0,
        le=60.0,
        description="Average seasonal ambient temperature in Celsius (-20 to 60 °C)",
        examples=[22.5],
    )
    humidity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average relative humidity percentage (0 to 100%)",
        examples=[65.0],
    )
    nitrogen: float = Field(
        ...,
        ge=0.0,
        description="Nitrogen ratio in soil (N) in kg/ha (>= 0)",
        examples=[120.0],
    )
    phosphorus: float = Field(
        ...,
        ge=0.0,
        description="Phosphorus ratio in soil (P) in kg/ha (>= 0)",
        examples=[50.0],
    )
    potassium: float = Field(
        ...,
        ge=0.0,
        description="Potassium ratio in soil (K) in kg/ha (>= 0)",
        examples=[40.0],
    )

    @field_validator("state", "crop", "season", "soil_type")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Categorical field cannot be empty")
        return v


class YieldPredictionData(BaseModel):
    """Core prediction data for crop yield."""

    predicted_yield: float = Field(..., description="Estimated yield per unit area")
    yield_unit: str = Field(default="quintal/hectare", description="Yield measurement unit")
    estimated_production: float = Field(..., description="Total production = predicted_yield * area")
    production_unit: str = Field(default="quintal", description="Total production unit")
    cultivated_area_hectares: float = Field(..., description="Land area in hectares")
    input_summary: Dict[str, Any] = Field(..., description="Summary of inputs used in the model")
    model_source: str = Field(..., description="Provenance and architecture of the ML model")


class YieldResponse(BaseModel):
    """Standardized API response for crop yield prediction."""

    success: bool = Field(default=True, description="Whether prediction succeeded")
    model: str = Field(default="yield", description="Identifier of the model used")
    prediction: YieldPredictionData = Field(..., description="Prediction result")
