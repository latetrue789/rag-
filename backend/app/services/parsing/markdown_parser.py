import re
from pathlib import Path

from app.services.parsing.base import EmptyDocumentError, ParsedSection

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class MarkdownParser:
    def parse(self, path: Path) -> list[ParsedSection]:
        text = path.read_text(encoding="utf-8-sig")
        sections: list[ParsedSection] = []
        headings: dict[int, str] = {}
        buffer: list[str] = []

        def flush() -> None:
            content = "\n".join(buffer).strip()
            if content:
                title = " / ".join(headings[level] for level in sorted(headings)) or None
                sections.append(ParsedSection(text=content, title=title))
            buffer.clear()

        for line in text.splitlines():
            match = HEADING.match(line)
            if match:
                flush()
                level = len(match.group(1))
                headings[level] = match.group(2).strip()
                for child_level in [item for item in headings if item > level]:
                    del headings[child_level]
            else:
                buffer.append(line)
        flush()

        if not sections:
            raise EmptyDocumentError("Markdown 文档没有可提取文字")
        return sections
