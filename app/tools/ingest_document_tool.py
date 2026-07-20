from __future__ import annotations

from typing import Any

from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.message import TextBlock
from app.models.tool import ToolDefinition, ToolResult


class IngestDocumentTool(Tool):
    """Даёт агенту доступ к capability ingestion.

    Tool → DocumentIngestionService → KnowledgeProvider. Инструмент не знает
    про extractor, chunker или add_batch — только открывает возможность.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="ingest_document",
            description="Ingest a text document into the knowledge base",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                    },
                    "source": {
                        "type": "string",
                    },
                },
                "required": ["content", "source"],
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        if context.ingestion is None:
            raise ValueError("Ingestion service is not configured")

        content = arguments["content"]
        source = arguments["source"]

        chunks = await context.ingestion.ingest(content.encode("utf-8"), source=source)

        return ToolResult(
            content=[
                TextBlock(
                    text=f"Ingested {len(chunks)} chunk(s) from '{source}'",
                ),
            ],
        )
