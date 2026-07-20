from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class ListSourcesTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_sources",
            description="List all sources currently stored in the knowledge base",
            input_schema={
                "type": "object",
                "properties": {},
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        if context.knowledge is None:
            raise ValueError("Knowledge provider is not configured")

        sources = await context.knowledge.list_sources()

        result = "No sources" if not sources else "\n".join(f"- {source}" for source in sources)

        return ToolResult(
            content=[
                TextBlock(
                    text=result,
                ),
            ],
        )
