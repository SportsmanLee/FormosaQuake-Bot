-- settings: single-server channel binding (extend if multi-guild in future)
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    channel_id TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

-- seen_events: track all seen events (including intensity < 4)
CREATE TABLE IF NOT EXISTS seen_events (
    event_key TEXT PRIMARY KEY,
    event_time TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    intensity_raw TEXT,
    intensity_value REAL,
    data_hash TEXT,
    last_payload TEXT
);

-- published_messages: events that have been published (intensity >= 4)
CREATE TABLE IF NOT EXISTS published_messages (
    event_key TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    published_at TEXT NOT NULL,
    last_edited_at TEXT,
    last_published_hash TEXT,
    status TEXT
);

CREATE INDEX IF NOT EXISTS idx_seen_events_last_seen_at ON seen_events(last_seen_at);