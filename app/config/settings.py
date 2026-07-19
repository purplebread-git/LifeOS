from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

MemoryBackend = Literal["memory", "sqlite"]
MemorySearchMode = Literal["substring", "semantic"]
KnowledgeBackend = Literal["memory", "sqlite"]
KnowledgeSearchMode = Literal["substring", "semantic"]


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
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout: float = 60.0

    database_url: str = "sqlite+aiosqlite:///./lifeos.db"
    # backend = storage (где хранить), search_mode = как искать.
    # semantic — это режим поиска поверх sqlite-хранилища, а не отдельный backend.
    memory_backend: MemoryBackend = "sqlite"
    memory_search_mode: MemorySearchMode = "substring"
    # Порог cosine-близости для semantic-ранжирования: кандидаты ниже отсекаются
    # как шум. Включён по умолчанию; тюнится под embedding-модель через env.
    memory_similarity_threshold: float = Field(default=0.25, ge=0.0, le=1.0)

    # storage знаний (in-memory для разработки/тестов, sqlite — persistent) и
    # режим поиска. semantic — режим поверх sqlite-хранилища, как у памяти.
    knowledge_backend: KnowledgeBackend = "sqlite"
    knowledge_search_mode: KnowledgeSearchMode = "substring"
    # Порог cosine-близости для semantic-ранжирования знаний. Тот же дефолт, что
    # у памяти: одна embedding-модель, одна метрика, одна задача — отсечь шум.
    knowledge_similarity_threshold: float = Field(default=0.25, ge=0.0, le=1.0)


@lru_cache
def get_settings() -> Settings:
    """Фабрика настроек с кэшированием — единственный instance на процесс."""
    return Settings()
