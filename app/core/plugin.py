from abc import ABC, abstractmethod

from app.core.plugin_registry import PluginRegistry


class Plugin(ABC):
    @abstractmethod
    def register(self, registry: PluginRegistry) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_startup(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_shutdown(self) -> None:
        raise NotImplementedError