import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.database import Database


@dataclass(frozen=True, slots=True)
class EvaluationRunRecord:
    id: str
    case_count: int
    metrics: dict[str, float]
    json_report_path: str
    markdown_report_path: str
    created_at: str


class EvaluationRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        run_id: str,
        case_count: int,
        metrics: dict[str, float],
        json_report_path: str,
        markdown_report_path: str,
    ) -> EvaluationRunRecord:
        created_at = datetime.now(UTC).isoformat()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO evaluation_runs (
                    id, case_count, metrics_json, json_report_path,
                    markdown_report_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    case_count,
                    json.dumps(metrics, ensure_ascii=False),
                    json_report_path,
                    markdown_report_path,
                    created_at,
                ),
            )
        return self.get(run_id)

    def get(self, run_id: str) -> EvaluationRunRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM evaluation_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Evaluation run not found: {run_id}")
        return self._from_row(row)

    def list_runs(self) -> list[EvaluationRunRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evaluation_runs ORDER BY created_at DESC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> EvaluationRunRecord:
        return EvaluationRunRecord(
            id=row["id"],
            case_count=row["case_count"],
            metrics=json.loads(row["metrics_json"]),
            json_report_path=row["json_report_path"],
            markdown_report_path=row["markdown_report_path"],
            created_at=row["created_at"],
        )
