"""Модели описания и результата выполнения инструментов."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.message import ContentBlock


class ToolDefinition(BaseModel):
    """input_schema — JSON Schema (json-schema.org): открытый стандарт,
    используемый OpenAI, Claude, Gemini и протоколом MCP независимо друг
    от друга. Это не заимствование терминологии у конкретного вендора."""

    name: str
    description: str
    input_schema: dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    content: list[ContentBlock]
    is_error: bool = False
