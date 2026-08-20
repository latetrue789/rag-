import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Protocol
from uuid import uuid4

from app.providers.base import LLMProvider
from app.repositories.evaluation_repository import (
    EvaluationRepository,
    EvaluationRunRecord,
)
from app.services.rag import RagService
from app.services.retrieval import Source


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    question: str
    expected_document_ids: list[str]


@dataclass(frozen=True, slots=True)
class Judgement:
    faithfulness: float
    citation_completeness: float


class EvaluationJudge(Protocol):
    def evaluate(
        self,
        question: str,
        answer: str,
        sources: list[Source],
    ) -> Judgement: ...


class JudgeUnavailableError(RuntimeError):
    """Raised when evaluation requires an unconfigured judge."""


class LLMJudge:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def evaluate(
        self,
        question: str,
        answer: str,
        sources: list[Source],
    ) -> Judgement:
        evidence = "\n".join(f"[{item.source_id}] {item.text}" for item in sources)
        raw = self.llm.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "你是固定的 RAG 评测器。只返回 JSON："
                        '{"faithfulness":0到1,"citation_completeness":0到1}。'
                    ),
                },
                {
                    "role": "user",
                    "content": f"问题：{question}\n答案：{answer}\n来源：\n{evidence}",
                },
            ]
        )
        payload = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return Judgement(
            faithfulness=self._score(payload["faithfulness"]),
            citation_completeness=self._score(payload["citation_completeness"]),
        )

    @staticmethod
    def _score(value) -> float:
        score = float(value)
        if not 0 <= score <= 1:
            raise ValueError("Judge score must be between 0 and 1")
        return score


class EvaluationService:
    def __init__(
        self,
        *,
        rag: RagService,
        judge: EvaluationJudge | None,
        repository: EvaluationRepository,
        report_directory: Path,
    ) -> None:
        self.rag = rag
        self.judge = judge
        self.repository = repository
        self.report_directory = report_directory

    def run(self, cases: list[EvaluationCase]) -> EvaluationRunRecord:
        if not cases:
            raise ValueError("评测集不能为空")
        if self.judge is None:
            raise JudgeUnavailableError("请先配置在线 LLM，再运行评测")
        run_id = str(uuid4())
        details = [self._evaluate_case(case) for case in cases]
        metrics = self._metrics(details)
        json_path, markdown_path = self._write_reports(run_id, metrics, details)
        return self.repository.create(
            run_id=run_id,
            case_count=len(cases),
            metrics=metrics,
            json_report_path=str(json_path),
            markdown_report_path=str(markdown_path),
        )

    def _evaluate_case(self, case: EvaluationCase) -> dict:
        response = self.rag.ask(case.question)
        judgement = self.judge.evaluate(
            case.question,
            response.answer,
            response.sources,
        )
        returned_ids = {source.document_id for source in response.sources}
        hit = bool(returned_ids & set(case.expected_document_ids))
        return {
            "case_id": case.case_id,
            "question": case.question,
            "expected_document_ids": case.expected_document_ids,
            "retrieval_hit": hit,
            "faithfulness": judgement.faithfulness,
            "citation_completeness": judgement.citation_completeness,
            "timings_ms": response.timings_ms,
            "trace_id": response.trace_id,
        }

    @staticmethod
    def _metrics(details: list[dict]) -> dict[str, float]:
        totals = [float(item["timings_ms"].get("total", 0)) for item in details]
        return {
            "retrieval_hit_rate": mean(item["retrieval_hit"] for item in details),
            "faithfulness": mean(item["faithfulness"] for item in details),
            "citation_completeness": mean(
                item["citation_completeness"] for item in details
            ),
            "latency_avg_ms": mean(totals),
            "latency_p95_ms": sorted(totals)[max(0, math.ceil(len(totals) * 0.95) - 1)],
        }

    def _write_reports(
        self,
        run_id: str,
        metrics: dict[str, float],
        details: list[dict],
    ) -> tuple[Path, Path]:
        self.report_directory.mkdir(parents=True, exist_ok=True)
        json_path = self.report_directory / f"{run_id}.json"
        markdown_path = self.report_directory / f"{run_id}.md"
        json_path.write_text(
            json.dumps(
                {"run_id": run_id, "metrics": metrics, "cases": details},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        rows = ["# RAG 评测报告", "", f"运行 ID：`{run_id}`", "", "## 汇总指标", ""]
        rows.extend(f"- {key}: {value:.3f}" for key, value in metrics.items())
        markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return json_path, markdown_path


def load_evaluation_cases(path: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(EvaluationCase(**json.loads(line)))
    return cases
