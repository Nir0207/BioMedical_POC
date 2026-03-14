from contextlib import asynccontextmanager

from fastapi import FastAPI

from biomedical_api.api.routes import auth, data, health
from biomedical_api.core.config import get_settings
from biomedical_api.db.postgres import dispose_engine, init_models


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_models()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(data.router, prefix=settings.api_prefix)
    return app
