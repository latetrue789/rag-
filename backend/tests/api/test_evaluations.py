import asyncio
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.repositories.evaluation_repository import EvaluationRunRecord


def run_record() -> EvaluationRunRecord:
    return EvaluationRunRecord(
        id="run-1",
        case_count=1,
        metrics={
            "retrieval_hit_rate": 1.0,
            "faithfulness": 0.9,
            "citation_completeness": 1.0,
            "latency_avg_ms": 20.0,
            "latency_p95_ms": 20.0,
        },
        json_report_path="D:/private/report.json",
        markdown_report_path="D:/private/report.md",
        created_at="2026-08-20T00:00:00+00:00",
    )


class FakeEvaluationService:
    def run(self, cases):
        assert cases[0].case_id == "case-1"
        return run_record()


class FakeEvaluationRepository:
    def list_runs(self):
        return [run_record()]


async def request(app, method: str, path: str, json=None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, json=json)


def test_run_and_list_evaluations_do_not_expose_report_paths() -> None:
    app = create_app(
        SimpleNamespace(
            evaluation=FakeEvaluationService(),
            evaluations=FakeEvaluationRepository(),
        )
    )
    body = {
        "cases": [
            {
                "case_id": "case-1",
                "question": "岗位要求什么？",
                "expected_document_ids": ["doc-1"],
            }
        ]
    }

    created = asyncio.run(request(app, "POST", "/api/v1/evaluations/run", body))
    listed = asyncio.run(request(app, "GET", "/api/v1/evaluations/runs"))

    assert created.status_code == 200
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert "report_path" not in created.text
    assert "D:/private" not in listed.text
