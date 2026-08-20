from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.container import ServiceContainer


def create_app(container: ServiceContainer | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.container = container or ServiceContainer(settings)
    app.include_router(api_router)
    return app


app = create_app()
