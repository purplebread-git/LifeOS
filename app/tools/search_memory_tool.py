from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class SearchMemoryTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_memory",
            description="Search stored memories",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                },
                "required": ["query"],
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        if context.memory is None:
            raise ValueError("Memory provider is not configured")

        query = arguments["query"]

        memories = await context.memory.search(query)

        if not memories:
            result = "No memories found"
        else:
            result = "\n".join(
                f"{index + 1}. {memory.content}" for index, memory in enumerate(memories)
            )

        return ToolResult(
            content=[
                TextBlock(
                    text=result,
                ),
            ],
        )
