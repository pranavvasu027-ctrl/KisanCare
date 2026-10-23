"""Open-Meteo weather adapter supporting standard and commercial API endpoints."""
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List
import requests

from .base import BaseWeatherProvider, wmo_code_to_text
from .schemas import (
    CurrentWeatherResponse,
    WeatherForecastResponse,
    Coordinates,
    HourlyForecastItem,
    DailyForecastItem,
)


class OpenMeteoAdapter(BaseWeatherProvider):
    """
    Adapter for Open-Meteo API.
    Supports:
    - Free/Development API: https://api.open-meteo.com/v1/forecast
    - Commercial Subscription API: https://customer-api.open-meteo.com/v1/forecast
    
    Authentication:
    Commercial keys are read from OPEN_METEO_API_KEY or WEATHER_API_KEY.
    When a commercial key is configured, requests automatically target the dedicated
    customer API endpoint or attach the apikey parameter.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: float = 4.0,
        commercial_endpoint: bool = False,
    ):
        self.api_key = api_key or os.getenv("OPEN_METEO_API_KEY") or os.getenv("WEATHER_API_KEY")
        self.timeout = timeout_seconds
        
        # Decide endpoint: if commercial key or explicit flag, use customer host
        if commercial_endpoint or (self.api_key and os.getenv("WEATHER_COMMERCIAL_MODE", "false").lower() == "true"):
            self.base_url = "https://customer-api.open-meteo.com/v1/forecast"
        else:
            self.base_url = "https://api.open-meteo.com/v1/forecast"

    @property
    def provider_name(self) -> str:
        return "open-meteo"

    @property
    def attribution(self) -> str:
        return "Weather data by Open-Meteo.com (CC BY 4.0)"

    def _execute_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes HTTP request with bounded retry and timeout."""
        if self.api_key:
            params["apikey"] = self.api_key

        max_attempts = 2
        last_error: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                resp = requests.get(self.base_url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    raise RuntimeError("Open-Meteo rate limit exceeded. Please back off or configure commercial key.")
                elif resp.status_code >= 400 and resp.status_code < 500:
                    err_msg = resp.json().get("reason", resp.text) if resp.headers.get("content-type") == "application/json" else resp.text
                    raise ValueError(f"Open-Meteo validation error ({resp.status_code}): {err_msg}")
                else:
                    resp.raise_for_status()
            except (requests.Timeout, requests.ConnectionError) as req_err:
                last_error = req_err
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
            except Exception as e:
                raise e

        raise RuntimeError(f"Open-Meteo connection failure: {last_error}")

    def get_current(self, latitude: float, longitude: float, location_name: str = "Unknown") -> CurrentWeatherResponse:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation,weather_code",
            "daily": "precipitation_probability_max,et0_fao_evapotranspiration",
            "timezone": "Asia/Kolkata",
            "forecast_days": 1,
        }

        data = self._execute_request(params)
        curr = data.get("current", {})
        daily = data.get("daily", {})
        code = curr.get("weather_code")
        precip_prob_list = daily.get("precipitation_probability_max", [])
        precip_prob = precip_prob_list[0] if precip_prob_list else None
        et0_list = daily.get("et0_fao_evapotranspiration", [])
        et0 = et0_list[0] if et0_list else None

        return CurrentWeatherResponse(
            location=location_name,
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
            temperature=curr.get("temperature_2m"),
            temperature_unit="°C",
            humidity=curr.get("relative_humidity_2m"),
            humidity_unit="%",
            wind_speed_kmh=curr.get("wind_speed_10m"),
            wind_direction_deg=curr.get("wind_direction_10m"),
            surface_pressure_hpa=curr.get("surface_pressure"),
            precipitation_mm=curr.get("precipitation"),
            weather_condition=wmo_code_to_text(code),
            weather_code=code,
            rainfall_probability=f"{precip_prob}%" if precip_prob is not None else "Unavailable",
            rainfall_since_sowing="Unavailable (No on-field rain gauge installed)",
            reference_evapotranspiration_mm=et0,
            data_source=f"Open-Meteo ({latitude:.2f}°N, {longitude:.2f}°E)",
            provider=self.provider_name,
            observed_at=curr.get("time"),
            is_synthetic=False,
            is_stale=False,
            verified=True,
            attribution=self.attribution,
        )

    def get_forecast(self, latitude: float, longitude: float, forecast_days: int = 7, location_name: str = "Unknown") -> WeatherForecastResponse:
        clamped_days = max(1, min(14, forecast_days))
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation,weather_code",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration,weather_code,sunrise,sunset",
            "timezone": "Asia/Kolkata",
            "forecast_days": clamped_days,
        }

        data = self._execute_request(params)
        curr_raw = data.get("current", {})
        daily_raw = data.get("daily", {})
        hourly_raw = data.get("hourly", {})

        current_res = self.get_current(latitude, longitude, location_name=location_name)

        # Parse hourly (next 24-48 hours)
        hourly_items: List[HourlyForecastItem] = []
        h_times = hourly_raw.get("time", [])
        h_temps = hourly_raw.get("temperature_2m", [])
        h_hums = hourly_raw.get("relative_humidity_2m", [])
        h_probs = hourly_raw.get("precipitation_probability", [])
        h_precips = hourly_raw.get("precipitation", [])
        h_winds = hourly_raw.get("wind_speed_10m", [])
        h_codes = hourly_raw.get("weather_code", [])

        # Include up to 24 hours of hourly forecast
        limit_hours = min(24, len(h_times))
        for i in range(limit_hours):
            h_code = h_codes[i] if i < len(h_codes) else None
            hourly_items.append(
                HourlyForecastItem(
                    time=h_times[i],
                    temperature=h_temps[i] if i < len(h_temps) else None,
                    humidity=h_hums[i] if i < len(h_hums) else None,
                    precipitation_probability=h_probs[i] if i < len(h_probs) else None,
                    precipitation_mm=h_precips[i] if i < len(h_precips) else None,
                    wind_speed_kmh=h_winds[i] if i < len(h_winds) else None,
                    weather_condition=wmo_code_to_text(h_code),
                    weather_code=h_code,
                )
            )

        # Parse daily
        daily_items: List[DailyForecastItem] = []
        d_times = daily_raw.get("time", [])
        d_tmax = daily_raw.get("temperature_2m_max", [])
        d_tmin = daily_raw.get("temperature_2m_min", [])
        d_psum = daily_raw.get("precipitation_sum", [])
        d_pprob = daily_raw.get("precipitation_probability_max", [])
        d_et0 = daily_raw.get("et0_fao_evapotranspiration", [])
        d_codes = daily_raw.get("weather_code", [])
        d_sunrises = daily_raw.get("sunrise", [])
        d_sunsets = daily_raw.get("sunset", [])

        for i in range(len(d_times)):
            d_code = d_codes[i] if i < len(d_codes) else None
            daily_items.append(
                DailyForecastItem(
                    date=d_times[i],
                    temperature_max=d_tmax[i] if i < len(d_tmax) else None,
                    temperature_min=d_tmin[i] if i < len(d_tmin) else None,
                    precipitation_sum_mm=d_psum[i] if i < len(d_psum) else None,
                    precipitation_probability_max=d_pprob[i] if i < len(d_pprob) else None,
                    et0_fao_evapotranspiration_mm=d_et0[i] if i < len(d_et0) else None,
                    weather_condition=wmo_code_to_text(d_code),
                    weather_code=d_code,
                    sunrise=d_sunrises[i] if i < len(d_sunrises) else None,
                    sunset=d_sunsets[i] if i < len(d_sunsets) else None,
                )
            )

        # Agronomic summary context (explicitly non-guaranteed advisory)
        max_rain_day = max((d.precipitation_sum_mm or 0.0) for d in daily_items) if daily_items else 0.0
        avg_et0 = (
            sum((d.et0_fao_evapotranspiration_mm or 0.0) for d in daily_items) / len(daily_items)
            if daily_items
            else 0.0
        )
        
        advisory_notes = []
        if max_rain_day > 25.0:
            advisory_notes.append("Moderate to heavy rainfall forecast during the week; consider delaying foliar pesticide/fungicide sprays.")
        if current_res.temperature and current_res.temperature > 37.0:
            advisory_notes.append("Elevated daytime heat; monitor soil moisture closely and irrigate during cooler morning/evening hours.")
        if not advisory_notes:
            advisory_notes.append("Agro-climatic forecast conditions are within normal regional thresholds.")

        return WeatherForecastResponse(
            location=location_name,
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
            timezone=data.get("timezone", "Asia/Kolkata"),
            current=current_res,
            hourly=hourly_items,
            daily=daily_items,
            agricultural_advisory={
                "average_daily_et0_mm": round(avg_et0, 2),
                "max_single_day_rain_mm": round(max_rain_day, 1),
                "advisory_notes": advisory_notes,
                "disclaimer": "Advisories are predictive meteorological guidance and not guaranteed to eliminate agronomic or weather risks. Consult local Krishi Vigyan Kendra (KVK) for critical field interventions.",
            },
            provider=self.provider_name,
            data_source=f"Open-Meteo NWP Ensemble ({latitude:.2f}°N, {longitude:.2f}°E)",
            is_cached=False,
            is_stale=False,
            attribution=self.attribution,
        )
