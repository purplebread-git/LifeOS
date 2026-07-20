"""Тесты minimal CLI (без реального LLM)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest

from app.cli import main, run_chat
from app.core.agent import Agent
from app.core.exceptions import LLMRateLimitError
from app.models.conversation import AgentResponse
from app.models.message import Message, Role, TextBlock
from app.providers.openai.openai_client import _rate_limit_message


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


class _FailingAgent(Agent):
    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        raise AssertionError("respond should not be called")

    async def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]:
        if False:  # pragma: no cover — make this an async generator
            yield ""
        raise LLMRateLimitError(
            "OpenAI quota exceeded — check billing/credits at "
            "https://platform.openai.com/settings/organization/billing"
        )


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


async def test_run_chat_prints_llm_error_and_continues() -> None:
    agent = _FailingAgent()
    prompts = iter(["hi", "/quit"])
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

    joined = "".join(lines)
    assert "error: OpenAI quota exceeded" in joined


def test_rate_limit_message_distinguishes_quota() -> None:
    by_code = _rate_limit_message(SimpleNamespace(code="insufficient_quota"))
    assert "quota exceeded" in by_code.lower()
    assert "billing" in by_code.lower()

    by_text = _rate_limit_message(Exception("Error code: 429 - insufficient_quota"))
    assert "quota exceeded" in by_text.lower()

    by_rpm = _rate_limit_message(SimpleNamespace(code="rate_limit_exceeded"))
    assert "rate limit exceeded" in by_rpm.lower()
    assert "quota exceeded" not in by_rpm.lower()


def test_main_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        main([])
