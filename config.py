"""Centralized application settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System-wide configuration settings."""

    gms_url: str = "http://localhost:8080"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    policy_path: str = "policies.yaml"
    max_lineage_depth: int = 6
    datahub_token: str | None = None
    # Overrides are a privileged exception to a blocked decision.  Keep them
    # disabled unless an operator explicitly provisions a secret.
    override_token: str | None = None

    # LLM Settings
    llm_provider: str = "openai"  # Options: openai, anthropic, gemini
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="UNDERWRITE_",
        case_sensitive=False,
        extra="ignore",
    )

# Single global settings instance for application entry points
settings = Settings()
