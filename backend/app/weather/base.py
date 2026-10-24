"""Abstract weather provider base class and WMO code mapper."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .schemas import CurrentWeatherResponse, WeatherForecastResponse

WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

def wmo_code_to_text(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(code, f"Weather Code {code}")


class BaseWeatherProvider(ABC):
    """Abstract interface for external meteorological providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'open-meteo', 'weatherapi')."""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str:
        """Mandatory attribution notice for frontend and API responses."""
        pass

    @abstractmethod
    def get_current(self, latitude: float, longitude: float, location_name: str = "Unknown") -> CurrentWeatherResponse:
        """Fetch real-time weather observations for given coordinates."""
        pass

    @abstractmethod
    def get_forecast(self, latitude: float, longitude: float, forecast_days: int = 7, location_name: str = "Unknown") -> WeatherForecastResponse:
        """Fetch hourly and daily forecasts including agricultural variables."""
        pass
