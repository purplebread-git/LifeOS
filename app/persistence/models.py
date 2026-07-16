"""ORM-модели. Отдельны от доменных pydantic-моделей: домен остаётся
свободным от SQLAlchemy, провайдер отвечает за перевод одного в другое.

Имя столбца для произвольных атрибутов — memory_metadata, а НЕ metadata:
имя `metadata` зарезервировано SQLAlchemy (Base.metadata).
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
