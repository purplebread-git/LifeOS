from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.knowledge import KnowledgeChunk
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class SearchKnowledgeTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_knowledge",
            description="Search the knowledge base for relevant information",
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
        if context.knowledge is None:
            raise ValueError("Knowledge provider is not configured")

        query = arguments["query"]

        chunks = await context.knowledge.search(query)

        result = "No knowledge found" if not chunks else _format_chunks(chunks)

        return ToolResult(
            tool_call_id="search_knowledge",
            content=[
                TextBlock(
                    text=result,
                ),
            ],
        )


def _format_chunks(chunks: list[KnowledgeChunk]) -> str:
    # Блочный формат (Source + content), расширяемый под будущие поля
    # (section / page / chunk_index / relevance) без слома структуры.
    return "\n\n".join(f"Source: {chunk.source}\n{chunk.content}" for chunk in chunks)
