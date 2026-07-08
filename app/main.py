from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config.settings import get_settings
from app.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container: Container = app.state.container
    await container.init_resources()
    try:
        yield
    finally:
        await container.shutdown_resources()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="LifeOS Agent", debug=settings.app_debug, lifespan=lifespan)
    app.state.container = Container()

    app.include_router(health_router)

    return app


app = create_app()
