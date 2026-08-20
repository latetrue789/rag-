from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.dependencies import ContainerDependency

router = APIRouter(tags=["health"])


class ServiceStatus(BaseModel):
    llm: Literal["configured", "unconfigured"]
    sqlite: Literal["ok", "unavailable"]
    qdrant: Literal["ok", "unavailable"]
    ollama: Literal["ok", "unavailable"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    services: ServiceStatus


@router.get("/health", response_model=HealthResponse)
def health(container: ContainerDependency) -> HealthResponse:
    settings = container.settings
    snapshot = container.health.check()
    return HealthResponse(
        version=settings.app_version,
        services=ServiceStatus(
            llm="configured" if settings.llm_configured else "unconfigured",
            sqlite=snapshot.sqlite,
            qdrant=snapshot.qdrant,
            ollama=snapshot.ollama,
        ),
    )
