from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_api.api.routes import agentic, health
from agentic_api.core.config import get_settings
from agentic_api.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(agentic.router, prefix=settings.api_prefix)
    return app
