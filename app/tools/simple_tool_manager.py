from __future__ import annotations

from app.core.exceptions import ToolExecutionError
from app.core.execution_context import ExecutionContext
from app.core.tool import Tool
from app.core.tool_manager import ToolManager
from app.models.message import TextBlock, ToolCall
from app.models.tool import ToolDefinition, ToolResult


class SimpleToolManager(ToolManager):
    def __init__(self, tools: list[Tool]) -> None:
        self._tools: dict[str, Tool] = {tool.definition.name: tool for tool in tools}

    def tool_definitions(self) -> list[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    async def execute(
        self,
        tool_call: ToolCall,
        context: ExecutionContext,
    ) -> ToolResult:
        tool = self._tools.get(tool_call.tool_name)

        if tool is None:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=[
                    TextBlock(
                        text=f"Tool '{tool_call.tool_name}' not found",
                    ),
                ],
                is_error=True,
            )

        try:
            return await tool.execute(
                tool_call.arguments,
                context,
            )

        except ToolExecutionError as exc:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=[
                    TextBlock(text=str(exc)),
                ],
                is_error=True,
            )
