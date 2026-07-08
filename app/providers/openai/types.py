"""Типы, максимально близкие к формату OpenAI Chat Completions API.

TypedDict вместо dict[str, Any] — чтобы IDE и mypy понимали форму данных,
которую ожидает и возвращает OpenAIClient.
"""
from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class OpenAIMessage(TypedDict):
    role: str
    content: str
    tool_call_id: NotRequired[str]


class OpenAIFunctionDef(TypedDict):
    name: str
    description: str
    parameters: dict[str, Any]


class OpenAIToolDef(TypedDict):
    type: Literal["function"]
    function: OpenAIFunctionDef