"""SQLAlchemy async engine и его жизненный цикл.

`init_database` — генератор для providers.Resource в контейнере: создаёт
engine, поднимает схему (create_all — Alembic появится отдельным PR, когда
таблиц станет больше), отдаёт async_sessionmaker и корректно закрывает
engine на shutdown.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def create_engine(database_url: str) -> AsyncEngine:
    """Создать async engine.

    Для in-memory SQLite нужен StaticPool: без него каждое соединение
    получает собственную пустую БД, и данные между сессиями теряются.
    """
    if _is_memory_sqlite(database_url):
        return create_async_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(database_url)


async def init_database(
    database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(database_url)

    # Импорт моделей до create_all: они должны быть зарегистрированы в
    # Base.metadata. Импорт здесь (а не на уровне модуля) исключает
    # циклический импорт database <-> models.
    from app.persistence import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        yield session_factory
    finally:
        await engine.dispose()


def _is_memory_sqlite(database_url: str) -> bool:
    return ":memory:" in database_url or database_url.endswith("sqlite+aiosqlite://")
