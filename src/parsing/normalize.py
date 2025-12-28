"""Normalize parsed CSV rows into EarthquakeEvent."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from domain.intensity import parse_intensity
from domain.models import EarthquakeEvent
from policies.keys import build_event_key


def normalize_row(row: dict[str, str], tz: str = "Asia/Taipei") -> EarthquakeEvent:
    event_time_local = row["地震時間"].strip()
    # Assumes CSV already in local time; store ISO for consistency
    try:
        dt = datetime.fromisoformat(event_time_local.replace(" ", "T"))
        dt = dt.replace(tzinfo=ZoneInfo(tz))
        event_time_iso = dt.isoformat()
    except Exception:
        event_time_iso = event_time_local  # fallback to raw string

    intensity_raw = row.get("最大震度")
    intensity_value = parse_intensity(intensity_raw)

    lon = float(row["經度"]) if row.get("經度") else 0.0
    lat = float(row["緯度"]) if row.get("緯度") else 0.0
    magnitude = float(row["規模"]) if row.get("規模") else 0.0
    depth_km = float(row["深度"]) if row.get("深度") else 0.0
    location_text = row.get("位置", "").strip()

    event_key = build_event_key(
        event_no=row.get("編號", ""),
        event_time=event_time_local,
        lon=lon,
        lat=lat,
        magnitude=magnitude,
        depth_km=depth_km,
    )

    return EarthquakeEvent(
        event_key=event_key,
        event_time=event_time_iso,
        lon=lon,
        lat=lat,
        magnitude=magnitude,
        depth_km=depth_km,
        intensity_raw=intensity_raw,
        intensity_value=intensity_value,
        location_text=location_text,
    )


__all__ = ["normalize_row"]