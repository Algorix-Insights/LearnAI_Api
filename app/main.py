from fastapi import FastAPI

from app.infra.v1.health import router as health_router
from app.infra.v1.router import api_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )
    app.include_router(health_router)
    app.include_router(api_router, prefix=app_settings.api_v1_prefix)
    return app


app = create_app()
