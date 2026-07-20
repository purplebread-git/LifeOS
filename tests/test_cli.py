"""Тесты minimal CLI (без реального LLM)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from app.cli import main, run_chat
from app.core.agent import Agent
from app.models.conversation import AgentResponse
from app.models.message import Message, Role, TextBlock


class _FakeAgent(Agent):
    def __init__(self) -> None:
        self.inputs: list[str] = []

    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        return AgentResponse(
            conversation_id=conversation_id,
            messages=[Message(role=Role.ASSISTANT, content=[TextBlock(text="unused")])],
        )

    async def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]:
        self.inputs.append(user_input)
        yield "ok:"
        yield user_input


async def test_run_chat_streams_and_quits() -> None:
    agent = _FakeAgent()
    prompts = iter(["hello", "/quit"])
    lines: list[str] = []

    def fake_input(prompt: str = "") -> str:
        return next(prompts)

    def fake_print(*args: object, **kwargs: object) -> None:
        text = " ".join(str(arg) for arg in args)
        end = kwargs.get("end", "\n")
        lines.append(text + ("" if end is None else str(end)))

    await run_chat(
        agent,
        "conv-cli",
        input_fn=fake_input,
        print_fn=fake_print,
    )

    assert agent.inputs == ["hello"]
    joined = "".join(lines)
    assert "ok:hello" in joined.replace("\n", "")


def test_main_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        main([])
