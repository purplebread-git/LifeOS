"""Доказательство: PluginManager встроен в runtime (Container Resource + lifespan).

Не про возможности плагинов — про то, что жизненный цикл приложения
реально проходит через менеджер: start → register/on_startup, stop → on_shutdown.
"""

from __future__ import annotations

from os import environ

from dependency_injector import providers

from app.config.settings import get_settings
from app.container import Container
from app.core.plugin import Plugin
from app.core.plugin_registry import PluginRegistry
from app.plugins.manager import SimplePluginManager
from app.plugins.registry import SimplePluginRegistry


class FakePlugin(Plugin):
    """Минимальный плагин: только фиксирует вызовы lifecycle."""

    def __init__(self) -> None:
        self.register_calls = 0
        self.startup_calls = 0
        self.shutdown_calls = 0
        self.events: list[str] = []

    def register(self, registry: PluginRegistry) -> None:
        self.register_calls += 1
        self.events.append("register")

    async def on_startup(self) -> None:
        self.startup_calls += 1
        self.events.append("startup")

    async def on_shutdown(self) -> None:
        self.shutdown_calls += 1
        self.events.append("shutdown")


async def test_simple_plugin_manager_invokes_lifecycle() -> None:
    plugin = FakePlugin()
    manager = SimplePluginManager(plugins=[plugin], registry=SimplePluginRegistry())

    await manager.start()
    assert plugin.events == ["register", "startup"]

    await manager.stop()
    assert plugin.events == ["register", "startup", "shutdown"]


async def test_simple_plugin_manager_start_is_idempotent() -> None:
    plugin = FakePlugin()
    manager = SimplePluginManager(plugins=[plugin], registry=SimplePluginRegistry())

    await manager.start()
    await manager.start()

    assert plugin.register_calls == 1
    assert plugin.startup_calls == 1


async def test_container_resource_runs_plugin_lifecycle() -> None:
    # Acceptance: init_resources / shutdown_resources (то же, что FastAPI lifespan)
    # реально прогоняют плагин через PluginManager. Пустой список плагинов
    # уже работал; FakePlugin доказывает, что каркас не no-op.
    environ["OPENAI_API_KEY"] = "test-key"
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    get_settings.cache_clear()

    plugin = FakePlugin()
    container = Container()

    try:
        with container.plugins.override(providers.Object([plugin])):
            init_result = container.init_resources()
            if init_result is not None:
                await init_result

            assert plugin.events == ["register", "startup"]

            manager = await container.plugin_manager()  # type: ignore[misc]
            assert isinstance(manager, SimplePluginManager)

            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result

            assert plugin.events == ["register", "startup", "shutdown"]
            assert plugin.startup_calls == 1
            assert plugin.shutdown_calls == 1
    finally:
        get_settings.cache_clear()
