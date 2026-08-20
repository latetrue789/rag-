from fastapi import APIRouter, HTTPException

from app.api.dependencies import ContainerDependency
from app.providers.base import ProviderError
from app.schemas.ask import AskRequest, AskResponse, SourceResponse
from app.services.retrieval import RetrievalUnavailableError

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, container: ContainerDependency) -> AskResponse:
    try:
        result = container.rag.ask(payload.question.strip())
    except ProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except RetrievalUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return AskResponse(
        answer=result.answer,
        sources=[
            SourceResponse.model_validate(source, from_attributes=True)
            for source in result.sources
        ],
        grounded=result.grounded,
        trace_id=result.trace_id,
        timings=result.timings_ms,
        rewritten=result.rewritten,
    )
