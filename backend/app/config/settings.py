from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Central application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./lexishelf.db"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Render/Railway/Neon commonly hand out the legacy "postgres://" scheme,
        # which SQLAlchemy 2.x no longer accepts.
        if value.startswith("postgres://"):
            return "postgresql://" + value[len("postgres://") :]
        return value

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_agent_model: str = "qwen/qwen3.8-27b"
    groq_temperature: float = 0.3

    notion_client_id: str = ""
    notion_client_secret: str = ""
    notion_redirect_uri: str = ""
    notion_oauth_state_secret: str = ""
    notion_token_encryption_key: str = ""
    notion_api_base_url: str = "https://api.notion.com"
    notion_api_version: str = "2026-03-11"
    app_web_url: str = "http://localhost:8081"

    jwt_signing_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    environment: str = "development"
    log_level: str = "INFO"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
