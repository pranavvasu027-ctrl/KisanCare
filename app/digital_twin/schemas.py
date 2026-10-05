from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Provenance(BaseModel):
    source: str = Field("user_input", description="Data source (e.g., user_input, iot_sensor, api_fetch)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class FarmLocation(BaseModel):
    state: Optional[str] = Field(None, description="State of the farm")
    district: Optional[str] = Field(None, description="District of the farm")
    latitude: Optional[float] = Field(None, description="Latitude coordinates")
    longitude: Optional[float] = Field(None, description="Longitude coordinates")
    provenance: Provenance = Field(default_factory=Provenance)

class SoilState(BaseModel):
    nitrogen: Optional[float] = Field(None, description="Nitrogen content in soil (mg/kg)")
    phosphorus: Optional[float] = Field(None, description="Phosphorus content in soil (mg/kg)")
    potassium: Optional[float] = Field(None, description="Potassium content in soil (mg/kg)")
    ph: Optional[float] = Field(None, description="Soil pH value")
    organic_carbon: Optional[float] = Field(None, description="Organic carbon percentage")
    provenance: Provenance = Field(default_factory=Provenance)

class ClimateState(BaseModel):
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Relative humidity in percentage")
    rainfall: Optional[float] = Field(None, description="Rainfall in mm")
    weather_condition: Optional[str] = Field(None, description="Current weather condition")
    provenance: Provenance = Field(default_factory=Provenance)

class CropState(BaseModel):
    current_crop: Optional[str] = Field(None, description="Currently planted crop, if any")
    season: Optional[str] = Field(None, description="Current agricultural season")
    planting_date: Optional[str] = Field(None, description="ISO Date of planting")
    provenance: Provenance = Field(default_factory=Provenance)

class WaterState(BaseModel):
    water_availability: Optional[str] = Field(None, description="Water availability: Low, Medium, High")
    irrigation_type: Optional[str] = Field(None, description="Type of irrigation used")
    provenance: Provenance = Field(default_factory=Provenance)

class FinancialState(BaseModel):
    budget: Optional[float] = Field(None, description="Available budget for the season")
    expected_revenue: Optional[float] = Field(None, description="Expected revenue")
    placeholder: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MarketState(BaseModel):
    nearest_market: Optional[str] = Field(None, description="Nearest APMC market")
    current_price: Optional[float] = Field(None, description="Current market price of the crop")
    placeholder: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FarmDigitalTwin(BaseModel):
    version: str = Field("1.0.0", description="Schema version")
    farm_id: str = Field(..., description="Unique identifier for the farm")
    farmer_id: str = Field(..., description="Unique identifier for the farmer")
    area_acres: Optional[float] = Field(None, description="Total farm area in acres")
    
    location: FarmLocation = Field(default_factory=FarmLocation)
    soil: SoilState = Field(default_factory=SoilState)
    climate: ClimateState = Field(default_factory=ClimateState)
    crop: CropState = Field(default_factory=CropState)
    water: WaterState = Field(default_factory=WaterState)
    financial: FinancialState = Field(default_factory=FinancialState)
    market: MarketState = Field(default_factory=MarketState)
    model_outputs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Stores inference outputs from AI models")
