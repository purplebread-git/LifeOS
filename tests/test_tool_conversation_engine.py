from typing import Any

from app.agent import SimpleContextBuilder
from app.agent.tool_conversation_engine import (
    MAX_TOOL_ITERATIONS,
    ToolConversationEngine,
)
from app.core.execution_context import ExecutionContext
from app.core.llm_provider import LLMProvider
from app.core.tool import Tool
from app.models.conversation import Conversation
from app.models.message import (
    LLMResponse,
    Message,
    Role,
    TextBlock,
    ToolCall,
)
from app.models.tool import ToolDefinition, ToolResult
from app.tools.simple_tool_manager import SimpleToolManager


class EchoTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="echo",
            description="echo",
            input_schema={},
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        return ToolResult(
            content=[
                TextBlock(
                    text=arguments["text"],
                ),
            ],
        )


class ToolCallingLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        self.calls += 1

        if self.calls == 1:
            return LLMResponse(
                message=Message(
                    role=Role.ASSISTANT,
                    content=[],
                    tool_calls=[
                        ToolCall(
                            id="call-1",
                            tool_name="echo",
                            arguments={"text": "hello"},
                        )
                    ],
                ),
                finish_reason="tool_calls",
            )

        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[
                    TextBlock(text="done"),
                ],
            ),
            finish_reason="stop",
        )


class SimpleLLMProvider(LLMProvider):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[
                    TextBlock(text="done"),
                ],
            ),
            finish_reason="stop",
        )


class InfiniteToolLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        self.calls += 1

        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[],
                tool_calls=[
                    ToolCall(
                        id=f"call-{self.calls}",
                        tool_name="echo",
                        arguments={"text": "hello"},
                    )
                ],
            ),
            finish_reason="tool_calls",
        )


async def test_tool_execution_loop() -> None:
    provider = ToolCallingLLMProvider()

    engine = ToolConversationEngine(
        llm_provider=provider,
        context_builder=SimpleContextBuilder(),
        tool_manager=SimpleToolManager(
            tools=[EchoTool()],
        ),
    )

    conversation = Conversation(
        conversation_id="conv-1",
    )

    result = await engine.run_turn(
        conversation,
        Message(
            role=Role.USER,
            content=[TextBlock(text="hi")],
        ),
    )

    assert provider.calls == 2
    assert result.role == Role.ASSISTANT
    assert len(conversation.messages) == 4

    # TOOL-сообщение несёт id исходного вызова (call-1), а не имя инструмента.
    tool_message = conversation.messages[2]
    assert tool_message.role == Role.TOOL
    assert tool_message.tool_call_id == "call-1"


async def test_no_tool_calls_behaviour_unchanged() -> None:
    engine = ToolConversationEngine(
        llm_provider=SimpleLLMProvider(),
        context_builder=SimpleContextBuilder(),
        tool_manager=SimpleToolManager(
            tools=[],
        ),
    )

    conversation = Conversation(
        conversation_id="conv-1",
    )

    result = await engine.run_turn(
        conversation,
        Message(
            role=Role.USER,
            content=[TextBlock(text="hi")],
        ),
    )

    assert result.role == Role.ASSISTANT
    assert len(conversation.messages) == 2


async def test_max_tool_iterations_limit() -> None:
    provider = InfiniteToolLLMProvider()

    engine = ToolConversationEngine(
        llm_provider=provider,
        context_builder=SimpleContextBuilder(),
        tool_manager=SimpleToolManager(
            tools=[EchoTool()],
        ),
    )

    conversation = Conversation(
        conversation_id="conv-1",
    )

    await engine.run_turn(
        conversation,
        Message(
            role=Role.USER,
            content=[TextBlock(text="hi")],
        ),
    )

    assert provider.calls == MAX_TOOL_ITERATIONS
