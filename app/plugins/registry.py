"""SimplePluginRegistry — конкретная реализация PluginRegistry."""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.core.plugin_registry import PluginRegistry
from app.core.tool import Tool


class SimplePluginRegistry(PluginRegistry):
    def __init__(self) -> None:
        self._tools: list[Tool] = []
        self._context_layers: list[ContextLayer] = []

    def register_tool(self, tool: Tool) -> None:
        self._tools.append(tool)

    def all_registered_tools(self) -> list[Tool]:
        return list(self._tools)

    def register_context_layer(self, layer: ContextLayer) -> None:
        self._context_layers.append(layer)

    def all_registered_context_layers(self) -> list[ContextLayer]:
        return list(self._context_layers)
