"""Discord client scaffold.

Currently only logs in and idles; slash commands will be added in a later step.
"""

import logging

import discord


class DiscordBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self) -> None:
        logging.info("Discord bot logged in as %s", self.user)


async def start_bot(token: str) -> None:
    bot = DiscordBot()
    await bot.start(token)