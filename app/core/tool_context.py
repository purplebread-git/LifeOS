"""ToolContext — сервисный контейнер, передаваемый в Tool.execute().

Сознательно НЕ Pydantic-модель: несёт ссылки на сервисы (MemoryProvider
и т.д.), а не данные для валидации/сериализации. Pydantic — для данных,
которые куда-то едут (в LLM, в БД, в API-ответ); dataclass — для
контейнеров с зависимостями внутри одного процесса.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.memory_provider import MemoryProvider


@dataclass
class ToolContext:
    conversation_id: str
    user_id: str | None = None
    memory: MemoryProvider | None = None
    metadata: dict[str, Any] = field(default_factory=dict)