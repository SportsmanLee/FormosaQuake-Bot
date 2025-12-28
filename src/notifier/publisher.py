"""Publisher that performs send/edit on Discord and updates DB mapping."""

from __future__ import annotations

import logging

import discord

from notifier.renderer import render_embed
from policies.publish import Decision
from store import repo


async def apply_decisions(
    *,
    client: discord.Client,
    db: repo.Database,
    channel_id: str,
    decisions: list[tuple[str, object, str | None]],
) -> None:
    """Execute send/edit based on decisions and persist message mapping.

    Assumes all decisions are for the same target channel (single-server scenario).
    """

    channel = client.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await client.fetch_channel(int(channel_id))
        except Exception as exc:  # noqa: BLE001
            logging.error("Channel %s not found or not sendable: %s", channel_id, exc)
            return

    if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
        logging.error("Channel %s not sendable (type=%s)", channel_id, type(channel))
        return

    for action, ev, _prior in decisions:
        if action == Decision.SKIP:
            continue
        embed = render_embed(ev)
        if action == Decision.SEND:
            msg = await channel.send(embed=embed)
            repo.upsert_published(
                db,
                event_key=ev.event_key,
                channel_id=str(channel.id),
                message_id=str(msg.id),
                last_published_hash=ev.fingerprint,
            )
        elif action == Decision.EDIT:
            row = repo.get_published(db, ev.event_key)
            if row is None:
                # fallback to send if missing mapping
                msg = await channel.send(embed=embed)
                repo.upsert_published(
                    db,
                    event_key=ev.event_key,
                    channel_id=str(channel.id),
                    message_id=str(msg.id),
                    last_published_hash=ev.fingerprint,
                )
                continue
            _ek, ch_id, msg_id, *_rest = row
            if str(ch_id) != str(channel.id):
                logging.warning("Channel mismatch for %s; expected %s got %s", ev.event_key, ch_id, channel.id)
            try:
                m = await channel.fetch_message(int(msg_id))
                await m.edit(embed=embed)
                repo.upsert_published(
                    db,
                    event_key=ev.event_key,
                    channel_id=str(channel.id),
                    message_id=str(msg.id),
                    last_published_hash=ev.fingerprint,
                )
            except Exception as exc:  # noqa: BLE001
                logging.warning("edit failed for %s (msg %s), fallback send: %s", ev.event_key, msg_id, exc)
                msg = await channel.send(embed=embed)
                repo.upsert_published(
                    db,
                    event_key=ev.event_key,
                    channel_id=str(channel.id),
                    message_id=str(msg.id),
                    last_published_hash=ev.fingerprint,
                )


__all__ = ["apply_decisions"]