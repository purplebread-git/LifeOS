"""OpenAIProvider — реализация core.LLMProvider поверх OpenAIClient.

Вся логика конвертации вынесена в mapper.py — этот класс только
оркестрирует: маппинг запроса → вызов клиента → маппинг ответа.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.llm_provider import LLMProvider
from app.models.message import LLMResponse, Message
from app.models.tool import ToolDefinition
from app.providers.openai import mapper
from app.providers.openai.openai_client import OpenAIClient


class OpenAIProvider(LLMProvider):
    def __init__(self, client: OpenAIClient, model: str) -> None:
        self._client = client
        self._model = model

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        openai_messages = [mapper.message_to_openai(message) for message in messages]
        openai_tools = [mapper.tool_definition_to_openai(tool) for tool in tools] if tools else None

        completion = await self._client.chat(
            model=self._model,
            messages=openai_messages,
            tools=openai_tools,
        )

        return mapper.completion_to_llm_response(completion)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        if tools is not None:
            raise NotImplementedError("Streaming with tools is not supported yet")

        openai_messages = [mapper.message_to_openai(message) for message in messages]
        async for delta in self._client.chat_stream(
            model=self._model,
            messages=openai_messages,
        ):
            yield delta
