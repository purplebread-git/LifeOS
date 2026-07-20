"""SSE chat transport — только текст поверх Agent.stream_respond."""

from __future__ import annotations

from collections.abc import AsyncIterator
from os import environ

from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.api.chat import format_sse_data
from app.config.settings import get_settings
from app.core.agent import Agent
from app.main import create_app
from app.models.conversation import AgentResponse
from app.models.message import Message, Role, TextBlock


def test_format_sse_data_single_line() -> None:
    assert format_sse_data("hello") == "data: hello\n\n"


def test_format_sse_data_multiline() -> None:
    assert format_sse_data("a\nb") == "data: a\ndata: b\n\n"


class _FakeStreamingAgent(Agent):
    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        return AgentResponse(
            conversation_id=conversation_id,
            messages=[
                Message(role=Role.ASSISTANT, content=[TextBlock(text="unused")]),
            ],
        )

    async def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]:
        assert conversation_id == "conv-1"
        assert user_input == "hi"
        yield "Hel"
        yield "lo"


async def test_chat_stream_endpoint_returns_sse_text() -> None:
    environ["OPENAI_API_KEY"] = "test-key"
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    get_settings.cache_clear()

    app = create_app()
    fake = _FakeStreamingAgent()
    with app.state.container.agent.override(providers.Object(fake)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/chat/stream",
                json={"conversation_id": "conv-1", "message": "hi"},
            )

    get_settings.cache_clear()

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "data: Hel\n\n" in body
    assert "data: lo\n\n" in body
    assert "data: [DONE]\n\n" in body
