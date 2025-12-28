"""SQLite repository for settings, seen events, and published messages."""

import asyncio
import sqlite3
from pathlib import Path
from typing import Any


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


class Database:
    def __init__(self, db_path: str, schema_path: str | None = None) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path) if schema_path else Path(__file__).with_name("schema.sql")
        _ensure_parent(self.db_path)

    def init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            with self.schema_path.open("r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, params)
            conn.commit()

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(sql, params)
            return cur.fetchall()


# --- settings ---

def upsert_setting(db: Database, channel_id: str, enabled: bool) -> None:
    db.execute(
        """
        INSERT INTO settings (id, channel_id, enabled, updated_at)
        VALUES (1, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET channel_id=excluded.channel_id, enabled=excluded.enabled, updated_at=excluded.updated_at;
        """,
        (channel_id, 1 if enabled else 0),
    )


def get_setting(db: Database) -> tuple[str, bool] | None:
    row = db.fetchone("SELECT channel_id, enabled FROM settings WHERE id=1")
    if row is None:
        return None
    channel_id, enabled = row
    return str(channel_id), bool(enabled)


# --- seen_events ---

def upsert_seen(
    db: Database,
    event_key: str,
    event_time: str,
    intensity_raw: str | None,
    intensity_value: float | None,
    data_hash: str | None,
    last_payload: str | None,
) -> None:
    db.execute(
        """
        INSERT INTO seen_events (event_key, event_time, first_seen_at, last_seen_at, intensity_raw, intensity_value, data_hash, last_payload)
        VALUES (?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?)
        ON CONFLICT(event_key) DO UPDATE SET
            last_seen_at=excluded.last_seen_at,
            event_time=excluded.event_time,
            intensity_raw=excluded.intensity_raw,
            intensity_value=excluded.intensity_value,
            data_hash=excluded.data_hash,
            last_payload=excluded.last_payload;
        """,
        (
            event_key,
            event_time,
            intensity_raw,
            intensity_value,
            data_hash,
            last_payload,
        ),
    )


def get_seen(db: Database, event_key: str) -> tuple[Any, ...] | None:
    return db.fetchone(
        "SELECT event_key, event_time, first_seen_at, last_seen_at, intensity_raw, intensity_value, data_hash, last_payload FROM seen_events WHERE event_key=?",
        (event_key,),
    )


# --- published_messages ---

def upsert_published(
    db: Database,
    event_key: str,
    channel_id: str,
    message_id: str,
    last_published_hash: str | None,
) -> None:
    db.execute(
        """
        INSERT INTO published_messages (event_key, channel_id, message_id, published_at, last_edited_at, last_published_hash, status)
        VALUES (?, ?, ?, datetime('now'), NULL, ?, NULL)
        ON CONFLICT(event_key) DO UPDATE SET
            channel_id=excluded.channel_id,
            message_id=excluded.message_id,
            last_edited_at=datetime('now'),
            last_published_hash=excluded.last_published_hash;
        """,
        (event_key, channel_id, message_id, last_published_hash),
    )


def get_published(db: Database, event_key: str) -> tuple[Any, ...] | None:
    return db.fetchone(
        "SELECT event_key, channel_id, message_id, published_at, last_edited_at, last_published_hash, status FROM published_messages WHERE event_key=?",
        (event_key,),
    )


def list_published(db: Database) -> list[tuple[Any, ...]]:
    return db.fetchall(
        "SELECT event_key, channel_id, message_id, published_at, last_edited_at, last_published_hash, status FROM published_messages"
    )


def list_seen(db: Database) -> list[tuple[Any, ...]]:
    return db.fetchall(
        "SELECT event_key, event_time, first_seen_at, last_seen_at, intensity_raw, intensity_value, data_hash, last_payload FROM seen_events"
    )


# Convenience async wrappers (execute in default loop executor)

async def async_init(db: Database) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, db.init)


async def async_upsert_setting(db: Database, channel_id: str, enabled: bool) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, upsert_setting, db, channel_id, enabled)


async def async_get_setting(db: Database) -> tuple[str, bool] | None:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_setting, db)


async def async_upsert_seen(
    db: Database,
    event_key: str,
    event_time: str,
    intensity_raw: str | None,
    intensity_value: float | None,
    data_hash: str | None,
    last_payload: str | None,
) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        upsert_seen,
        db,
        event_key,
        event_time,
        intensity_raw,
        intensity_value,
        data_hash,
        last_payload,
    )


async def async_get_seen(db: Database, event_key: str) -> tuple[Any, ...] | None:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_seen, db, event_key)


async def async_upsert_published(
    db: Database,
    event_key: str,
    channel_id: str,
    message_id: str,
    last_published_hash: str | None,
) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, upsert_published, db, event_key, channel_id, message_id, last_published_hash)


async def async_get_published(db: Database, event_key: str) -> tuple[Any, ...] | None:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_published, db, event_key)


async def async_list_published(db: Database) -> list[tuple[Any, ...]]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, list_published, db)


async def async_list_seen(db: Database) -> list[tuple[Any, ...]]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, list_seen, db)