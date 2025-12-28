"""Domain models for earthquake events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EarthquakeEvent:
    event_key: str
    event_time: str  # ISO string (local TZ applied upstream)
    lon: float
    lat: float
    magnitude: float
    depth_km: float
    intensity_raw: str | None
    intensity_value: float | None
    location_text: str
    source: str = "cwa_csv"
    fingerprint: str | None = None


__all__ = ["EarthquakeEvent"]