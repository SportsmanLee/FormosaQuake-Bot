"""Event key and fingerprint helpers."""

from __future__ import annotations

import hashlib


def _hash(parts: list[str]) -> str:
    m = hashlib.sha256()
    for p in parts:
        m.update(p.encode("utf-8", errors="ignore"))
        m.update(b"|")
    return m.hexdigest()


def build_event_key(
    *,
    event_no: str,
    event_time: str,
    lon: float,
    lat: float,
    magnitude: float,
    depth_km: float,
) -> str:
    # Prefer numeric event number if available
    eno = event_no.strip()
    if eno.isdigit():
        return f"E:{eno}"

    # Fallback to hash of stable fields
    return "H:" + _hash(
        [
            event_time.strip(),
            f"{lon:.4f}",
            f"{lat:.4f}",
            f"{magnitude:.1f}",
            f"{depth_km:.1f}",
        ]
    )


def build_fingerprint(event_fields: list[str]) -> str:
    return _hash(event_fields)


__all__ = ["build_event_key", "build_fingerprint"]