"""Acceptance: плагин вносит ContextLayer без изменения ядра.

Вторая ось расширения Phase 2: Plugin → ContextLayer (рядом с Plugin → Tool).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from os import environ

import pytest_asyncio
from dependency_injector import providers

from app.config.settings import get_settings
from app.container import Container
from app.context import LayeredContextBuilder
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock
from app.plugins.current_time_plugin import (
    TIME_MESSAGE_PREFIX,
    CurrentTimeContextLayer,
    CurrentTimePlugin,
)
from app.plugins.registry import SimplePluginRegistry


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


async def test_current_time_layer_injects_frozen_clock() -> None:
    fixed = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    layer = CurrentTimeContextLayer(now=lambda: fixed)
    conversation = Conversation(conversation_id="c1")

    context = await layer.apply(conversation, [])

    assert len(context) == 1
    assert context[0].role == Role.SYSTEM
    assert isinstance(context[0].content[0], TextBlock)
    assert context[0].content[0].text == f"{TIME_MESSAGE_PREFIX}{fixed.isoformat()}"


async def test_current_time_plugin_registers_layer() -> None:
    registry = SimplePluginRegistry()
    CurrentTimePlugin().register(registry)

    layers = registry.all_registered_context_layers()
    assert len(layers) == 1
    assert isinstance(layers[0], CurrentTimeContextLayer)


async def test_plugin_contributed_layer_appears_in_context_builder(
    container: Container,
) -> None:
    registry = container.plugin_registry()
    assert any(
        isinstance(layer, CurrentTimeContextLayer)
        for layer in registry.all_registered_context_layers()
    )

    builder = await container.context_builder()  # type: ignore[misc]
    assert isinstance(builder, LayeredContextBuilder)

    conversation = Conversation(
        conversation_id="c1",
        messages=[Message(role=Role.USER, content=[TextBlock(text="hi")])],
    )
    context = await builder.build(conversation)

    time_messages = [
        message
        for message in context
        if message.role == Role.SYSTEM
        and message.content
        and isinstance(message.content[0], TextBlock)
        and message.content[0].text.startswith(TIME_MESSAGE_PREFIX)
    ]
    assert len(time_messages) == 1


async def test_without_plugins_time_layer_is_absent() -> None:
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
            assert registry.all_registered_context_layers() == []
            assert registry.all_registered_tools() == []

            builder = await container.context_builder()  # type: ignore[misc]
            conversation = Conversation(
                conversation_id="c1",
                messages=[Message(role=Role.USER, content=[TextBlock(text="hi")])],
            )
            context = await builder.build(conversation)

            assert not any(
                message.role == Role.SYSTEM
                and message.content
                and isinstance(message.content[0], TextBlock)
                and message.content[0].text.startswith(TIME_MESSAGE_PREFIX)
                for message in context
            )

            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result
    finally:
        get_settings.cache_clear()
