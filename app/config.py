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


@lru_cache
def get_settings() -> Settings:
    return Settings()
