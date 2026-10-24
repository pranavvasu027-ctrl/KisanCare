"""WeatherAPI.com adapter implementation supporting real-time conditions and forecasts."""
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List
import requests

from .base import BaseWeatherProvider
from .schemas import (
    CurrentWeatherResponse,
    WeatherForecastResponse,
    Coordinates,
    HourlyForecastItem,
    DailyForecastItem,
)


class WeatherAPIAdapter(BaseWeatherProvider):
    """
    Adapter for WeatherAPI.com.
    Requires an API key configured via WEATHERAPI_KEY or WEATHER_API_KEY.
    """

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: float = 4.0):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("WEATHERAPI_KEY") or os.getenv("WEATHER_API_KEY")
        self.timeout = timeout_seconds
        self.base_url = "https://api.weatherapi.com/v1"

    @property
    def provider_name(self) -> str:
        return "weatherapi"

    @property
    def attribution(self) -> str:
        return "Powered by WeatherAPI.com"

    def _execute_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("WeatherAPI key is required but not configured.")

        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}.json"

        max_attempts = 2
        last_error = None
        for attempt in range(max_attempts):
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    raise RuntimeError("WeatherAPI rate limit exceeded.")
                elif 400 <= resp.status_code < 500:
                    err_json = resp.json() if resp.headers.get("content-type") == "application/json" else {}
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    raise ValueError(f"WeatherAPI client error ({resp.status_code}): {err_msg}")
                else:
                    resp.raise_for_status()
            except (requests.Timeout, requests.ConnectionError) as req_err:
                last_error = req_err
                if attempt < max_attempts - 1:
                    time.sleep(0.5)

        raise RuntimeError(f"WeatherAPI request failed: {last_error}")

    def get_current(self, latitude: float, longitude: float, location_name: str = "Unknown") -> CurrentWeatherResponse:
        data = self._execute_request("current", {"q": f"{latitude},{longitude}", "aqi": "no"})
        current = data.get("current", {})
        condition = current.get("condition", {})

        return CurrentWeatherResponse(
            location=location_name,
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
            temperature=current.get("temp_c"),
            temperature_unit="°C",
            humidity=current.get("humidity"),
            humidity_unit="%",
            wind_speed_kmh=current.get("wind_kph"),
            wind_direction_deg=current.get("wind_degree"),
            surface_pressure_hpa=current.get("pressure_mb"),
            precipitation_mm=current.get("precip_mm"),
            weather_condition=condition.get("text", "Partly Cloudy"),
            weather_code=condition.get("code"),
            rainfall_probability="Unavailable",
            rainfall_since_sowing="Unavailable (No on-field rain gauge installed)",
            reference_evapotranspiration_mm=None,
            data_source=f"WeatherAPI.com ({latitude:.2f}°N, {longitude:.2f}°E)",
            provider=self.provider_name,
            observed_at=current.get("last_updated"),
            is_synthetic=False,
            is_stale=False,
            verified=True,
            attribution=self.attribution,
        )

    def get_forecast(self, latitude: float, longitude: float, forecast_days: int = 7, location_name: str = "Unknown") -> WeatherForecastResponse:
        clamped_days = max(1, min(14, forecast_days))
        data = self._execute_request("forecast", {"q": f"{latitude},{longitude}", "days": clamped_days, "aqi": "no", "alerts": "no"})
        current_data = data.get("current", {})
        forecast_days_data = data.get("forecast", {}).get("forecastday", [])

        # Current
        curr_cond = current_data.get("condition", {})
        current_res = CurrentWeatherResponse(
            location=location_name,
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
            temperature=current_data.get("temp_c"),
            temperature_unit="°C",
            humidity=current_data.get("humidity"),
            humidity_unit="%",
            wind_speed_kmh=current_data.get("wind_kph"),
            wind_direction_deg=current_data.get("wind_degree"),
            surface_pressure_hpa=current_data.get("pressure_mb"),
            precipitation_mm=current_data.get("precip_mm"),
            weather_condition=curr_cond.get("text", "Partly Cloudy"),
            weather_code=curr_cond.get("code"),
            rainfall_probability="Unavailable",
            rainfall_since_sowing="Unavailable (No on-field rain gauge installed)",
            reference_evapotranspiration_mm=None,
            data_source=f"WeatherAPI.com ({latitude:.2f}°N, {longitude:.2f}°E)",
            provider=self.provider_name,
            observed_at=current_data.get("last_updated"),
            is_synthetic=False,
            is_stale=False,
            verified=True,
            attribution=self.attribution,
        )

        daily_items: List[DailyForecastItem] = []
        hourly_items: List[HourlyForecastItem] = []

        for fday in forecast_days_data:
            day_info = fday.get("day", {})
            cond = day_info.get("condition", {})
            astro = fday.get("astro", {})
            daily_items.append(
                DailyForecastItem(
                    date=fday.get("date"),
                    temperature_max=day_info.get("maxtemp_c"),
                    temperature_min=day_info.get("mintemp_c"),
                    precipitation_sum_mm=day_info.get("totalprecip_mm"),
                    precipitation_probability_max=day_info.get("daily_chance_of_rain"),
                    et0_fao_evapotranspiration_mm=None,
                    weather_condition=cond.get("text", "Clear"),
                    weather_code=cond.get("code"),
                    sunrise=astro.get("sunrise"),
                    sunset=astro.get("sunset"),
                )
            )
            # Add hourly from the first day
            if not hourly_items:
                for h in fday.get("hour", [])[:24]:
                    h_cond = h.get("condition", {})
                    hourly_items.append(
                        HourlyForecastItem(
                            time=h.get("time"),
                            temperature=h.get("temp_c"),
                            humidity=h.get("humidity"),
                            precipitation_probability=h.get("chance_of_rain"),
                            precipitation_mm=h.get("precip_mm"),
                            wind_speed_kmh=h.get("wind_kph"),
                            weather_condition=h_cond.get("text", "Clear"),
                            weather_code=h_cond.get("code"),
                        )
                    )

        return WeatherForecastResponse(
            location=location_name,
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
            timezone="Asia/Kolkata",
            current=current_res,
            hourly=hourly_items,
            daily=daily_items,
            agricultural_advisory={
                "disclaimer": "Advisories are predictive meteorological guidance and not guaranteed to eliminate agronomic or weather risks.",
                "advisory_notes": ["Forecast sourced from WeatherAPI."],
            },
            provider=self.provider_name,
            data_source=f"WeatherAPI.com ({latitude:.2f}°N, {longitude:.2f}°E)",
            is_cached=False,
            is_stale=False,
            attribution=self.attribution,
        )
