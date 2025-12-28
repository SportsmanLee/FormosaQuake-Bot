"""Selection policy: merge, sort, and take Top N events."""

from __future__ import annotations

from typing import Iterable

from domain.models import EarthquakeEvent


def select_top_n(events: Iterable[EarthquakeEvent], n: int) -> list[EarthquakeEvent]:
    """Return newest N events by event_time (descending).

    Assumes event_time is ISO string sortable by time ordering.
    """

    return sorted(events, key=lambda e: e.event_time, reverse=True)[:n]


__all__ = ["select_top_n"]