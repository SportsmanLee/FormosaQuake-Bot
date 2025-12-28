"""App entrypoint.

Loads settings, configures logging, and starts the Discord bot (commands not yet wired).
"""

import asyncio
import logging

from config.settings import load_settings
from notifier.discord_client import start_bot
from observability.logging_setup import setup_logging


async def async_main() -> None:
    setup_logging()
    settings = load_settings()
    logging.info("Settings loaded; starting Discord bot (commands not yet wired).")
    await start_bot(settings.discord_token)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()