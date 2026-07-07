from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Единая точка правды о конфигурации приложения.

    Ничто в проекте не должно читать переменные окружения напрямую —
    только через эту модель, внедряемую через DI.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_debug: bool = True

    openai_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./lifeos.db"


@lru_cache
def get_settings() -> Settings:
    """Фабрика настроек с кэшированием — единственный instance на процесс."""
    return Settings()
