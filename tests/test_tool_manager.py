from typing import Any

from app.core.exceptions import ToolExecutionError
from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.models.message import TextBlock, ToolCall
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
            tool_call_id="1",
            content=[
                TextBlock(
                    text=arguments["text"],
                ),
            ],
        )


class FailingTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="fail",
            description="fail",
            input_schema={},
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        raise ToolExecutionError("boom")


async def test_execute_tool() -> None:
    manager = SimpleToolManager(
        tools=[EchoTool()],
    )

    result = await manager.execute(
        ToolCall(
            id="1",
            tool_name="echo",
            arguments={"text": "hello"},
        ),
        ExecutionContext(
            conversation_id="conv",
        ),
    )

    assert result.is_error is False

    block = result.content[0]

    assert isinstance(block, TextBlock)
    assert block.text == "hello"


async def test_tool_not_found() -> None:
    manager = SimpleToolManager(
        tools=[],
    )

    result = await manager.execute(
        ToolCall(
            id="1",
            tool_name="missing",
            arguments={},
        ),
        ExecutionContext(
            conversation_id="conv",
        ),
    )

    assert result.is_error is True


async def test_tool_execution_error() -> None:
    manager = SimpleToolManager(
        tools=[FailingTool()],
    )

    result = await manager.execute(
        ToolCall(
            id="1",
            tool_name="fail",
            arguments={},
        ),
        ExecutionContext(
            conversation_id="conv",
        ),
    )

    assert result.is_error is True
