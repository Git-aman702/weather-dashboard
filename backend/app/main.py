"""
Minimal FastAPI service that proxies Open-Meteo.

Step 1 of the Weather Dashboard build:
prove we can fetch weather data and return it cleanly.

No database, no scheduler, no config module yet.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("weather.api")

app = FastAPI(title="Weather Dashboard API", version="0.1.0")

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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
    "precipitation",
    "precipitation_probability",
    "weather_code",
    "wind_speed_10m",
]


@app.get("/health")
async def health() -> dict[str, bool]:
    """Liveness check. Used later by Docker and uptime monitors."""
    return {"ok": True}


@app.get("/api/weather")
async def get_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    timezone: str = Query("auto", description="IANA tz or 'auto'"),
) -> dict[str, Any]:
    """
    Fetch current + hourly weather for a coordinate.

    Returns the raw Open-Meteo payload reshaped into a small,
    stable response so the frontend never depends on their schema.
    """
    params: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(CURRENT_VARS),
        "hourly": ",".join(HOURLY_VARS),
        "timezone": timezone,
        "forecast_days": 2,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPEN_METEO_FORECAST_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Open-Meteo returned %s: %s", exc.response.status_code, exc.response.text[:300])
        raise HTTPException(
            status_code=502,
            detail=f"Open-Meteo error: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Open-Meteo request failed: %s", exc)
        raise HTTPException(status_code=504, detail="Could not reach Open-Meteo") from exc

    return {
        "request": {"latitude": lat, "longitude": lon, "timezone": timezone},
        "source": "open-meteo",
        "units": payload.get("current_units", {}),
        "current": payload.get("current", {}),
        "hourly": payload.get("hourly", {}),
    }