from app.context.conversation_history_layer import ConversationHistoryLayer
from app.context.knowledge_context_layer import KnowledgeContextLayer
from app.context.layered_context_builder import LayeredContextBuilder
from app.context.system_prompt_layer import SystemPromptLayer
from app.core.context_layer import ContextLayer
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock


def _conversation() -> Conversation:
    return Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="hello")]),
            Message(role=Role.ASSISTANT, content=[TextBlock(text="hi")]),
        ],
    )


async def test_layers_apply_in_order() -> None:
    builder = LayeredContextBuilder(
        layers=[
            SystemPromptLayer(system_prompt="persona"),
            ConversationHistoryLayer(),
        ]
    )

    result = await builder.build(_conversation())

    assert [m.role for m in result] == [Role.SYSTEM, Role.USER, Role.ASSISTANT]
    assert result[0].content[0].text == "persona"  # type: ignore[union-attr]


async def test_empty_system_prompt_contributes_nothing() -> None:
    builder = LayeredContextBuilder(
        layers=[
            SystemPromptLayer(system_prompt="   "),
            ConversationHistoryLayer(),
        ]
    )

    result = await builder.build(_conversation())

    assert [m.role for m in result] == [Role.USER, Role.ASSISTANT]


async def test_knowledge_layer_is_passthrough() -> None:
    builder = LayeredContextBuilder(
        layers=[
            ConversationHistoryLayer(),
            KnowledgeContextLayer(),
        ]
    )

    result = await builder.build(_conversation())

    assert [m.role for m in result] == [Role.USER, Role.ASSISTANT]


async def test_build_does_not_mutate_conversation() -> None:
    conversation = _conversation()
    builder = LayeredContextBuilder(
        layers=[
            SystemPromptLayer(system_prompt="persona"),
            ConversationHistoryLayer(),
        ]
    )

    await builder.build(conversation)

    assert len(conversation.messages) == 2


async def test_no_layers_returns_empty_context() -> None:
    builder = LayeredContextBuilder(layers=[])

    result = await builder.build(_conversation())

    assert result == []


class _TruncateToLastLayer(ContextLayer):
    """Пример слоя-трансформера (как будущий Token Budget): получает
    накопленный контекст и возвращает изменённый — доказывает, что
    pipeline-контракт это позволяет, а не только producer-семантику."""

    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        return context[-1:]


async def test_transformer_layer_can_rewrite_context() -> None:
    builder = LayeredContextBuilder(
        layers=[
            SystemPromptLayer(system_prompt="persona"),
            ConversationHistoryLayer(),
            _TruncateToLastLayer(),
        ]
    )

    result = await builder.build(_conversation())

    assert len(result) == 1
    assert result[0].role == Role.ASSISTANT
