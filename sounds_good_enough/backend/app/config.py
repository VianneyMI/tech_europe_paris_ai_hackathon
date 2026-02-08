"""Application settings and environment configuration."""

from __future__ import annotations

from pydantic import Field, field_validator
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: object) -> object:
        """Accept a comma-separated string in addition to a JSON list."""
        if isinstance(v, str) and not v.strip().startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


def get_settings() -> Settings:
    """Return app settings loaded from environment variables."""

    return Settings()  # type: ignore[call-arg]
