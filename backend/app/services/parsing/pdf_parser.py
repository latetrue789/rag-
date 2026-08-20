from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from pypdf import PdfReader

from app.services.parsing.base import EmptyDocumentError, ParsedSection


class PageLike(Protocol):
    def extract_text(self) -> str | None: ...


class ReaderLike(Protocol):
    pages: Sequence[PageLike]


def default_reader(path: Path) -> ReaderLike:
    return PdfReader(path)


class PdfParser:
    def __init__(self, reader_factory: Callable[[Path], ReaderLike] = default_reader) -> None:
        self.reader_factory = reader_factory

    def parse(self, path: Path) -> list[ParsedSection]:
        reader = self.reader_factory(path)
        sections = [
            ParsedSection(text=text, page=page_number)
            for page_number, page in enumerate(reader.pages, start=1)
            if (text := (page.extract_text() or "").strip())
        ]
        if not sections:
            raise EmptyDocumentError("PDF 中没有可提取文字，暂不支持扫描版 PDF")
        return sections
