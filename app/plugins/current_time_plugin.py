"""CurrentTimePlugin — второй тип расширения: Plugin → ContextLayer.

Доказывает non-tool ось платформы. Composition root подключает плагин;
Agent / ConversationEngine / LayeredContextBuilder не меняются.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.core.context_layer import ContextLayer
from app.core.plugin import Plugin
from app.core.plugin_registry import PluginRegistry
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock

TIME_MESSAGE_PREFIX = "Current UTC time: "


class CurrentTimeContextLayer(ContextLayer):
    """Producer-слой: добавляет текущее UTC-время отдельным system-сообщением.

    now инъецируем для тестов; в runtime — datetime.now(UTC).
    """

    def __init__(self, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or (lambda: datetime.now(UTC))

    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        text = f"{TIME_MESSAGE_PREFIX}{self._now().isoformat()}"
        return [
            *context,
            Message(role=Role.SYSTEM, content=[TextBlock(text=text)]),
        ]


class CurrentTimePlugin(Plugin):
    def register(self, registry: PluginRegistry) -> None:
        registry.register_context_layer(CurrentTimeContextLayer())

    async def on_startup(self) -> None:
        return None

    async def on_shutdown(self) -> None:
        return None
