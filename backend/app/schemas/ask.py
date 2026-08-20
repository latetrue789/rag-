from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class SourceResponse(BaseModel):
    source_id: str
    document_id: str
    filename: str
    file_type: str
    text: str
    score: float
    chunk_index: int
    title: str | None = None
    page: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    grounded: bool
    trace_id: str
    timings: dict[str, float]
    rewritten: bool
