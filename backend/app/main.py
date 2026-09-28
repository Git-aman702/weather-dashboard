"""
FastAPI service exposing a small weather API on top of Open-Meteo.

This module owns only routing and HTTP error translation.
The upstream call lives in `openmeteo.py`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from .openmeteo import OpenMeteoError, fetch_air_quality, fetch_forecast

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("weather.api")

app = FastAPI(title="Weather Dashboard API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, bool]:
    """Liveness check."""
    return {"ok": True}


@app.get("/api/weather")
async def get_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    timezone: str = Query("auto", description="IANA tz or 'auto'"),
    include_air_quality: bool = Query(False, description="Also fetch AQI"),
) -> dict[str, Any]:
    """
    Current + hourly weather for a coordinate.

    Optionally includes air quality. Air quality failures are non-fatal:
    the forecast is still returned.
    """
    try:
        payload = await fetch_forecast(lat, lon, timezone)
    except OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    air_quality: dict[str, Any] = {}
    if include_air_quality:
        try:
            aq_payload = await fetch_air_quality(lat, lon, timezone)
            air_quality = aq_payload.get("current", {})
        except OpenMeteoError as exc:
            logger.warning("air quality fetch failed: %s", exc)

    return {
        "request": {"latitude": lat, "longitude": lon, "timezone": timezone},
        "source": "open-meteo",
        "units": payload.get("current_units", {}),
        "current": payload.get("current", {}),
        "hourly": payload.get("hourly", {}),
        "air_quality": air_quality,
    }