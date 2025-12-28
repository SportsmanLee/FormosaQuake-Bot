"""Polling pipeline orchestration (no Discord side-effects yet)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from domain.models import EarthquakeEvent
from parsing.csv_parser import decode_big5, parse_csv
from parsing.normalize import normalize_row
from policies.publish import Decision, decide_actions
from policies.selection import select_top_n
from sources.cwa_csv import CwaCsvSource
from store import repo


async def fetch_month_events(source: CwaCsvSource, year: int, month: int, tz: str) -> list[EarthquakeEvent]:
    raw = await source.fetch_month_csv(year, month)
    text = decode_big5(raw)
    rows = parse_csv(text)
    events = [normalize_row(r, tz=tz) for r in rows]
    return events


def _current_and_prev_month(now: datetime) -> tuple[tuple[int, int], tuple[int, int]]:
    y, m = now.year, now.month
    if m == 1:
        return (y, m), (y - 1, 12)
    return (y, m), (y, m - 1)


async def run_poll(
    *,
    source: CwaCsvSource,
    db: repo.Database,
    top_n: int,
    intensity_threshold: float,
    tz: str,
) -> list[tuple[str, EarthquakeEvent, str | None]]:
    """Run one poll cycle and return decisions (send/edit/skip).

    This function does not perform Discord side-effects; it only returns the decisions
    and updates the database (seen/published) are left to caller.
    """

    now = datetime.now(ZoneInfo(tz))
    (y1, m1), (y2, m2) = _current_and_prev_month(now)

    # fetch both months
    events_1 = await fetch_month_events(source, y1, m1, tz)
    events_2 = await fetch_month_events(source, y2, m2, tz)
    merged = events_1 + events_2

    # load current state
    seen_rows = repo.list_seen(db)
    published_rows = repo.list_published(db)
    seen_lookup = {row[0]: row[6] for row in seen_rows}  # event_key -> data_hash (fingerprint placeholder)
    published_lookup = {row[0]: row[5] for row in published_rows}  # event_key -> last_published_hash

    # select Top N by time
    selected = select_top_n(merged, top_n=top_n)

    # decide actions
    decisions = decide_actions(
        selected,
        intensity_threshold=intensity_threshold,
        seen_lookup=seen_lookup,
        published_lookup=published_lookup,
    )

    # persist seen updates (all), published updates (send/edit only) to DB
    for action, ev, _prior in decisions:
        # seen
        repo.upsert_seen(
            db,
            event_key=ev.event_key,
            event_time=ev.event_time,
            intensity_raw=ev.intensity_raw,
            intensity_value=ev.intensity_value,
            data_hash=ev.fingerprint,
            last_payload=None,
        )
        # published
        if action in {Decision.SEND, Decision.EDIT}:
            repo.upsert_published(
                db,
                event_key=ev.event_key,
                channel_id="",  # channel mapping handled elsewhere
                message_id="",  # placeholder until Discord send/edit occurs
                last_published_hash=ev.fingerprint,
            )

    return decisions


async def poll_loop(
    *,
    source: CwaCsvSource,
    db: repo.Database,
    top_n: int,
    intensity_threshold: float,
    tz: str,
    interval_seconds: int,
) -> None:
    """Loop forever, running poll on interval. Does not include backoff yet."""

    while True:
        try:
            decisions = await run_poll(
                source=source,
                db=db,
                top_n=top_n,
                intensity_threshold=intensity_threshold,
                tz=tz,
            )
            logging.info("poll finished; decisions=%d", len(decisions))
        except Exception as exc:  # noqa: BLE001
            logging.exception("poll error: %s", exc)
        await asyncio.sleep(interval_seconds)
