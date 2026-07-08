"""OpenAIClient — тонкая обёртка над официальным OpenAI SDK.

Единственная ответственность: создать AsyncOpenAI, выполнить один chat
completion запрос, перевести сетевые ошибки SDK в исключения ядра
(app.core.exceptions). Ничего не знает про Message, ToolDefinition,
Conversation — форматом OpenAI-совместимых типов управляет только types.py
и mapper.py.
"""

from __future__ import annotations

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
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.providers.openai.types import OpenAIMessage, OpenAIToolDef


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
            raise LLMTimeoutError(
                f"OpenAI request timed out after {self._timeout}s"
            ) from exc
        except RateLimitError as exc:
            raise LLMRateLimitError("OpenAI rate limit exceeded") from exc
        except APIConnectionError as exc:
            raise LLMConnectionError("Failed to connect to OpenAI API") from exc
        except APIStatusError as exc:
            raise LLMError(
                f"OpenAI API returned an error (status {exc.status_code}): {exc.message}"
            ) from exc