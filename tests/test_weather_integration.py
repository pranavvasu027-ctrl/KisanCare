"""Unit and integration tests for the Weather integration including failure scenarios."""
import pytest
from unittest.mock import MagicMock, patch
import requests
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.weather.schemas import Coordinates, CurrentWeatherResponse, WeatherForecastResponse
from backend.app.weather.cache import WeatherCache
from backend.app.weather.open_meteo_adapter import OpenMeteoAdapter
from backend.app.weather.weatherapi_adapter import WeatherAPIAdapter
from backend.app.weather.service import WeatherService


@pytest.fixture
def client():
    return TestClient(app)


def test_weather_coordinates_validation():
    # Valid coordinates
    c = Coordinates(latitude=20.7002, longitude=77.0082)
    assert c.latitude == 20.7002
    assert c.longitude == 77.0082

    # Invalid latitude
    with pytest.raises(Exception):
        Coordinates(latitude=95.0, longitude=77.0)

    # Invalid longitude
    with pytest.raises(Exception):
        Coordinates(latitude=20.0, longitude=-195.0)


def test_weather_cache_ttl_and_stale():
    cache = WeatherCache(default_ttl_seconds=1, max_stale_seconds=3)
    cache.set("test", 20.7002, 77.0082, "test_data")

    # Immediate lookup: Fresh hit
    data, hit, stale = cache.get("test", 20.7002, 77.0082)
    assert hit is True
    assert stale is False
    assert data == "test_data"

    # Spatial binning: within ~1.1km (rounding to 2 decimal places)
    data_nearby, hit_nearby, _ = cache.get("test", 20.7011, 77.0079)
    assert hit_nearby is True
    assert data_nearby == "test_data"

    # Beyond spatial binning
    _, hit_far, _ = cache.get("test", 20.75, 77.05)
    assert hit_far is False


def test_open_meteo_adapter_normalizes_mocked_response():
    mock_payload = {
        "current": {
            "time": "2026-10-23T12:00",
            "temperature_2m": 31.5,
            "relative_humidity_2m": 58.0,
            "wind_speed_10m": 12.4,
            "wind_direction_10m": 180.0,
            "surface_pressure": 1012.3,
            "precipitation": 0.0,
            "weather_code": 1
        },
        "daily": {
            "time": ["2026-10-23"],
            "temperature_2m_max": [34.0],
            "temperature_2m_min": [22.0],
            "precipitation_sum": [0.0],
            "precipitation_probability_max": [10.0],
            "et0_fao_evapotranspiration": [4.8],
            "weather_code": [1],
            "sunrise": ["2026-10-23T06:15"],
            "sunset": ["2026-10-23T18:05"]
        },
        "hourly": {
            "time": ["2026-10-23T12:00", "2026-10-23T13:00"],
            "temperature_2m": [31.5, 32.0],
            "relative_humidity_2m": [58.0, 55.0],
            "precipitation_probability": [10.0, 15.0],
            "precipitation": [0.0, 0.0],
            "wind_speed_10m": [12.4, 13.0],
            "weather_code": [1, 1]
        },
        "timezone": "Asia/Kolkata"
    }

    adapter = OpenMeteoAdapter()
    with patch.object(adapter, "_execute_request", return_value=mock_payload):
        current = adapter.get_current(20.7002, 77.0082, "Akola")
        assert current.temperature == 31.5
        assert current.humidity == 58.0
        assert current.wind_speed_kmh == 12.4
        assert current.weather_condition == "Mainly Clear"
        assert current.rainfall_probability == "10.0%"
        assert current.reference_evapotranspiration_mm == 4.8
        assert "Open-Meteo" in current.data_source
        assert current.provider == "open-meteo"

        forecast = adapter.get_forecast(20.7002, 77.0082, forecast_days=7, location_name="Akola")
        assert len(forecast.daily) == 1
        assert forecast.daily[0].temperature_max == 34.0
        assert len(forecast.hourly) == 2
        assert "disclaimer" in forecast.agricultural_advisory


def test_weatherapi_adapter_normalizes_mocked_response():
    mock_payload = {
        "current": {
            "last_updated": "2026-10-23 12:00",
            "temp_c": 32.2,
            "humidity": 50,
            "wind_kph": 14.0,
            "wind_degree": 210,
            "pressure_mb": 1010.0,
            "precip_mm": 0.0,
            "condition": {"text": "Sunny", "code": 1000}
        },
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-10-23",
                    "day": {
                        "maxtemp_c": 35.0,
                        "mintemp_c": 21.0,
                        "totalprecip_mm": 0.0,
                        "daily_chance_of_rain": 5,
                        "condition": {"text": "Sunny", "code": 1000}
                    },
                    "astro": {"sunrise": "06:12 AM", "sunset": "06:01 PM"},
                    "hour": [
                        {
                            "time": "2026-10-23 12:00",
                            "temp_c": 32.2,
                            "humidity": 50,
                            "chance_of_rain": 5,
                            "precip_mm": 0.0,
                            "wind_kph": 14.0,
                            "condition": {"text": "Sunny", "code": 1000}
                        }
                    ]
                }
            ]
        }
    }

    adapter = WeatherAPIAdapter(api_key="mock_key")
    with patch.object(adapter, "_execute_request", return_value=mock_payload):
        current = adapter.get_current(20.7002, 77.0082, "Akola")
        assert current.temperature == 32.2
        assert current.humidity == 50.0
        assert current.wind_speed_kmh == 14.0
        assert current.weather_condition == "Sunny"
        assert current.provider == "weatherapi"


def test_weather_endpoints_api(client):
    # Test valid current weather
    res = client.get("/api/v1/weather/current?lat=20.7002&lon=77.0082")
    assert res.status_code == 200
    data = res.json()
    assert "temperature" in data
    assert "humidity" in data
    assert "weather_condition" in data
    assert "data_source" in data
    assert "attribution" in data

    # Test invalid coordinates (out of range latitude)
    res_bad = client.get("/api/v1/weather/current?lat=95.0&lon=77.0082")
    assert res_bad.status_code == 422
    assert "Invalid geographic coordinates" in res_bad.json()["detail"]

    # Test valid forecast endpoint
    res_forecast = client.get("/api/v1/weather/forecast?lat=20.7002&lon=77.0082&days=5")
    assert res_forecast.status_code == 200
    fdata = res_forecast.json()
    assert "current" in fdata
    assert "hourly" in fdata
    assert "daily" in fdata
    assert "agricultural_advisory" in fdata
    assert "disclaimer" in fdata["agricultural_advisory"]

    # Test invalid days range
    res_bad_days = client.get("/api/v1/weather/forecast?lat=20.7002&lon=77.0082&days=20")
    assert res_bad_days.status_code == 422


def test_provider_outage_and_timeout_resilience():
    service = WeatherService(cache=WeatherCache())
    # Mock provider failure
    mock_provider = MagicMock()
    mock_provider.provider_name = "open-meteo"
    mock_provider.attribution = "Weather data by Open-Meteo.com"
    mock_provider.get_current.side_effect = requests.Timeout("Network connection timed out")

    with patch.object(service, "get_provider", return_value=mock_provider):
        res = service.get_current_weather(20.7002, 77.0082, force_refresh=True)
        assert res.verified is False or res.is_stale is True
        assert res.weather_condition in ["Service Temporarily Unavailable", "Partly Cloudy"]
        assert "timed out" in res.data_source or "Supabase" in res.data_source


def test_weatherapi_missing_credentials(monkeypatch):
    monkeypatch.delenv("WEATHERAPI_KEY", raising=False)
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    adapter = WeatherAPIAdapter(api_key=None)
    with pytest.raises(ValueError) as exc:
        adapter.get_current(20.7002, 77.0082)
    assert "WeatherAPI key is required" in str(exc.value)


def test_openmeteo_rate_limit_handling():
    adapter = OpenMeteoAdapter()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"content-type": "application/json"}
    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc:
            adapter.get_current(20.7002, 77.0082)
        assert "rate limit exceeded" in str(exc.value)
