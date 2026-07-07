# LifeOS Agent

Модульная платформа для персонального AI-агента с долгосрочной памятью
и расширяемой системой плагинов для внешних сервисов.

## Стек
Python 3.12+, uv, FastAPI, Pydantic v2, SQLAlchemy, Alembic, OpenAI SDK

## Быстрый старт

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

## Тесты

```bash
uv run pytest
```

## Документация
См. [docs/architecture.md](docs/architecture.md)