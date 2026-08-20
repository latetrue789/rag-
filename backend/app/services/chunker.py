from dataclasses import dataclass

from app.services.parsing.base import ParsedSection


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    index: int
    title: str | None = None
    page: int | None = None


class Chunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, sections: list[ParsedSection]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for section in sections:
            start = 0
            while start < len(section.text):
                proposed_end = min(start + self.chunk_size, len(section.text))
                end = self._find_break(section.text, start, proposed_end)
                content = section.text[start:end].strip()
                if content:
                    chunks.append(
                        Chunk(
                            text=content,
                            index=len(chunks),
                            title=section.title,
                            page=section.page,
                        )
                    )
                if end >= len(section.text):
                    break
                start = max(end - self.overlap, start + 1)
        return chunks

    def _find_break(self, text: str, start: int, proposed_end: int) -> int:
        if proposed_end >= len(text):
            return len(text)
        lower_bound = start + int(self.chunk_size * 0.6)
        for separator in ("\n\n", "\n", "。", "！", "？", ". "):
            position = text.rfind(separator, lower_bound, proposed_end)
            if position >= lower_bound:
                return position + len(separator)
        return proposed_end
