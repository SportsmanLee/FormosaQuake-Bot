"""Application settings loaded from environment (.env supported)."""

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Aligned with Spec/Architecture: poll 60s, top 20, intensity >=4, single guild optional gate.
    """

    discord_token: str
    data_base_url: AnyUrl

    sqlite_path: str = "./data/bot.db"
    poll_interval_seconds: int = 60
    top_n: int = 20
    intensity_threshold: float = 4.0
    tz: str = "Asia/Taipei"
    allowed_guild_id: int | None = None
    backoff_base_seconds: float | None = None
    backoff_max_seconds: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


def load_settings() -> Settings:
    """Factory helper to keep a single import site in app entrypoint."""

    return Settings()