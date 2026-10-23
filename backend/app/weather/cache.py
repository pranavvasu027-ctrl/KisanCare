"""Thread-safe in-memory cache for weather data with TTL and spatial binning."""
from __future__ import annotations

import time
import threading
from typing import Any, Optional, Dict, Tuple


class WeatherCache:
    """
    Coordinates are rounded to 2 decimal places (~1.1 km precision at the equator)
    to prevent hammering the external weather provider when querying adjoining fields
    on the same farm or neighboring plots.
    """
    def __init__(self, default_ttl_seconds: int = 900, max_stale_seconds: int = 7200):
        # 15 minutes default TTL for fresh weather
        self.default_ttl = default_ttl_seconds
        # Up to 2 hours allowed as stale data in degraded mode before full rejection
        self.max_stale_seconds = max_stale_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _make_key(prefix: str, lat: float, lon: float, extra: str = "") -> str:
        rounded_lat = round(lat, 2)
        rounded_lon = round(lon, 2)
        return f"{prefix}:{rounded_lat:.2f}:{rounded_lon:.2f}:{extra}"

    def get(self, prefix: str, lat: float, lon: float, extra: str = "") -> Tuple[Optional[Any], bool, bool]:
        """
        Returns:
            (cached_data, is_hit, is_stale)
            If not found or older than max_stale_seconds: (None, False, False)
            If fresh (< default_ttl): (data, True, False)
            If stale (default_ttl <= age < max_stale_seconds): (data, True, True)
        """
        key = self._make_key(prefix, lat, lon, extra)
        now = time.time()
        with self._lock:
            if key not in self._store:
                return None, False, False
            ts, val = self._store[key]
            age = now - ts
            if age > self.max_stale_seconds:
                del self._store[key]
                return None, False, False
            if age > self.default_ttl:
                return val, True, True
            return val, True, False

    def set(self, prefix: str, lat: float, lon: float, value: Any, extra: str = "") -> None:
        key = self._make_key(prefix, lat, lon, extra)
        now = time.time()
        with self._lock:
            self._store[key] = (now, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
