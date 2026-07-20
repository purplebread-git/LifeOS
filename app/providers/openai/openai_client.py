"""OpenAIClient — тонкая обёртка над официальным OpenAI SDK.

Единственная ответственность: создать AsyncOpenAI, выполнить один chat
completion запрос, перевести сетевые ошибки SDK в исключения ядра
(app.core.exceptions). Ничего не знает про Message, ToolDefinition,
Conversation — форматом OpenAI-совместимых типов управляет только types.py
и mapper.py.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletion

from app.core.exceptions import (
    EmbeddingError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.providers.openai.types import OpenAIMessage, OpenAIToolDef


def _rate_limit_message(exc: object) -> str:
    """RateLimitError у OpenAI покрывает и RPM, и insufficient_quota."""
    body = str(exc)
    code = getattr(exc, "code", None)
    if code == "insufficient_quota" or "insufficient_quota" in body:
        return (
            "OpenAI quota exceeded — check billing/credits at "
            "https://platform.openai.com/settings/organization/billing"
        )
    return "OpenAI rate limit exceeded — wait a moment and try again"


class OpenAIClient:
    def __init__(self, api_key: str, timeout: float = 60.0) -> None:
        self._timeout = timeout
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)

    async def chat(
        self,
        model: str,
        messages: list[OpenAIMessage],
        tools: list[OpenAIToolDef] | None = None,
    ) -> ChatCompletion:
        try:
            if tools:
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=cast(Any, messages),
                    tools=cast(Any, tools),
                )
            else:
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=cast(Any, messages),
                )

            return response

        except APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI request timed out after {self._timeout}s") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(_rate_limit_message(exc)) from exc
        except APIConnectionError as exc:
            raise LLMConnectionError("Failed to connect to OpenAI API") from exc
        except APIStatusError as exc:
            raise LLMError(
                f"OpenAI API returned an error (status {exc.status_code}): {exc.message}"
            ) from exc

    async def chat_stream(
        self,
        model: str,
        messages: list[OpenAIMessage],
    ) -> AsyncIterator[str]:
        """Поток текстовых дельт chat completion (stream=True, без tools)."""
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=cast(Any, messages),
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        except APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI request timed out after {self._timeout}s") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(_rate_limit_message(exc)) from exc
        except APIConnectionError as exc:
            raise LLMConnectionError("Failed to connect to OpenAI API") from exc
        except APIStatusError as exc:
            raise LLMError(
                f"OpenAI API returned an error (status {exc.status_code}): {exc.message}"
            ) from exc

    async def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        """Сгенерировать эмбеддинги для батча текстов.

        Ошибки SDK транслируются в EmbeddingError (а не LLMError): память
        деградирует по этому исключению отдельно от LLM-слоя."""
        try:
            response = await self._client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except (
            APITimeoutError,
            RateLimitError,
            APIConnectionError,
            APIStatusError,
        ) as exc:
            raise EmbeddingError(f"OpenAI embeddings request failed: {exc}") from exc
