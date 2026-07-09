from app.core.execution_context import ExecutionContext
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.models.message import TextBlock
from app.tools.remember_tool import RememberTool
from app.tools.search_memory_tool import SearchMemoryTool


async def test_remember_tool_stores_memory() -> None:
    memory = InMemoryMemoryProvider()

    tool = RememberTool()

    await tool.execute(
        {"text": "my favorite color is purple"},
        ExecutionContext(
            conversation_id="test",
            memory=memory,
        ),
    )

    results = await memory.search("purple")

    assert len(results) == 1
    assert results[0].content == "my favorite color is purple"


async def test_search_memory_tool_returns_memories() -> None:
    memory = InMemoryMemoryProvider()

    remember = RememberTool()

    await remember.execute(
        {"text": "my favorite color is purple"},
        ExecutionContext(
            conversation_id="test",
            memory=memory,
        ),
    )

    search = SearchMemoryTool()

    result = await search.execute(
        {"query": "purple"},
        ExecutionContext(
            conversation_id="test",
            memory=memory,
        ),
    )

    block = result.content[0]

    assert isinstance(block, TextBlock)
    assert "purple" in block.text
