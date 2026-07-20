"""Chat HTTP API — транспорт к ConversationEngine.

SSE отдаёт только текст (data: …). Без WebSocket, heartbeat, tool events.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.container import Container
from app.core.agent import Agent

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatStreamRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


def format_sse_data(text: str) -> str:
    """Одна SSE-запись: только текстовый payload, без event types."""
    lines = text.split("\n")
    return "".join(f"data: {line}\n" for line in lines) + "\n"


async def _resolve_agent(request: Request) -> Agent:
    container: Container = request.app.state.container
    agent = container.agent()
    if hasattr(agent, "__await__"):
        agent = await agent
    assert isinstance(agent, Agent)
    return agent


@router.post("/chat/stream")
async def chat_stream(body: ChatStreamRequest, request: Request) -> StreamingResponse:
    agent = await _resolve_agent(request)

    async def events() -> AsyncIterator[bytes]:
        async for token in agent.stream_respond(body.conversation_id, body.message):
            yield format_sse_data(token).encode("utf-8")
        yield b"data: [DONE]\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
