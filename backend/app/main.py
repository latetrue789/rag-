import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.container import ServiceContainer

logger = logging.getLogger(__name__)


def create_app(container: ServiceContainer | None = None) -> FastAPI:
    settings = get_settings()
    services = container or ServiceContainer(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        sync = getattr(services, "folder_sync", None)
        task: asyncio.Task[None] | None = None
        if sync is not None:
            async def scan_periodically() -> None:
                while True:
                    try:
                        await asyncio.to_thread(sync.scan)
                    except Exception:
                        logger.exception("Automatic document scan failed")
                    await asyncio.sleep(settings.document_scan_interval_seconds)

            task = asyncio.create_task(scan_periodically())
        yield
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.container = services
    app.include_router(api_router)
    return app


app = create_app()
