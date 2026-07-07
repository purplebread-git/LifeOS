"""SimplePluginManager — конкретная реализация PluginManager."""

from __future__ import annotations

from app.core.plugin import Plugin
from app.core.plugin_manager import PluginManager
from app.core.plugin_registry import PluginRegistry


class SimplePluginManager(PluginManager):
    def __init__(
        self,
        plugins: list[Plugin],
        registry: PluginRegistry,
    ) -> None:
        self._plugins = plugins
        self._registry = registry
        self._started = False

    async def start(self) -> None:
        """Регистрация и запуск всех плагинов.

        Метод идемпотентный: повторный вызов не запускает плагины второй раз.
        """
        if self._started:
            return

        for plugin in self._plugins:
            plugin.register(self._registry)

        for plugin in self._plugins:
            await plugin.on_startup()

        self._started = True

    async def stop(self) -> None:
        """Остановка плагинов в обратном порядке."""
        if not self._started:
            return

        for plugin in reversed(self._plugins):
            await plugin.on_shutdown()

        self._started = False