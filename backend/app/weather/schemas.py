"""Pydantic schemas for standardized meteorological and agro-climatic data."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)")


class CurrentWeatherResponse(BaseModel):
    location: str = Field(default="Takli Bu, Akola, Maharashtra", description="Geographic location name or nearest district")
    coordinates: Coordinates
    temperature: Optional[float] = Field(None, description="Air temperature at 2m height")
    temperature_unit: str = Field(default="°C")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity at 2m height")
    humidity_unit: str = Field(default="%")
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Wind speed at 10m height in km/h")
    wind_direction_deg: Optional[float] = Field(None, ge=0.0, le=360.0, description="Wind direction in degrees")
    surface_pressure_hpa: Optional[float] = Field(None, description="Atmospheric pressure at surface level in hPa")
    precipitation_mm: Optional[float] = Field(None, ge=0.0, description="Current precipitation accumulation in mm")
    weather_condition: str = Field(default="Partly Cloudy", description="Human-readable weather status")
    weather_code: Optional[int] = Field(None, description="WMO weather interpretation code")
    rainfall_probability: str = Field(default="Unavailable", description="Precipitation probability summary")
    rainfall_since_sowing: str = Field(default="Unavailable (No on-field rain gauge installed)")
    reference_evapotranspiration_mm: Optional[float] = Field(None, description="Daily reference evapotranspiration (ET0) in mm")
    data_source: str = Field(..., description="Data source description and station/grid information")
    provider: str = Field(..., description="Provider name: 'open-meteo', 'weatherapi', or 'supabase_fallback'")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of meteorological observation")
    is_synthetic: bool = Field(default=False, description="Whether data is simulated/mocked")
    is_stale: bool = Field(default=False, description="Whether data exceeded maximum freshness window")
    verified: bool = Field(default=True, description="Whether data meets quality validation")
    attribution: str = Field(default="Weather data by Open-Meteo.com (CC BY 4.0)", description="Mandatory legal provider attribution")


class HourlyForecastItem(BaseModel):
    time: str = Field(..., description="ISO timestamp for forecast hour")
    temperature: Optional[float] = Field(None, description="Air temperature in °C")
    humidity: Optional[float] = Field(None, description="Relative humidity in %")
    precipitation_probability: Optional[float] = Field(None, ge=0.0, le=100.0, description="Chance of precipitation in %")
    precipitation_mm: Optional[float] = Field(None, ge=0.0, description="Hourly rainfall in mm")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    weather_condition: str = Field(default="Clear", description="Human-readable weather status")
    weather_code: Optional[int] = Field(None, description="WMO code")


class DailyForecastItem(BaseModel):
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    temperature_max: Optional[float] = Field(None, description="Maximum air temperature in °C")
    temperature_min: Optional[float] = Field(None, description="Minimum air temperature in °C")
    precipitation_sum_mm: Optional[float] = Field(None, ge=0.0, description="Total daily precipitation in mm")
    precipitation_probability_max: Optional[float] = Field(None, ge=0.0, le=100.0, description="Max daily rain probability %")
    et0_fao_evapotranspiration_mm: Optional[float] = Field(None, description="Reference evapotranspiration (ET0) in mm")
    weather_condition: str = Field(default="Clear", description="Summary condition")
    weather_code: Optional[int] = Field(None, description="WMO code")
    sunrise: Optional[str] = Field(None, description="Sunrise ISO timestamp")
    sunset: Optional[str] = Field(None, description="Sunset ISO timestamp")


class WeatherForecastResponse(BaseModel):
    location: str = Field(default="Takli Bu, Akola, Maharashtra")
    coordinates: Coordinates
    timezone: str = Field(default="Asia/Kolkata")
    current: CurrentWeatherResponse
    hourly: List[HourlyForecastItem] = Field(default_factory=list)
    daily: List[DailyForecastItem] = Field(default_factory=list)
    agricultural_advisory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-guaranteed agro-climatic summary (heat risk, rain advisory)"
    )
    provider: str
    data_source: str
    is_cached: bool = Field(default=False)
    is_stale: bool = Field(default=False)
    attribution: str = Field(default="Weather data by Open-Meteo.com (CC BY 4.0)")
