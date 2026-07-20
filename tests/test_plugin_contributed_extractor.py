"""Acceptance: плагин вносит DocumentExtractor без изменения ядра.

Третья ось Phase 2: Plugin → DocumentExtractor (рядом с Tool и ContextLayer).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from os import environ

import pytest_asyncio
from dependency_injector import providers

from app.config.settings import get_settings
from app.container import Container
from app.core.document_extractor import DocumentExtractor
from app.knowledge.extractor_registry import ExtractorRegistry
from app.knowledge.plain_text_extractor import PlainTextExtractor
from app.plugins.registry import SimplePluginRegistry
from app.plugins.uppercase_text_plugin import (
    UPPERCASE_EXTENSION,
    UppercaseTextExtractor,
    UppercaseTextPlugin,
)


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


async def test_uppercase_extractor_policy() -> None:
    extractor = UppercaseTextExtractor()
    assert await extractor.extract(b"hello world") == "HELLO WORLD"


async def test_uppercase_plugin_registers_extractor() -> None:
    registry = SimplePluginRegistry()
    UppercaseTextPlugin().register(registry)

    extractors = registry.all_registered_document_extractors()
    assert UPPERCASE_EXTENSION in extractors
    assert isinstance(extractors[UPPERCASE_EXTENSION], UppercaseTextExtractor)


async def test_plugin_contributed_extractor_appears_in_registry(
    container: Container,
) -> None:
    plugin_registry = container.plugin_registry()
    assert UPPERCASE_EXTENSION in plugin_registry.all_registered_document_extractors()

    extractor_registry = await container.extractor_registry()  # type: ignore[misc]
    assert isinstance(extractor_registry, ExtractorRegistry)

    resolved = extractor_registry.resolve("notes.upper")
    assert isinstance(resolved, UppercaseTextExtractor)
    assert await resolved.extract(b"LifeOS") == "LIFEOS"

    # Ядровые форматы на месте.
    assert not isinstance(extractor_registry.resolve("readme.md"), UppercaseTextExtractor)


async def test_plugin_extractor_flows_through_ingestion(container: Container) -> None:
    service = await container.document_ingestion_service()  # type: ignore[misc]
    chunks = await service.ingest(b"hello plugin", source="demo.upper")

    assert chunks
    assert all(chunk.content == chunk.content.upper() for chunk in chunks)
    assert all("HELLO" in chunk.content for chunk in chunks)


async def test_without_plugins_uppercase_falls_to_default() -> None:
    environ["OPENAI_API_KEY"] = "test-key"
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    get_settings.cache_clear()

    container = Container()
    try:
        with container.plugins.override(providers.Object([])):
            init_result = container.init_resources()
            if init_result is not None:
                await init_result

            assert container.plugin_registry().all_registered_document_extractors() == {}

            extractor_registry = await container.extractor_registry()  # type: ignore[misc]
            resolved = extractor_registry.resolve("notes.upper")
            assert isinstance(resolved, PlainTextExtractor)
            assert isinstance(resolved, DocumentExtractor)
            assert await resolved.extract(b"hello") == "hello"

            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result
    finally:
        get_settings.cache_clear()


async def test_existing_plugins_unchanged_by_third_axis(container: Container) -> None:
    # Аддитивность: Echo / CurrentTime не трогали при появлении extractor-оси.
    registry = container.plugin_registry()
    tool_names = [tool.definition.name for tool in registry.all_registered_tools()]
    assert "echo" in tool_names
    assert registry.all_registered_context_layers()
    assert UPPERCASE_EXTENSION in registry.all_registered_document_extractors()
