"""Application settings and environment configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    gradium_api_key: str = Field("", alias="GRADIUM_API_KEY")
    demucs_model: str = "htdemucs"
    demucs_device: str = "cpu"
    upload_max_mb: int = 50
    job_ttl_seconds: int = 1800
    cleanup_interval_seconds: int = 300
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


def get_settings() -> Settings:
    """Return app settings loaded from environment variables."""

    return Settings()  # type: ignore[call-arg]
