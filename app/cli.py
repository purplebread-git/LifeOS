"""Minimal LifeOS CLI — точка входа для ежедневного dogfooding.

Не продукт и не UI-платформа: достаточно, чтобы начать жить внутри системы.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Protocol

from app.container import Container
from app.core.agent import Agent


class _StreamingAgent(Protocol):
    def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]: ...


async def run_chat(
    agent: _StreamingAgent,
    conversation_id: str,
    *,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
) -> None:
    """Интерактивный цикл. input_fn/print_fn — для тестов."""
    print_fn(f"LifeOS chat ({conversation_id}). /quit to exit.")
    while True:
        try:
            line = input_fn("you> ")
        except EOFError:
            print_fn()
            break

        text = line.strip()
        if not text:
            continue
        if text in {"/quit", "/exit", ":q"}:
            break

        print_fn("lifeos> ", end="", flush=True)
        async for token in agent.stream_respond(conversation_id, line):
            print_fn(token, end="", flush=True)
        print_fn()


async def _chat_with_container(conversation_id: str) -> None:
    container = Container()
    init_result = container.init_resources()
    if init_result is not None:
        await init_result

    try:
        agent = container.agent()
        if hasattr(agent, "__await__"):
            agent = await agent
        assert isinstance(agent, Agent)
        await run_chat(agent, conversation_id)
    finally:
        shutdown_result = container.shutdown_resources()
        if shutdown_result is not None:
            await shutdown_result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lifeos", description="LifeOS minimal client")
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Interactive streaming chat")
    chat.add_argument(
        "--conversation-id",
        default=None,
        help="Conversation id (default: random uuid)",
    )

    args = parser.parse_args(argv)
    if args.command == "chat":
        conversation_id = args.conversation_id or str(uuid.uuid4())
        asyncio.run(_chat_with_container(conversation_id))


if __name__ == "__main__":
    main()
