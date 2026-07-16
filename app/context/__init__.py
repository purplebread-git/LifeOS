"""Context System — pipeline сборки контекста для LLM.

LayeredContextBuilder применяет упорядоченные ContextLayer'ы. Порядок и
состав слоёв задаются в composition root.
"""

from app.context.conversation_history_layer import ConversationHistoryLayer
from app.context.default_system_prompt import DEFAULT_SYSTEM_PROMPT
from app.context.knowledge_context_layer import KnowledgeContextLayer
from app.context.layered_context_builder import LayeredContextBuilder
from app.context.memory_context_layer import MemoryContextLayer
from app.context.system_prompt_layer import SystemPromptLayer

__all__ = [
    "DEFAULT_SYSTEM_PROMPT",
    "ConversationHistoryLayer",
    "KnowledgeContextLayer",
    "LayeredContextBuilder",
    "MemoryContextLayer",
    "SystemPromptLayer",
]
