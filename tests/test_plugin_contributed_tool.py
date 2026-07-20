"""Acceptance: плагин вносит Tool в runtime без изменения ядра.

Инвариант Phase 2: новая возможность = Plugin в composition root.
Agent / ConversationEngine / ToolManager не правятся под конкретный плагин.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from os import environ

import pytest_asyncio
from dependency_injector import providers

from app.config.settings import get_settings
from app.container import Container
from app.core.execution_context import ExecutionContext
from app.models.message import TextBlock, ToolCall
from app.plugins.echo_plugin import EchoPlugin, EchoTool
from app.tools.simple_tool_manager import SimpleToolManager


@pytest_asyncio.fixture
async def container() -> AsyncGenerator[Container, None]:
    environ["OPENAI_API_KEY"] = "test-key"
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    get_settings.cache_clear()

    c = Container()
    init_result = c.init_resources()
    if init_result is not None:
        await init_result

    yield c

    shutdown_result = c.shutdown_resources()
    if shutdown_result is not None:
        await shutdown_result

    get_settings.cache_clear()


async def test_echo_plugin_registers_tool_in_registry(container: Container) -> None:
    registry = container.plugin_registry()
    names = [tool.definition.name for tool in registry.all_registered_tools()]

    assert "echo" in names
    assert any(isinstance(tool, EchoTool) for tool in registry.all_registered_tools())


async def test_plugin_contributed_tool_appears_in_tool_manager(
    container: Container,
) -> None:
    manager = await container.tool_manager()  # type: ignore[misc]
    assert isinstance(manager, SimpleToolManager)

    names = {definition.name for definition in manager.tool_definitions()}
    assert "echo" in names
    # Ядровые tools по-прежнему на месте.
    assert "remember" in names
    assert "search_knowledge" in names


async def test_plugin_contributed_tool_is_executable(container: Container) -> None:
    manager = await container.tool_manager()  # type: ignore[misc]

    result = await manager.execute(
        ToolCall(id="call_echo_1", tool_name="echo", arguments={"text": "ping"}),
        ExecutionContext(conversation_id="conv"),
    )

    assert result.is_error is False
    assert result.tool_call_id == "call_echo_1"
    assert isinstance(result.content[0], TextBlock)
    assert result.content[0].text == "ping"


async def test_without_plugins_echo_is_absent() -> None:
    # Контроль: echo появляется только через Plugin, не зашит в ToolManager.
    environ["OPENAI_API_KEY"] = "test-key"
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    get_settings.cache_clear()

    container = Container()
    try:
        with container.plugins.override(providers.Object([])):
            init_result = container.init_resources()
            if init_result is not None:
                await init_result

            registry = container.plugin_registry()
            assert registry.all_registered_tools() == []

            manager = await container.tool_manager()  # type: ignore[misc]
            names = {definition.name for definition in manager.tool_definitions()}
            assert "echo" not in names
            assert "remember" in names

            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result
    finally:
        get_settings.cache_clear()


async def test_echo_plugin_register_is_pure() -> None:
    # Плагин сам по себе только пишет в registry — без DI и без ядра.
    from app.plugins.registry import SimplePluginRegistry

    registry = SimplePluginRegistry()
    EchoPlugin().register(registry)

    assert [tool.definition.name for tool in registry.all_registered_tools()] == ["echo"]
