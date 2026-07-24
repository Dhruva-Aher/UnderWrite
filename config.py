"""Centralized application settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System-wide configuration settings."""

    gms_url: str = "http://localhost:8080"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    policy_path: str = "policies.yaml"

    model_config = SettingsConfigDict(
        env_prefix="UNDERWRITE_",
        case_sensitive=False,
        extra="ignore",
    )


# Single global settings instance for application entry points
settings = Settings()
