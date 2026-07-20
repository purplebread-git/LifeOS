from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.context_builder import ContextBuilder
from app.core.conversation_engine import ConversationEngine
from app.core.execution_context import ExecutionContext
from app.core.knowledge_provider import KnowledgeProvider
from app.core.llm_provider import LLMProvider
from app.core.memory_provider import MemoryProvider
from app.core.tool_manager import ToolManager
from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock
from app.models.tool import ToolResult

MAX_TOOL_ITERATIONS = 5


class ToolConversationEngine(ConversationEngine):
    def __init__(
        self,
        llm_provider: LLMProvider,
        context_builder: ContextBuilder,
        tool_manager: ToolManager,
        memory_provider: MemoryProvider | None = None,
        knowledge_provider: KnowledgeProvider | None = None,
        ingestion_service: DocumentIngestionService | None = None,
    ) -> None:
        self._llm_provider = llm_provider
        self._context_builder = context_builder
        self._tool_manager = tool_manager
        self._memory_provider = memory_provider
        self._knowledge_provider = knowledge_provider
        self._ingestion_service = ingestion_service

    async def run_turn(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> Message:
        conversation.messages.append(user_message)

        for _ in range(MAX_TOOL_ITERATIONS):
            context = await self._context_builder.build(conversation)

            response = await self._llm_provider.generate(
                context,
                tools=self._tool_manager.tool_definitions(),
            )

            assistant_message = response.message
            conversation.messages.append(assistant_message)

            if not assistant_message.tool_calls:
                return assistant_message

            execution_context = ExecutionContext(
                conversation_id=conversation.conversation_id,
                memory=self._memory_provider,
                knowledge=self._knowledge_provider,
                ingestion=self._ingestion_service,
            )

            for tool_call in assistant_message.tool_calls:
                result = await self._tool_manager.execute(
                    tool_call,
                    execution_context,
                )

                conversation.messages.append(
                    self._tool_result_to_message(result),
                )

        return conversation.messages[-1]

    async def stream_turn(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> AsyncIterator[str]:
        """Текстовый stream без tool loop. Streaming tool calls — отдельный PR."""
        conversation.messages.append(user_message)

        context = await self._context_builder.build(conversation)
        parts: list[str] = []
        async for token in self._llm_provider.stream(context):
            parts.append(token)
            yield token

        assistant_message = Message(
            role=Role.ASSISTANT,
            content=[TextBlock(text="".join(parts))],
        )
        conversation.messages.append(assistant_message)

    @staticmethod
    def _tool_result_to_message(result: ToolResult) -> Message:
        return Message(
            role=Role.TOOL,
            content=result.content,
            tool_call_id=result.tool_call_id,
        )
