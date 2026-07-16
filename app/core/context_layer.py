"""ContextLayer — pipeline-контракт слоя сборки контекста.

Каждый слой получает уже накопленный контекст и возвращает новый. Слои-
производители (System / Memory / Knowledge / Conversation) обычно добавляют
свои сообщения: `return [*context, *mine]`. Но контракт сознательно
pipeline, а не producer: будущие слои-трансформеры (Token Budget, Trimming,
Compression, Deduplication) смогут вернуть изменённый контекст целиком без
слома интерфейса.
"""

from abc import ABC, abstractmethod

from app.models.conversation import Conversation
from app.models.message import Message


class ContextLayer(ABC):
    @abstractmethod
    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        raise NotImplementedError
