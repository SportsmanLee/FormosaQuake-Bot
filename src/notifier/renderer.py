"""Render Discord embeds for earthquake events."""

from __future__ import annotations

import discord

from domain.models import EarthquakeEvent


def _color_for_intensity(intensity: float | None) -> int:
    if intensity is None:
        return 0x666666
    if intensity >= 6:
        return 0xCC3300
    if intensity >= 5:
        return 0xFF6600
    if intensity >= 4:
        return 0xFFCC00
    return 0x6699FF


def render_embed(event: EarthquakeEvent) -> discord.Embed:
    color = _color_for_intensity(event.intensity_value)
    title = f"地震速報 | {event.event_key}"
    if event.intensity_raw:
        title += f" | 最大震度 {event.intensity_raw}"

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="發震時間", value=event.event_time, inline=False)
    embed.add_field(name="規模", value=f"M {event.magnitude:.1f}")
    embed.add_field(name="深度", value=f"{event.depth_km:.1f} km")
    embed.add_field(name="最大震度", value=event.intensity_raw or "未知")
    embed.add_field(name="位置", value=event.location_text or "")
    embed.add_field(name="震央", value=f"{event.lat:.4f}, {event.lon:.4f}")
    maps_url = f"https://www.google.com/maps?q={event.lat},{event.lon}"
    embed.add_field(name="地圖", value=maps_url, inline=False)
    embed.set_footer(text=f"source={event.source}")
    return embed


__all__ = ["render_embed"]