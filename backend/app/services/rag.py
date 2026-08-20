from dataclasses import dataclass
from uuid import uuid4

from app.services.answering import AnsweringService
from app.services.retrieval import RetrievalService, Source


@dataclass(frozen=True, slots=True)
class RagResponse:
    answer: str
    sources: list[Source]
    grounded: bool
    trace_id: str
    timings_ms: dict[str, float]
    rewritten: bool


class RagService:
    def __init__(
        self,
        retrieval: RetrievalService,
        answering: AnsweringService,
    ) -> None:
        self.retrieval = retrieval
        self.answering = answering

    def ask(self, question: str) -> RagResponse:
        retrieval = self.retrieval.retrieve(question)
        result = self.answering.answer(question, retrieval)
        return RagResponse(
            answer=result.answer,
            sources=result.sources,
            grounded=result.grounded,
            trace_id=str(uuid4()),
            timings_ms=result.timings_ms,
            rewritten=retrieval.rewritten,
        )
