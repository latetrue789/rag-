from pathlib import Path

from app.cli import expand_input_paths


def test_expand_input_paths_recursively_filters_supported_files(tmp_path: Path) -> None:
    nested = tmp_path / "notes"
    nested.mkdir()
    markdown = tmp_path / "job.md"
    text = nested / "interview.TXT"
    ignored = nested / "table.csv"
    markdown.write_text("JD", encoding="utf-8")
    text.write_text("question", encoding="utf-8")
    ignored.write_text("ignored", encoding="utf-8")

    assert expand_input_paths([tmp_path]) == sorted([markdown, text])
