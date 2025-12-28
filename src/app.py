"""App entrypoint.

Loads settings, configures logging, and starts the Discord bot (commands not yet wired).
"""

import asyncio
import logging

from config.settings import load_settings
from notifier.discord_client import start_bot
from observability.logging_setup import setup_logging
from service.backoff import Backoff
from service.poller import poll_loop
from sources.cwa_csv import CwaCsvSource
from store.repo import Database, async_init


async def async_main() -> None:
    setup_logging()
    settings = load_settings()
    # ensure DB schema
    db = Database(db_path=settings.sqlite_path)
    await async_init(db)

    # configure backoff if provided
    backoff = None
    if settings.backoff_base_seconds and settings.backoff_max_seconds:
        backoff = Backoff(settings.backoff_base_seconds, settings.backoff_max_seconds)

    # start CWA source
    source = CwaCsvSource(
        base_url=str(settings.data_base_url), allow_insecure_ssl=settings.allow_insecure_ssl
    )

    async def poller_task() -> None:
        await poll_loop(
            source=source,
            db=db,
            top_n=settings.top_n,
            intensity_threshold=settings.intensity_threshold,
            tz=settings.tz,
            interval_seconds=settings.poll_interval_seconds,
            backoff=backoff,
        )

    logging.info("Settings loaded; starting Discord bot and poller.")
    poller = asyncio.create_task(poller_task())
    try:
        await start_bot(settings.discord_token, db=db, allowed_guild_id=settings.allowed_guild_id)
    finally:
        poller.cancel()
        with contextlib.suppress(Exception):
            await poller
        await source.close()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()