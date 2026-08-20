from pathlib import Path

import pytest

from app.services.chunker import Chunker
from app.services.document_hasher import sha256_file
from app.services.parsing.base import ParsedSection


def test_chunker_splits_long_text_and_keeps_source_metadata() -> None:
    section = ParsedSection(text="甲" * 70 + "。" + "乙" * 70, title="技能", page=2)

    chunks = Chunker(chunk_size=90, overlap=15).split([section])

    assert len(chunks) == 2
    assert chunks[0].title == "技能"
    assert chunks[0].page == 2
    assert chunks[0].index == 0
    assert chunks[1].index == 1
    assert chunks[0].text[-15:] in chunks[1].text


def test_chunker_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="overlap"):
        Chunker(chunk_size=100, overlap=100)


def test_sha256_file_depends_on_content_not_filename(tmp_path: Path) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")

    assert sha256_file(first) == sha256_file(second)
