from abc import ABC, abstractmethod

from app.core.context_layer import ContextLayer
from app.core.tool import Tool


class PluginRegistry(ABC):
    """Собирает регистрации плагинов при старте (write-side).

    all_registered_*() предназначены ИСКЛЮЧИТЕЛЬНО для composition root
    при сборке ToolManager / ContextBuilder. Agent/ConversationEngine никогда
    не обращаются к PluginRegistry напрямую в рантайме.
    """

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        raise NotImplementedError

    @abstractmethod
    def all_registered_tools(self) -> list[Tool]:
        raise NotImplementedError

    @abstractmethod
    def register_context_layer(self, layer: ContextLayer) -> None:
        raise NotImplementedError

    @abstractmethod
    def all_registered_context_layers(self) -> list[ContextLayer]:
        raise NotImplementedError
