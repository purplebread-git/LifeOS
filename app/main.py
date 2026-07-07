from fastapi import FastAPI

from app.api.health import router as health_router
from app.config.settings import get_settings


def create_app() -> FastAPI:
    """Application factory.

    На этом этапе фабрика ничего не знает про Agent, Provider или Plugin —
    это появится по мере того, как будет собираться DI-контейнер.
    """
    settings = get_settings()

    app = FastAPI(
        title="LifeOS Agent",
        debug=settings.app_debug,
    )

    app.include_router(health_router)

    return app


app = create_app()
