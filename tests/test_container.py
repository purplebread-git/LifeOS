import pytest_asyncio

from app.container import Container
from app.core.agent import Agent
from app.core.plugin_registry import PluginRegistry
from app.models import AgentResponse


@pytest_asyncio.fixture
async def container() -> Container:
    c = Container()

    await c.init_resources()

    yield c

    await c.shutdown_resources()


async def test_container_resolves_agent(
    container: Container,
) -> None:
    agent = container.agent()

    assert isinstance(agent, Agent)


async def test_agent_respond_end_to_end(
    container: Container,
) -> None:
    agent = container.agent()

    response = await agent.respond(
        conversation_id="conv-1",
        user_input="Привет",
    )

    assert isinstance(response, AgentResponse)
    assert response.conversation_id == "conv-1"
    assert len(response.messages) == 1


async def test_plugin_lifecycle_resolves_even_without_plugins(
    container: Container,
) -> None:
    manager = container.plugin_manager()
    registry = container.plugin_registry()

    assert manager is not None
    assert isinstance(registry, PluginRegistry)
    assert registry.all_registered_tools() == []


async def test_null_llm_returns_content_blocks(
    container: Container,
) -> None:
    llm = container.llm_provider()

    response = await llm.generate([])

    assert response.message.content[0].type == "text"