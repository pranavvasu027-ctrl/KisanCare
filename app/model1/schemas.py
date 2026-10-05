from pydantic import BaseModel, Field
from typing import List

class CropRecommendationRequest(BaseModel):
    nitrogen: float = Field(..., description="Nitrogen content in soil (mg/kg)")
    phosphorus: float = Field(..., description="Phosphorus content in soil (mg/kg)")
    potassium: float = Field(..., description="Potassium content in soil (mg/kg)")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity in percentage")
    ph: float = Field(..., description="Soil pH value")
    rainfall: float = Field(..., description="Rainfall in mm")

class Recommendation(BaseModel):
    rank: int
    crop: str
    score: float

class CropRecommendationResponse(BaseModel):
    model: str
    model_version: str
    recommendations: List[Recommendation]
