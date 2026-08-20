from pathlib import Path

from app.services.parsing.base import EmptyDocumentError, ParsedSection


class TextParser:
    encodings = ("utf-8-sig", "utf-8", "gb18030")

    def parse(self, path: Path) -> list[ParsedSection]:
        raw = path.read_bytes()
        text: str | None = None
        for encoding in self.encodings:
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError("TXT 文件编码不受支持，请转换为 UTF-8")
        content = text.strip()
        if not content:
            raise EmptyDocumentError("TXT 文档没有可提取文字")
        return [ParsedSection(text=content)]
