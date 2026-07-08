"""ExecutionContext — сервисный контейнер, передаваемый в Tool.execute()
и, в перспективе, в другие точки исполнения. Сознательно НЕ Pydantic-модель:
несёт ссылки на сервисы, а не данные для сериализации, и никогда не
сериализуется — живёт только внутри процесса."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.memory_provider import MemoryProvider


@dataclass
class ExecutionContext:
    conversation_id: str
    user_id: str | None = None
    memory: MemoryProvider | None = None
    metadata: dict[str, Any] = field(default_factory=dict)