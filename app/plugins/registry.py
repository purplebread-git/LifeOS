"""SimplePluginRegistry — конкретная реализация PluginRegistry."""
from __future__ import annotations

from app.core.plugin_registry import PluginRegistry
from app.core.tool import Tool


class SimplePluginRegistry(PluginRegistry):
    def __init__(self) -> None:
        self._tools: list[Tool] = []

    def register_tool(self, tool: Tool) -> None:
        self._tools.append(tool)

    def all_registered_tools(self) -> list[Tool]:
        return list(self._tools)