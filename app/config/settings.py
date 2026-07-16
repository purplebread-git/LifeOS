from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

MemoryBackend = Literal["memory", "sqlite"]


class Settings(BaseSettings):
    """Единая точка правды о конфигурации приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_debug: bool = True

    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o-mini"
    openai_timeout: float = 60.0

    database_url: str = "sqlite+aiosqlite:///./lifeos.db"
    memory_backend: MemoryBackend = "sqlite"


@lru_cache
def get_settings() -> Settings:
    """Фабрика настроек с кэшированием — единственный instance на процесс."""
    return Settings()
