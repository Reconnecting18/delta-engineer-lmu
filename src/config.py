from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    port: int = 8000
    host: str = "0.0.0.0"
    env: Environment = Environment.DEVELOPMENT
    log_level: str = "info"

    # Database
    database_url: str = "sqlite+aiosqlite:///telemetry.db"

    # Telemetry capture
    telemetry_poll_rate_ms: int = 10
    telemetry_batch_size: int = 100
    max_batch_size: int = 1000

    # Session management
    session_gap_threshold_seconds: int = 300

    # E3N integration
    e3n_enabled: bool = False
    e3n_endpoint: str = "http://localhost:3000/ingest"

    # Alerts
    alerts_enabled: bool = True
    alerts_default_rules: bool = True

    # WebSocket
    ws_heartbeat_interval_s: int = 30

    # App metadata
    app_name: str = "LMU Telemetry API"
    app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Factory that can be used as a FastAPI dependency."""
    return Settings()
