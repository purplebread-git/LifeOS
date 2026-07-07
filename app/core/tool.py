from abc import ABC, abstractmethod
from typing import Any

from app.core.execution_context import ExecutionContext
from app.models.tool import ToolDefinition, ToolResult


class Tool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, arguments: dict[str, Any], context: ExecutionContext) -> ToolResult:
        raise NotImplementedError