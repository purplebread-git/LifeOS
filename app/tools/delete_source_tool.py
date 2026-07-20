from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class DeleteSourceTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delete_source",
            description="Delete all knowledge chunks belonging to a given source",
            input_schema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                    },
                },
                "required": ["source"],
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        if context.knowledge is None:
            raise ValueError("Knowledge provider is not configured")

        source = arguments["source"]

        deleted = await context.knowledge.delete_source(source)

        return ToolResult(
            content=[
                TextBlock(
                    text=f"Deleted {deleted} chunk(s) from '{source}'",
                ),
            ],
        )
