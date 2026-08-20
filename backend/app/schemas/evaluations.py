from pydantic import BaseModel, Field


class EvaluationCaseRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=2, max_length=1000)
    expected_document_ids: list[str] = Field(min_length=1)


class EvaluationRunRequest(BaseModel):
    cases: list[EvaluationCaseRequest] = Field(min_length=1, max_length=200)


class EvaluationRunResponse(BaseModel):
    id: str
    case_count: int
    metrics: dict[str, float]
    created_at: str


class EvaluationRunListResponse(BaseModel):
    items: list[EvaluationRunResponse]
    total: int
