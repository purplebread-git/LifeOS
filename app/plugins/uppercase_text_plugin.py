"""UppercaseTextPlugin — третья ось расширения: Plugin → DocumentExtractor.

Новый формат `.upper` подключается только через Plugin + composition root.
DocumentIngestionService / ExtractorRegistry / Agent не правятся под плагин
(ExtractorRegistry лишь получает расширенный dict из container).
"""

from __future__ import annotations

from app.core.document_extractor import DocumentExtractor
from app.core.plugin import Plugin
from app.core.plugin_registry import PluginRegistry

UPPERCASE_EXTENSION = ".upper"


class UppercaseTextExtractor(DocumentExtractor):
    """Декодирует UTF-8 и приводит текст к верхнему регистру.

    Скучный формат намеренно: цель PR — доказать ось расширения, не полезность.
    """

    async def extract(self, content: bytes) -> str:
        return content.decode("utf-8").upper()


class UppercaseTextPlugin(Plugin):
    def register(self, registry: PluginRegistry) -> None:
        registry.register_document_extractor(UPPERCASE_EXTENSION, UppercaseTextExtractor())

    async def on_startup(self) -> None:
        return None

    async def on_shutdown(self) -> None:
        return None
