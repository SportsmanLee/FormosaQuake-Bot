"""CSV decoding and parsing utilities for CWA earthquake CSV (Big5, comma)."""

from __future__ import annotations

import csv


def decode_big5(data: bytes) -> str:
    """Decode bytes using Big5. Raises UnicodeDecodeError on failure."""

    return data.decode("big5")


def parse_csv(text: str) -> list[dict[str, str]]:
    """Parse CSV text (header row + comma separated) into list of dicts."""

    reader = csv.DictReader(text.splitlines())
    return [dict(row) for row in reader]


__all__ = ["decode_big5", "parse_csv"]