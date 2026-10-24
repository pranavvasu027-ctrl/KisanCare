"""Weather module init."""
from .schemas import (
    Coordinates,
    CurrentWeatherResponse,
    HourlyForecastItem,
    DailyForecastItem,
    WeatherForecastResponse,
)
from .base import BaseWeatherProvider, wmo_code_to_text
from .open_meteo_adapter import OpenMeteoAdapter
from .weatherapi_adapter import WeatherAPIAdapter
from .cache import WeatherCache
from .service import WeatherService, get_weather_service

__all__ = [
    "Coordinates",
    "CurrentWeatherResponse",
    "HourlyForecastItem",
    "DailyForecastItem",
    "WeatherForecastResponse",
    "BaseWeatherProvider",
    "wmo_code_to_text",
    "OpenMeteoAdapter",
    "WeatherAPIAdapter",
    "WeatherCache",
    "WeatherService",
    "get_weather_service",
]
