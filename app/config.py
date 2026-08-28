from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "SMPilot AI"
    app_env: str = "development"
    app_debug: bool = False
    app_base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://smpilot:smpilot@localhost/smpilot"
    session_secret: str = Field(default="development-only-change-me", repr=False)
    session_cookie_name: str = "smpilot_session"
    session_max_age: int = 60 * 60 * 24 * 14
    password_reset_minutes: int = 30
    ai_provider: str = "openrouter"
    openrouter_api_key: str = Field(default="", repr=False)
    openrouter_model: str = "openrouter/free"
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-5-mini"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = Field(default="", repr=False)
    smtp_from: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def ai_api_key(self) -> str:
        return self.openrouter_api_key if self.ai_provider == "openrouter" else self.openai_api_key

    @property
    def ai_model(self) -> str:
        return self.openrouter_model if self.ai_provider == "openrouter" else self.openai_model

    @property
    def ai_base_url(self) -> str | None:
        return "https://openrouter.ai/api/v1" if self.ai_provider == "openrouter" else None

    def validate_production_security(self) -> None:
        if self.is_production and self.session_secret == "development-only-change-me":
            raise RuntimeError("SESSION_SECRET must be configured in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
