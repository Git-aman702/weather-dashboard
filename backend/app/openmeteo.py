"""
Async client for the Open-Meteo APIs.

Every public function returns the parsed JSON dict from Open-Meteo.
Callers (API routes, scheduler, alerts) never touch httpx directly,
so upstream changes only need to be handled in this one module.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


# Variables we ask Open-Meteo for on every forecast call.
# Kept as module constants so they're easy to find and extend.
CURRENT_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "pressure_msl",
    "cloud_cover",
]

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "precipitation_probability",
    "weather_code",
    "wind_speed_10m",
    "wind_gusts_10m",
]

AIR_QUALITY_VARS = [
    "european_aqi",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
]


class OpenMeteoError(RuntimeError):
    """Raised when Open-Meteo is unreachable or returns an error status."""


async def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Shared GET helper with consistent logging and error mapping."""
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Open-Meteo returned %s for %s: %s",
            exc.response.status_code,
            url,
            exc.response.text[:300],
        )
        raise OpenMeteoError(
            f"Open-Meteo error {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Open-Meteo request failed for %s: %s", url, exc)
        raise OpenMeteoError("Could not reach Open-Meteo") from exc


async def fetch_forecast(
    lat: float,
    lon: float,
    timezone: str = "auto",
    forecast_days: int | None = None,
) -> dict[str, Any]:
    """Fetch current + hourly forecast for a coordinate."""
    params: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(CURRENT_VARS),
        "hourly": ",".join(HOURLY_VARS),
        "timezone": timezone,
        "forecast_days": forecast_days or settings.forecast_days,
    }
    return await _get_json(settings.open_meteo_forecast_url, params)


async def fetch_air_quality(
    lat: float,
    lon: float,
    timezone: str = "auto",
) -> dict[str, Any]:
    """Fetch current European AQI and the main pollutants."""
    params: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(AIR_QUALITY_VARS),
        "timezone": timezone,
        "forecast_days": 1,
    }
    return await _get_json(settings.open_meteo_air_quality_url, params)