"""Discord client with /setup and /status commands (single-guild)."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

from store import repo


ALLOWED_CHANNEL_TYPES = {discord.ChannelType.text, discord.ChannelType.news}


class DiscordBot(discord.Client):
    def __init__(self, *, db: repo.Database, allowed_guild_id: int | None) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.db = db
        self.allowed_guild_id = allowed_guild_id
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # register commands
        @self.tree.command(name="setup", description="綁定公告頻道並啟用/停用")
        @app_commands.describe(channel="公告頻道", enabled="是否啟用推送 (預設 True)")
        async def setup_cmd(interaction: discord.Interaction, channel: discord.TextChannel, enabled: bool = True):
            # guild gate
            if not interaction.guild_id:
                await interaction.response.send_message("請在伺服器內使用此指令", ephemeral=True)
                return
            if self.allowed_guild_id and interaction.guild_id != self.allowed_guild_id:
                await interaction.response.send_message("此 bot 未授權於此伺服器使用 /setup", ephemeral=True)
                return

            if channel.type not in ALLOWED_CHANNEL_TYPES:
                await interaction.response.send_message("僅支援文字/公告頻道", ephemeral=True)
                return

            # 寫入設定
            await repo.async_upsert_setting(self.db, str(channel.id), enabled)
            await interaction.response.send_message(
                f"已綁定頻道 <#{channel.id}>，啟用={enabled}", ephemeral=True
            )

        @self.tree.command(name="status", description="查看目前公告設定")
        async def status_cmd(interaction: discord.Interaction):
            if not interaction.guild_id:
                await interaction.response.send_message("請在伺服器內使用此指令", ephemeral=True)
                return
            if self.allowed_guild_id and interaction.guild_id != self.allowed_guild_id:
                await interaction.response.send_message("此 bot 未授權於此伺服器使用 /status", ephemeral=True)
                return

            setting = await repo.async_get_setting(self.db)
            if not setting:
                await interaction.response.send_message("尚未設定公告頻道 (/setup)", ephemeral=True)
                return
            channel_id, enabled = setting
            await interaction.response.send_message(
                f"公告頻道：<#{channel_id}>\n啟用：{enabled}",
                ephemeral=True,
            )

        # sync commands
        await self.tree.sync()

    async def on_ready(self) -> None:
        logging.info("Discord bot logged in as %s", self.user)


def create_bot(*, db: repo.Database, allowed_guild_id: int | None) -> DiscordBot:
    return DiscordBot(db=db, allowed_guild_id=allowed_guild_id)


async def start_bot(token: str, bot: DiscordBot) -> None:
    await bot.start(token)