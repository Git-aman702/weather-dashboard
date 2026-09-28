"""
Central configuration.

All settings are read from environment variables with safe defaults,
so the app runs out of the box in local dev and can be overridden in
Docker or production without changing code.
"""

from __future__ import annotations

import os


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class Settings:
    """Runtime settings, instantiated once at import time."""

    def __init__(self) -> None:
        self.open_meteo_forecast_url = _env_str(
            "OPEN_METEO_FORECAST_URL",
            "https://api.open-meteo.com/v1/forecast",
        )
        self.open_meteo_air_quality_url = _env_str(
            "OPEN_METEO_AIR_QUALITY_URL",
            "https://air-quality-api.open-meteo.com/v1/air-quality",
        )
        self.open_meteo_geocoding_url = _env_str(
            "OPEN_METEO_GEOCODING_URL",
            "https://geocoding-api.open-meteo.com/v1/search",
        )
        self.http_timeout_seconds = _env_float("HTTP_TIMEOUT_SECONDS", 15.0)
        self.forecast_days = _env_int("FORECAST_DAYS", 2)


settings = Settings()