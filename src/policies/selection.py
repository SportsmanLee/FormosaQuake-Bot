"""Selection policy: merge, sort, and take Top N events."""

from __future__ import annotations

from typing import Iterable

from domain.models import EarthquakeEvent


def select_top_n(events: Iterable[EarthquakeEvent], n: int | None = None, top_n: int | None = None) -> list[EarthquakeEvent]:
    """Return newest N events by event_time (descending).

    Supports both positional `n` and keyword `top_n` for call-site convenience.
    Assumes event_time is ISO string sortable by time ordering.
    """

    limit = top_n if top_n is not None else n
    if limit is None:
        raise ValueError("select_top_n requires n or top_n")

    return sorted(events, key=lambda e: e.event_time, reverse=True)[:limit]


__all__ = ["select_top_n"]