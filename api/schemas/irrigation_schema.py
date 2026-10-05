"""Pydantic schemas for Irrigation Inference API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class IrrigationRequest(BaseModel):
    """Input payload for irrigation prediction."""

    crop: str = Field(
        ...,
        description="Crop name (e.g., 'wheat', 'rice', 'maize', 'cotton', 'sugarcane')",
        examples=["wheat"],
    )
    crop_stage: str = Field(
        ...,
        description="Growth stage ('initial', 'mid', 'late')",
        examples=["mid"],
    )
    soil_type: str = Field(
        ...,
        description="Soil texture category ('loam', 'clay', 'sand', 'sandy loam', 'clay loam', 'silt loam')",
        examples=["loam"],
    )
    soil_moisture: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Current volumetric soil moisture fraction (0.0 to 1.0 m³/m³)",
        examples=[0.15],
    )
    rainfall: float = Field(
        default=0.0,
        ge=0.0,
        description="Observed or forecasted rainfall today in mm",
        examples=[0.0],
    )
    decision_date: Optional[str] = Field(
        default=None,
        description="Advisory date (YYYY-MM-DD). Defaults to current date if omitted.",
        examples=["2026-10-05"],
    )
    historical_weather: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional 14-day sequence of weather observations for neural ETo calculation.",
    )

    @field_validator("crop", "crop_stage", "soil_type")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("String field cannot be empty")
        return v


class WaterBalanceMetricsResponse(BaseModel):
    """FAO-56 physical root zone water balance metrics."""

    soil_water_depletion_mm: float = Field(..., description="Root zone soil water depletion (Dr) in mm")
    total_available_water_mm: float = Field(..., description="Total available soil water in root zone (TAW) in mm")
    readily_available_water_mm: float = Field(..., description="Readily available soil water without stress (RAW) in mm")
    crop_evapotranspiration_mm: float = Field(..., description="Daily crop evapotranspiration (ETc) in mm")
    reference_eto_mm: float = Field(..., description="Reference evapotranspiration (ETo) in mm")
    net_irrigation_requirement_mm: float = Field(..., description="Net irrigation requirement in mm")


class IrrigationPredictionData(BaseModel):
    """Core prediction data for irrigation advisory."""

    irrigation_required: bool = Field(..., description="Whether irrigation is needed")
    irrigation_quantity_mm: float = Field(..., description="Gross recommended irrigation depth in mm")
    irrigation_timing: str = Field(..., description="Timing recommendation ('today', 'within_24h', 'none')")
    decision_date: str = Field(..., description="Advisory decision date (YYYY-MM-DD)")
    crop: str = Field(..., description="Crop evaluated")
    crop_stage: str = Field(..., description="Crop growth stage")
    soil_type: str = Field(..., description="Soil type evaluated")
    soil_moisture: float = Field(..., description="Input soil moisture fraction")
    rainfall_mm: float = Field(..., description="Input rainfall in mm")
    water_balance: WaterBalanceMetricsResponse = Field(..., description="Physical soil water balance metrics")
    decision_reason_codes: List[str] = Field(..., description="Audit reason codes for irrigation decision")
    warnings: List[str] = Field(default_factory=list, description="Diagnostic warnings or fallbacks")
    model_source: str = Field(..., description="Provenance of the inference model")
    units: Dict[str, str] = Field(
        default={
            "irrigation_quantity": "mm",
            "soil_water_depletion": "mm",
            "total_available_water": "mm",
            "readily_available_water": "mm",
            "crop_evapotranspiration": "mm",
            "reference_eto": "mm",
            "net_irrigation_requirement": "mm",
            "soil_moisture": "m³/m³ (fraction)",
            "rainfall": "mm",
        },
        description="Physical units for numerical values",
    )


class IrrigationResponse(BaseModel):
    """Standardized API response for irrigation prediction."""

    success: bool = Field(default=True, description="Whether prediction succeeded")
    model: str = Field(default="irrigation", description="Identifier of the model used")
    prediction: IrrigationPredictionData = Field(..., description="Prediction result")
