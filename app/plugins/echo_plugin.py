"""EchoPlugin — первый реальный плагин: вносит Tool без изменения ядра.

Плагин живёт целиком здесь (Tool + Plugin). Composition root только
добавляет экземпляр в `plugins`; Agent / ConversationEngine / ToolManager
не знают про Echo.
"""

from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.plugin import Plugin
from app.core.plugin_registry import PluginRegistry
from app.core.tool import Tool
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class EchoTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="echo",
            description="Echo back the provided text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                    },
                },
                "required": ["text"],
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        return ToolResult(
            content=[
                TextBlock(text=str(arguments["text"])),
            ],
        )


class EchoPlugin(Plugin):
    def register(self, registry: PluginRegistry) -> None:
        registry.register_tool(EchoTool())

    async def on_startup(self) -> None:
        return None

    async def on_shutdown(self) -> None:
        return None
