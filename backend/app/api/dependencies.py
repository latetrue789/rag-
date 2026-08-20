from typing import Annotated

from fastapi import Depends, Request

from app.services.container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]
