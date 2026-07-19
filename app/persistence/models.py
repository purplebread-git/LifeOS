"""ORM-модели. Отдельны от доменных pydantic-моделей: домен остаётся
свободным от SQLAlchemy, провайдер отвечает за перевод одного в другое.

Имя столбца для произвольных атрибутов — *_metadata, а НЕ metadata:
имя `metadata` зарезервировано SQLAlchemy (Base.metadata).

Memory и Knowledge — разные таблицы и разные доменные сущности; общей ORM
базы у них нет намеренно (см. app/models/knowledge.py). С появлением второй
таблицы create_all остаётся достаточным; Alembic — когда схема начнёт
эволюционировать.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


class MemoryRecord(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # nullable: запись сохраняется даже если генерация эмбеддинга не удалась
    # (сбой OpenAI). Поиск деградирует к substring для таких записей.
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True, default=None)


class KnowledgeRecord(Base):
    __tablename__ = "knowledge"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    knowledge_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # nullable: чанк сохраняется даже если генерация эмбеддинга не удалась
    # (сбой OpenAI). Поиск деградирует к substring для таких записей.
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True, default=None)
