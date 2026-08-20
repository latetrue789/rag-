from pathlib import Path

from app.services.parsing.base import DocumentParser, UnsupportedDocumentError
from app.services.parsing.markdown_parser import MarkdownParser
from app.services.parsing.pdf_parser import PdfParser
from app.services.parsing.text_parser import TextParser

PARSERS: dict[str, DocumentParser] = {
    ".md": MarkdownParser(),
    ".markdown": MarkdownParser(),
    ".txt": TextParser(),
    ".pdf": PdfParser(),
}


def parser_for(path: Path) -> DocumentParser:
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        raise UnsupportedDocumentError(f"不支持的文档格式：{path.suffix or '无扩展名'}")
    return parser
