from pathlib import Path

import pytest

from app.services.parsing.base import EmptyDocumentError
from app.services.parsing.markdown_parser import MarkdownParser
from app.services.parsing.pdf_parser import PdfParser
from app.services.parsing.text_parser import TextParser


def test_markdown_parser_preserves_heading_path(tmp_path: Path) -> None:
    path = tmp_path / "岗位.md"
    path.write_text("# AI 应用开发\n岗位职责。\n## RAG\n掌握向量检索。", encoding="utf-8")

    sections = MarkdownParser().parse(path)

    assert [section.title for section in sections] == ["AI 应用开发", "AI 应用开发 / RAG"]
    assert sections[1].text == "掌握向量检索。"


def test_text_parser_supports_gb18030(tmp_path: Path) -> None:
    path = tmp_path / "面试题.txt"
    path.write_bytes("什么是 RAG？".encode("gb18030"))

    sections = TextParser().parse(path)

    assert sections[0].text == "什么是 RAG？"


class FakePage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


class FakeReader:
    def __init__(self, texts: list[str | None]) -> None:
        self.pages = [FakePage(text) for text in texts]


def test_pdf_parser_preserves_one_based_page_numbers(tmp_path: Path) -> None:
    path = tmp_path / "官方文档.pdf"
    path.touch()
    parser = PdfParser(reader_factory=lambda _: FakeReader(["第一页", None, "第三页"]))

    sections = parser.parse(path)

    assert [(section.page, section.text) for section in sections] == [(1, "第一页"), (3, "第三页")]


def test_pdf_parser_rejects_scanned_or_empty_pdf(tmp_path: Path) -> None:
    path = tmp_path / "扫描件.pdf"
    path.touch()
    parser = PdfParser(reader_factory=lambda _: FakeReader([None, "  "]))

    with pytest.raises(EmptyDocumentError, match="没有可提取文字"):
        parser.parse(path)
