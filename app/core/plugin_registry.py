from abc import ABC, abstractmethod

from app.core.tool import Tool


class PluginRegistry(ABC):
    """Собирает регистрации плагинов при старте (write-side).

    all_registered_tools() предназначен ИСКЛЮЧИТЕЛЬНО для composition root
    при построении ToolManager. Agent/ConversationEngine никогда не
    обращаются к PluginRegistry напрямую в рантайме."""

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        raise NotImplementedError

    @abstractmethod
    def all_registered_tools(self) -> list[Tool]:
        raise NotImplementedError
