from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.memory import MemoryEntry
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class RememberTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="remember",
            description="Store important information in memory",
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
        if context.memory is None:
            raise ValueError("Memory provider is not configured")

        text = arguments["text"]

        await context.memory.add(
            MemoryEntry(
                id=str(uuid4()),
                content=text,
            )
        )

        return ToolResult(
            content=[
                TextBlock(
                    text="Memory stored",
                ),
            ],
        )
