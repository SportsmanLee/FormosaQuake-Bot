"""Intensity parsing and normalization."""

from __future__ import annotations

import re
from typing import Optional


_PAT_WEAK_STRONG = re.compile(r"^(?P<int>\d+)(?P<qualifier>[弱强強])$")
_PAT_PLUS_MINUS = re.compile(r"^(?P<int>\d+)(?P<qualifier>[+-])$")


def parse_intensity(raw: str | None) -> Optional[float]:
    """Parse intensity strings like '4', '5弱', '5強', '4-', '4+' into a comparable float.

    Returns None if cannot be parsed.
    """

    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    # pure number
    if s.isdigit():
        try:
            return float(s)
        except ValueError:
            return None
    # 5弱 / 5強
    m = _PAT_WEAK_STRONG.match(s)
    if m:
        base = float(m.group("int"))
        q = m.group("qualifier")
        if q in {"弱"}:
            return base
        if q in {"强", "強"}:
            return base + 0.5
    # 4- / 4+
    m = _PAT_PLUS_MINUS.match(s)
    if m:
        base = float(m.group("int"))
        q = m.group("qualifier")
        if q == "-":
            return base - 0.1
        if q == "+":
            return base + 0.1
    return None


__all__ = ["parse_intensity"]