"""Publish policy: decide send/edit/skip based on intensity and prior state."""

from __future__ import annotations

from typing import Iterable

from domain.models import EarthquakeEvent
from policies.keys import build_fingerprint


class Decision:
    SEND = "send"
    EDIT = "edit"
    SKIP = "skip"


def decide_actions(
    events: Iterable[EarthquakeEvent],
    *,
    intensity_threshold: float,
    seen_lookup: dict[str, str | None],  # event_key -> fingerprint or None
    published_lookup: dict[str, str | None],  # event_key -> last_published_hash
) -> list[tuple[str, EarthquakeEvent, str | None]]:
    """Return list of decisions: (action, event, prior_hash).

    - All events are assumed already filtered to Top N and merged.
    - seen_lookup: tracks any seen event (including < threshold).
    - published_lookup: tracks only events that have been published.
    """

    results: list[tuple[str, EarthquakeEvent, str | None]] = []
    for ev in events:
        fp = build_fingerprint(
            [
                ev.event_time,
                f"{ev.lon:.4f}",
                f"{ev.lat:.4f}",
                f"{ev.magnitude:.1f}",
                f"{ev.depth_km:.1f}",
                ev.intensity_raw or "",
                str(ev.intensity_value) if ev.intensity_value is not None else "",
                ev.location_text,
            ]
        )

        # update in-memory fingerprint so caller can persist to seen
        ev.fingerprint = fp

        # Only numbered reports (event_key startswith "E:") are eligible to publish/edit.
        is_numbered_report = ev.event_key.startswith("E:")
        if not is_numbered_report:
            results.append((Decision.SKIP, ev, None))
            continue

        # rules: primary threshold on intensity; secondary exception for
        # shallow, larger quakes even if intensity僅達 3（常見實務門檻）。
        primary_hit = (
            ev.intensity_value is not None
            and ev.intensity_value >= intensity_threshold
        )
        secondary_hit = (
            ev.intensity_value is not None
            and ev.intensity_value >= 3
            and ev.magnitude is not None
            and ev.magnitude >= 5.5
            and ev.depth_km is not None
            and ev.depth_km <= 40
        )

        # below all thresholds: never send/edit
        if not (primary_hit or secondary_hit):
            results.append((Decision.SKIP, ev, None))
            continue

        prior_pub = published_lookup.get(ev.event_key)
        if prior_pub is None:
            # not published yet, above threshold -> send
            results.append((Decision.SEND, ev, None))
        else:
            # already published; compare hash
            if prior_pub != fp:
                results.append((Decision.EDIT, ev, prior_pub))
            else:
                results.append((Decision.SKIP, ev, prior_pub))

        # also ensure seen_lookup is updated by caller (done outside)

    return results


__all__ = ["Decision", "decide_actions"]