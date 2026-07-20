from collections.abc import AsyncIterator
from typing import cast

from app.agent import SimpleAgent, SimpleContextBuilder, SimpleConversationEngine
from app.conversation.in_memory_repository import InMemoryConversationRepository
from app.core.llm_provider import LLMProvider
from app.models.message import LLMResponse, Message, Role, TextBlock
from app.models.tool import ToolDefinition


class _RecordingLLMProvider(LLMProvider):
    """Фейковый LLMProvider для проверки того, сколько сообщений истории
    видит движок на каждом шаге — без реальных сетевых вызовов."""

    def __init__(self) -> None:
        self.received_message_counts: list[int] = []

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        self.received_message_counts.append(len(messages))
        reply_index = len(self.received_message_counts)
        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[TextBlock(text=f"Ответ #{reply_index}")],
            ),
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        response = await self.generate(messages, tools)
        block = response.message.content[0]
        assert isinstance(block, TextBlock)
        yield block.text


def _build_agent() -> tuple[SimpleAgent, _RecordingLLMProvider, InMemoryConversationRepository]:
    llm_provider = _RecordingLLMProvider()
    context_builder = SimpleContextBuilder()
    engine = SimpleConversationEngine(llm_provider=llm_provider, context_builder=context_builder)
    repository = InMemoryConversationRepository()
    agent = SimpleAgent(conversation_engine=engine, conversation_repository=repository)
    return agent, llm_provider, repository


async def test_conversation_history_accumulates_across_calls() -> None:
    agent, llm_provider, repository = _build_agent()

    first = await agent.respond(conversation_id="conv-1", user_input="Привет")
    second = await agent.respond(conversation_id="conv-1", user_input="Как дела?")

    # Первый вызов: движок видит только сообщение пользователя (1).
    # Второй вызов: видит всю историю первого шага + новое сообщение (3).
    assert llm_provider.received_message_counts == [1, 3]

    first_block = cast(TextBlock, first.messages[0].content[0])
    second_block = cast(TextBlock, second.messages[0].content[0])

    assert first_block.text == "Ответ #1"
    assert second_block.text == "Ответ #2"

    conversation = await repository.load("conv-1")
    assert len(conversation.messages) == 4  # user, assistant, user, assistant


async def test_stream_respond_saves_conversation() -> None:
    agent, llm_provider, repository = _build_agent()

    tokens: list[str] = []
    async for token in agent.stream_respond(conversation_id="conv-stream", user_input="Привет"):
        tokens.append(token)

    assert tokens == ["Ответ #1"]
    conversation = await repository.load("conv-stream")
    assert len(conversation.messages) == 2
    assert conversation.messages[0].role == Role.USER
    assert conversation.messages[1].role == Role.ASSISTANT
    assert llm_provider.received_message_counts == [1]


async def test_different_conversation_ids_are_isolated() -> None:
    agent, llm_provider, _ = _build_agent()

    await agent.respond(conversation_id="conv-a", user_input="Привет")
    await agent.respond(conversation_id="conv-b", user_input="Другой разговор")

    # Оба вызова видят только по одному сообщению — истории не пересекаются.
    assert llm_provider.received_message_counts == [1, 1]
