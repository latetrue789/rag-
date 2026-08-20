from fastapi import APIRouter, HTTPException

from app.api.dependencies import ContainerDependency
from app.schemas.evaluations import (
    EvaluationRunListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.evaluation import (
    EvaluationCase,
    JudgeUnavailableError,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def to_response(record) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        id=record.id,
        case_count=record.case_count,
        metrics=record.metrics,
        created_at=record.created_at,
    )


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(
    payload: EvaluationRunRequest,
    container: ContainerDependency,
) -> EvaluationRunResponse:
    cases = [
        EvaluationCase(
            case_id=item.case_id,
            question=item.question,
            expected_document_ids=item.expected_document_ids,
        )
        for item in payload.cases
    ]
    try:
        return to_response(container.evaluation.run(cases))
    except JudgeUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/runs", response_model=EvaluationRunListResponse)
def list_evaluation_runs(container: ContainerDependency) -> EvaluationRunListResponse:
    items = [to_response(item) for item in container.evaluations.list_runs()]
    return EvaluationRunListResponse(items=items, total=len(items))
