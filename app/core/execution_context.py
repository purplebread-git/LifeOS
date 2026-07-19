"""ExecutionContext — реестр capabilities, доступных инструментам через
Tool.execute(). Сознательно НЕ Pydantic-модель: несёт ссылки на сервисы, а не
данные для сериализации, и никогда не сериализуется — живёт только внутри
процесса.

Правило: здесь живут только capabilities (memory, knowledge, ingestion, ...),
а не технические зависимости (database, embedding_provider, settings, logger) —
иначе он выродится в service locator. Инструмент получает возможность, не зная,
где и как она создаётся.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.knowledge_provider import KnowledgeProvider
    from app.core.memory_provider import MemoryProvider
    from app.knowledge.document_ingestion_service import DocumentIngestionService


@dataclass
class ExecutionContext:
    conversation_id: str
    user_id: str | None = None
    memory: MemoryProvider | None = None
    knowledge: KnowledgeProvider | None = None
    ingestion: DocumentIngestionService | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
