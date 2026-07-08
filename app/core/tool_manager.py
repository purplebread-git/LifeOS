from abc import ABC, abstractmethod

from app.core.execution_context import ExecutionContext
from app.models.message import ToolCall
from app.models.tool import ToolDefinition, ToolResult


class ToolManager(ABC):
    @abstractmethod
    def tool_definitions(self) -> list[ToolDefinition]:
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        tool_call: ToolCall,
        context: ExecutionContext,
    ) -> ToolResult:
        raise NotImplementedError
