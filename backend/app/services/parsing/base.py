from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class DocumentParseError(ValueError):
    """Base error for document parsing failures."""


class EmptyDocumentError(DocumentParseError):
    """Raised when a document contains no usable text."""


class UnsupportedDocumentError(DocumentParseError):
    """Raised when a file type is outside the supported set."""


@dataclass(frozen=True, slots=True)
class ParsedSection:
    text: str
    title: str | None = None
    page: int | None = None


class DocumentParser(Protocol):
    def parse(self, path: Path) -> list[ParsedSection]: ...
