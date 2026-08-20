import json
from pathlib import Path

import pytest

from app.db.database import Database
from app.repositories.evaluation_repository import EvaluationRepository
from app.services.evaluation import (
    EvaluationCase,
    EvaluationService,
    Judgement,
    load_evaluation_cases,
)
from app.services.rag import RagResponse
from app.services.retrieval import Source


class FakeRag:
    def __init__(self) -> None:
        self.calls = 0

    def ask(self, question: str) -> RagResponse:
        self.calls += 1
        document_id = "doc-1" if self.calls == 1 else "other"
        return RagResponse(
            answer="岗位要求掌握 FastAPI。[S1]",
            sources=[
                Source(
                    "S1", document_id, "jd.md", "md", "掌握 FastAPI", 0.9, 0
                )
            ],
            grounded=True,
            trace_id=f"trace-{self.calls}",
            timings_ms={"total": 10.0 if self.calls == 1 else 30.0},
            rewritten=False,
        )


class FakeJudge:
    def evaluate(self, question, answer, sources) -> Judgement:
        return Judgement(faithfulness=0.8, citation_completeness=1.0)


def test_evaluation_calculates_four_metrics_and_writes_reports(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    repository = EvaluationRepository(database)
    service = EvaluationService(
        rag=FakeRag(),
        judge=FakeJudge(),
        repository=repository,
        report_directory=tmp_path / "reports",
    )
    cases = [
        EvaluationCase("case-1", "技能？", ["doc-1"]),
        EvaluationCase("case-2", "还要什么？", ["doc-2"]),
    ]

    run = service.run(cases)

    assert run.metrics == {
        "retrieval_hit_rate": 0.5,
        "faithfulness": 0.8,
        "citation_completeness": 1.0,
        "latency_avg_ms": 20.0,
        "latency_p95_ms": 30.0,
    }
    assert Path(run.json_report_path).exists()
    assert Path(run.markdown_report_path).exists()
    assert repository.list_runs()[0].id == run.id


def test_load_evaluation_cases_from_local_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps(
            {
                "case_id": "skill-001",
                "question": "岗位需要什么技能？",
                "expected_document_ids": ["doc-1"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)

    assert cases[0].case_id == "skill-001"
    assert cases[0].expected_document_ids == ["doc-1"]


def test_evaluation_rejects_empty_cases(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    service = EvaluationService(
        rag=FakeRag(),
        judge=FakeJudge(),
        repository=EvaluationRepository(database),
        report_directory=tmp_path,
    )

    with pytest.raises(ValueError, match="不能为空"):
        service.run([])
