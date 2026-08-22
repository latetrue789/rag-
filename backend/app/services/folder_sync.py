from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import monotonic

from app.db.models import DocumentRecord, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.document_hasher import sha256_file
from app.services.ingestion import IngestionAction, IngestionService

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}
DOCUMENT_SUBDIRECTORIES = ("md", "txt", "pdf")


@dataclass(frozen=True, slots=True)
class FolderSyncResult:
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    waiting: int = 0
    missing: int = 0
    oversized: int = 0
    busy: bool = False
    scanned_at: str | None = None

    def to_dict(self) -> dict[str, int | bool | str | None]:
        return asdict(self)


class FolderSyncService:
    def __init__(
        self,
        *,
        root: Path,
        ingestion: IngestionService,
        documents: DocumentRepository,
        stable_seconds: int = 10,
        max_size_mb: int = 25,
    ) -> None:
        self.root = root.resolve()
        self.ingestion = ingestion
        self.documents = documents
        self.stable_seconds = stable_seconds
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = Lock()
        self._observed: dict[str, tuple[tuple[int, int], float]] = {}
        self._processed: dict[str, tuple[int, int]] = {}
        self.last_result: FolderSyncResult | None = None

    @property
    def is_scanning(self) -> bool:
        return self._lock.locked()

    def ensure_directories(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in DOCUMENT_SUBDIRECTORIES:
            (self.root / name).mkdir(exist_ok=True)

    def scan(self) -> FolderSyncResult:
        if not self._lock.acquire(blocking=False):
            return FolderSyncResult(busy=True, scanned_at=self._now())
        try:
            result = self._scan_once()
            self.last_result = result
            return result
        finally:
            self._lock.release()

    def retry(self, document_id: str) -> DocumentRecord:
        document = self.documents.get(document_id)
        if document.status is not DocumentStatus.FAILED:
            raise ValueError("只有失败文档可以重试")
        source = Path(document.source_path).resolve()
        self._ensure_managed(source)
        if not source.is_file():
            raise FileNotFoundError(source)
        source_key = str(source)
        self._observed.pop(source_key, None)
        self._processed.pop(source_key, None)
        return self.ingestion.ingest(source).document

    def _scan_once(self) -> FolderSyncResult:
        self.ensure_directories()
        counters = {
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
            "waiting": 0,
            "missing": 0,
            "oversized": 0,
        }
        paths = [
            path
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        ]
        discovered = {str(path.resolve()) for path in paths}

        for path in paths:
            source = path.resolve()
            source_key = str(source)
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            fingerprint = (stat.st_size, stat.st_mtime_ns)
            if stat.st_size > self.max_size_bytes:
                counters["oversized"] += 1
                continue
            if self._processed.get(source_key) == fingerprint:
                counters["skipped"] += 1
                continue
            if not self._is_stable(source_key, fingerprint):
                counters["waiting"] += 1
                continue

            active = self.documents.get_active_by_source_path(source_key)
            try:
                content_hash = sha256_file(path)
            except FileNotFoundError:
                continue
            if active is not None and active.content_hash == content_hash:
                if active.status is DocumentStatus.MISSING:
                    self.documents.restore_indexed(active.id)
                self._processed[source_key] = fingerprint
                counters["skipped"] += 1
                continue

            duplicate = self.documents.get_by_hash(content_hash)
            if (
                duplicate is not None
                and duplicate.status is DocumentStatus.INDEXED
                and duplicate.source_path not in discovered
            ):
                self.documents.update_source(
                    duplicate.id,
                    filename=source.name,
                    source_path=source_key,
                    file_type=source.suffix.lower().lstrip("."),
                )
                self._processed[source_key] = fingerprint
                counters["skipped"] += 1
                continue

            outcome = self.ingestion.ingest(path)
            self._processed[source_key] = fingerprint
            if outcome.action is IngestionAction.INDEXED:
                counters["indexed"] += 1
            elif outcome.action is IngestionAction.FAILED:
                counters["failed"] += 1
            else:
                counters["skipped"] += 1

        for document in self.documents.list_active():
            if document.status not in {DocumentStatus.INDEXED, DocumentStatus.FAILED}:
                continue
            source = Path(document.source_path).resolve()
            if not self._is_managed(source) or str(source) in discovered:
                continue
            self.documents.mark_missing(document.id)
            self._observed.pop(str(source), None)
            self._processed.pop(str(source), None)
            counters["missing"] += 1

        return FolderSyncResult(**counters, scanned_at=self._now())

    def _is_stable(self, source: str, fingerprint: tuple[int, int]) -> bool:
        observed = self._observed.get(source)
        now = monotonic()
        if observed is None or observed[0] != fingerprint:
            self._observed[source] = (fingerprint, now)
            return self.stable_seconds <= 0
        return now - observed[1] >= self.stable_seconds

    def _ensure_managed(self, source: Path) -> None:
        if not self._is_managed(source):
            raise ValueError("文档不在固定资料目录中")

    def _is_managed(self, source: Path) -> bool:
        try:
            source.relative_to(self.root)
        except ValueError:
            return False
        return True

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
