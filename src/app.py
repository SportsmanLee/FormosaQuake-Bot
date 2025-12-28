"""App entrypoint.

Loads settings, configures logging, and starts the Discord bot (commands not yet wired).
"""

import asyncio
import logging

from config.settings import load_settings
from notifier.discord_client import start_bot
from observability.logging_setup import setup_logging
from store.repo import Database, async_init


async def async_main() -> None:
    setup_logging()
    settings = load_settings()
    # ensure DB schema
    db = Database(db_path=settings.sqlite_path)
    await async_init(db)

    logging.info("Settings loaded; starting Discord bot.")
    await start_bot(settings.discord_token, db=db, allowed_guild_id=settings.allowed_guild_id)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()