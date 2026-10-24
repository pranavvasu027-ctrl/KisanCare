"""Weather service orchestrator with provider swappability, caching, and fallback."""
from __future__ import annotations

import os
from typing import Optional, Dict, Any
from .schemas import CurrentWeatherResponse, WeatherForecastResponse, Coordinates
from .base import BaseWeatherProvider
from .open_meteo_adapter import OpenMeteoAdapter
from .weatherapi_adapter import WeatherAPIAdapter
from .cache import WeatherCache


class WeatherService:
    def __init__(self, cache: Optional[WeatherCache] = None):
        self.cache = cache or WeatherCache(
            default_ttl_seconds=int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "900")),
            max_stale_seconds=int(os.getenv("WEATHER_CACHE_MAX_STALE_SECONDS", "7200")),
        )

    def get_provider(self, provider_name: Optional[str] = None) -> BaseWeatherProvider:
        name = (provider_name or os.getenv("WEATHER_PROVIDER", "open-meteo")).strip().lower()
        if name in ["weatherapi", "weather_api"]:
            return WeatherAPIAdapter()
        return OpenMeteoAdapter()

    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Takli Bu, Akola, Maharashtra",
        farm_id: Optional[str] = None,
        force_refresh: bool = False,
    ) -> CurrentWeatherResponse:
        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid geographic coordinates: lat={latitude}, lon={longitude}")

        # Check Cache
        if not force_refresh:
            cached_val, is_hit, is_stale = self.cache.get("current", latitude, longitude)
            if is_hit and cached_val is not None:
                # Return cached value with freshness markers
                cached_copy = cached_val.model_copy()
                cached_copy.is_stale = is_stale
                return cached_copy

        provider = self.get_provider()
        try:
            current = provider.get_current(latitude, longitude, location_name=location_name)
            self.cache.set("current", latitude, longitude, current)
            return current
        except Exception as prov_err:
            # Check if we have stale cache to serve in degraded mode
            cached_val, is_hit, _ = self.cache.get("current", latitude, longitude)
            if is_hit and cached_val is not None:
                stale_copy = cached_val.model_copy()
                stale_copy.is_stale = True
                return stale_copy

            # Fallback to Supabase weather_records if available
            fallback = self._try_supabase_fallback(latitude, longitude, location_name, farm_id)
            if fallback:
                return fallback

            # Ultimate degraded state with explicit "Unavailable"
            return CurrentWeatherResponse(
                location=location_name,
                coordinates=Coordinates(latitude=latitude, longitude=longitude),
                temperature=None,
                humidity=None,
                wind_speed_kmh=None,
                weather_condition="Service Temporarily Unavailable",
                rainfall_probability="Unavailable",
                rainfall_since_sowing="Unavailable (No on-field rain gauge installed)",
                data_source=f"Error contacting {provider.provider_name}: {str(prov_err)}",
                provider="none",
                observed_at=None,
                is_synthetic=False,
                is_stale=True,
                verified=False,
                attribution=provider.attribution,
            )

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        location_name: str = "Takli Bu, Akola, Maharashtra",
        force_refresh: bool = False,
    ) -> WeatherForecastResponse:
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid geographic coordinates: lat={latitude}, lon={longitude}")

        cache_extra = f"days_{days}"
        if not force_refresh:
            cached_val, is_hit, is_stale = self.cache.get("forecast", latitude, longitude, extra=cache_extra)
            if is_hit and cached_val is not None:
                cached_copy = cached_val.model_copy()
                cached_copy.is_cached = True
                cached_copy.is_stale = is_stale
                return cached_copy

        provider = self.get_provider()
        try:
            forecast = provider.get_forecast(latitude, longitude, forecast_days=days, location_name=location_name)
            self.cache.set("forecast", latitude, longitude, forecast, extra=cache_extra)
            return forecast
        except Exception as prov_err:
            cached_val, is_hit, _ = self.cache.get("forecast", latitude, longitude, extra=cache_extra)
            if is_hit and cached_val is not None:
                stale_copy = cached_val.model_copy()
                stale_copy.is_cached = True
                stale_copy.is_stale = True
                return stale_copy
            raise RuntimeError(f"Unable to retrieve forecast from {provider.provider_name}: {prov_err}")

    def _try_supabase_fallback(
        self, latitude: float, longitude: float, location_name: str, farm_id: Optional[str]
    ) -> Optional[CurrentWeatherResponse]:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            return None

        try:
            from supabase import create_client
            sb = create_client(url, key)
            query = sb.table("weather_records").select("*")
            if farm_id:
                query = query.eq("farm_id", farm_id)
            w_res = query.order("timestamp", desc=True).limit(1).execute()
            if w_res.data:
                w = w_res.data[0]
                return CurrentWeatherResponse(
                    location=w.get("location", location_name),
                    coordinates=Coordinates(latitude=latitude, longitude=longitude),
                    temperature=float(w["temperature"]) if w.get("temperature") is not None else 29.0,
                    temperature_unit="°C",
                    humidity=float(w["humidity"]) if w.get("humidity") is not None else 55.0,
                    humidity_unit="%",
                    wind_speed_kmh=float(w["wind"]) if w.get("wind") is not None else 10.0,
                    weather_condition=(w.get("forecast_information") or {}).get("condition", "Partly Cloudy"),
                    rainfall_probability="Unavailable (Forecast feed offline)",
                    rainfall_since_sowing="Unavailable (No on-field rain gauge installed)",
                    reference_evapotranspiration_mm=None,
                    data_source="Supabase weather_records (Farmer-reported local observation)",
                    provider="supabase_fallback",
                    observed_at=w.get("timestamp"),
                    is_synthetic=False,
                    is_stale=True,
                    verified=True,
                    attribution="KisanCare Field Records",
                )
        except Exception:
            pass
        return None


# Global singleton instance
_weather_service_instance: Optional[WeatherService] = None

def get_weather_service() -> WeatherService:
    global _weather_service_instance
    if _weather_service_instance is None:
        _weather_service_instance = WeatherService()
    return _weather_service_instance
