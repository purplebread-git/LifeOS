"""DocumentExtractor — контракт извлечения текста из сырого документа.

Единственная ответственность: bytes → text. Extractor НЕ знает про chunking,
KnowledgeProvider, embeddings или формат-роутинг. Разные форматы (plain text,
Markdown, PDF, DOCX, HTML, remote URL) — это разные реализации одного
контракта: добавление формата = новый адаптер, а не правка пайплайна.

Контракт async намеренно: будущие extractor'ы бывают IO-bound (remote) и
CPU-bound (PDF) — единый async-интерфейс не придётся менять.
"""

from abc import ABC, abstractmethod


class DocumentExtractor(ABC):
    @abstractmethod
    async def extract(self, content: bytes) -> str:
        raise NotImplementedError
