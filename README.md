# FormosaQuake Bot

A Discord bot that posts Taiwan earthquake (formal report) alerts to a configured channel. It polls CWA CSV data every 60s, deduplicates by event, and updates the same message when a report is revised.

## Features
- Formal report source: `GET /zh-tw/earthquake/data/` then `POST /zh-tw/earthquake/csv` (Big5 CSV)
- Polling: every 60s; fetch current month + previous month, Top N=20, dedup by event key
- Threshold: only publish when max intensity ≥ configured value (default 4)
- Message update: same event is edited when data changes; hash key kept in footer for debugging
- Slash commands: `/setup` to bind the announcement channel (single-server), `/status` to view current binding
- SQLite state: settings, seen events, published messages (persist via volume)
- Optional backoff on failures; optional insecure SSL (for troubleshooting only)

## Quick start (Docker Compose)
1) Prepare `.env` in project root:
   ```env
   DISCORD_TOKEN=your_bot_token
   DATA_BASE_URL=https://scweb.cwa.gov.tw
   SQLITE_PATH=/data/bot.db
   POLL_INTERVAL_SECONDS=60
   TOP_N=20
   INTENSITY_THRESHOLD=4
   TZ=Asia/Taipei
   # optional
   # ALLOW_INSECURE_SSL=false
   # BACKOFF_BASE_SECONDS=30
   # BACKOFF_MAX_SECONDS=300
   # ALLOWED_GUILD_ID=123456789012345678
   ```
2) (If not already) generate lockfile locally:
   ```bash
   uv lock
   ```
3) Build & run:
   ```bash
   docker compose build
   docker compose up -d
   docker compose logs -f app
   ```
4) In your Discord server, run `/setup` to bind the announcement channel, then `/status` to confirm.

## Local run (no Docker)
```bash
uv sync --dev
uv run python -m src.app
```
Requirements: Python 3.11+, `tzdata` (Windows/containers included via deps), `.env` as above.

## Slash commands
- `/setup channel:<text channel> enabled:<bool>`
- `/status`

## Configuration (env vars)
- `DISCORD_TOKEN` (required)
- `DATA_BASE_URL` (required, e.g. `https://scweb.cwa.gov.tw`)
- `SQLITE_PATH` (default `./data/bot.db` or `/data/bot.db` in Docker)
- `POLL_INTERVAL_SECONDS` (default 60)
- `TOP_N` (default 20)
- `INTENSITY_THRESHOLD` (default 4)
- `TZ` (default `Asia/Taipei`)
- `BACKOFF_BASE_SECONDS`, `BACKOFF_MAX_SECONDS` (optional; enables jittered exponential backoff)
- `ALLOWED_GUILD_ID` (optional single-guild gate)
- `ALLOW_INSECURE_SSL` (optional, default false; only for temporary troubleshooting SSL issues)

## Data flow (high level)
1. Poll current + previous month CSV → Big5 decode → parse
2. Normalize to `EarthquakeEvent` (time, coords, magnitude, depth, intensity)
3. Build event key (`E:<number>` or hash) and fingerprint
4. Select Top N (newest) → policy decide send/edit/skip
5. Persist seen; publish send/edit to Discord; update mapping

## Persistence
- SQLite tables: `settings`, `seen_events`, `published_messages`
- In Docker, `/data` is a named volume (see `compose.yml`)

## Development
- Lint/Test: `uv run pytest` (sample-based parsing tests included)
- Recommended: `ruff` (configured in `pyproject.toml`)

## Security notes
- Keep `DISCORD_TOKEN` and `.env` out of version control.
- `ALLOW_INSECURE_SSL` should remain false; use only for temporary SSL troubleshooting.
- Minimum Discord permissions: View Channel, Send Messages, Embed Links, Read Message History.

## License
MIT
